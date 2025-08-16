from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
import sqlite3
from twelvelabs import TwelveLabs
from twelvelabs.models.embed import EmbeddingsTask
import hashlib
import numpy as np
import tempfile
import os
from datetime import datetime, timezone
import sys
import boto3
from botocore.exceptions import ClientError
import uuid
import io

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="SAGE Backend", version="2.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://tl-sage.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    client_host = request.client.host if request.client else "unknown"
    path = str(request.url.path)
    
    try:
        response = await call_next(request)
        duration = (datetime.now() - start_time).total_seconds()
        
        if response.status_code >= 400:
            logger.warning(f"{client_host} - {request.method} {path} - {response.status_code} ({duration:.3f}s)")
        else:
            logger.info(f"{client_host} - {request.method} {path} - {response.status_code} ({duration:.3f}s)")
        
        return response
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"{client_host} - {request.method} {path} - Error: {str(e)} ({duration:.3f}s)")
        raise

# Database setup
DB_PATH = "sage.db"
conn = sqlite3.connect(DB_PATH)
conn.execute('''
    CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key_hash TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

# Pydantic models
class ApiKeyRequest(BaseModel):
    key: str

class ApiKeyResponse(BaseModel):
    key: str
    isValid: bool

class VideoUploadResponse(BaseModel):
    embeddings: Dict[str, Any]
    filename: str
    duration: float
    embedding_id: str
    video_id: str

class ComparisonRequest(BaseModel):
    embedding_id1: str
    embedding_id2: str
    threshold: float = 0.1
    distance_metric: str = "cosine"

class DifferenceSegment(BaseModel):
    start_sec: float
    end_sec: float
    distance: float

class ComparisonResponse(BaseModel):
    filename1: str
    filename2: str
    differences: List[DifferenceSegment]
    total_segments: int
    differing_segments: int
    threshold_used: float

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float
    uptime: str
    timestamp: str
    database_status: str
    python_version: str

# In-memory storage for videos and embeddings
videos: Dict[str, Dict[str, Any]] = {}
embeddings: Dict[str, Dict[str, Any]] = {}
start_time = datetime.now()

# TwelveLabs client
twelvelabs_client = None

def get_twelvelabs_client(api_key: str):
    global twelvelabs_client
    if twelvelabs_client is None:
        twelvelabs_client = TwelveLabs(api_key=api_key)
    return twelvelabs_client

def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()

def store_api_key(key: str):
    key_hash = hash_api_key(key)
    try:
        conn.execute('INSERT OR REPLACE INTO api_keys (key_hash) VALUES (?)', (key_hash,))
        conn.commit()
    except Exception as e:
        logger.error(f"Error storing API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to store API key")

def validate_stored_api_key(key: str) -> bool:
    key_hash = hash_api_key(key)
    try:
        cursor = conn.execute('SELECT key_hash FROM api_keys WHERE key_hash = ?', (key_hash,))
        return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"Error validating stored API key: {e}")
        return False

@app.post("/validate-key", response_model=ApiKeyResponse)
async def validate_api_key(request: ApiKeyRequest):
    """Validate TwelveLabs API key and store hash securely."""
    try:
        client = get_twelvelabs_client(request.key)
        # Test the API key by making a simple request
        client.task.list()
        
        # Store the valid key
        store_api_key(request.key)
        
        return ApiKeyResponse(key=request.key, isValid=True)
    except Exception as e:
        logger.error(f"API key validation failed: {e}")
        return ApiKeyResponse(key=request.key, isValid=False)

@app.post("/upload-and-generate-embeddings", response_model=VideoUploadResponse)
async def upload_and_generate_embeddings(file: UploadFile = File(...)):
    """Upload video file and start AI embedding generation."""
    if not file.content_type or not file.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    try:
        # Read file content
        content = await file.read()
        
        # Generate unique IDs
        video_id = str(uuid.uuid4())
        embedding_id = str(uuid.uuid4())
        
        # Store video in memory
        videos[video_id] = {
            'content': content,
            'filename': file.filename,
            'content_type': file.content_type,
            'size': len(content),
            'created_at': datetime.now()
        }
        
        # Create temporary file for TwelveLabs
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Get API key from request headers or use stored one
            # For now, we'll use a placeholder - in production this should come from auth
            api_key = os.getenv('TWELVELABS_API_KEY', '')
            if not api_key:
                raise HTTPException(status_code=400, detail="No API key available")
            
            client = get_twelvelabs_client(api_key)
            
            # Upload to TwelveLabs
            with open(temp_file_path, 'rb') as video_file:
                task = client.task.create(
                    file=video_file,
                    task_type="embed",
                    model="marengo-retrieval-2.7"
                )
            
            # Store task info
            embeddings[embedding_id] = {
                'task_id': task.id,
                'video_id': video_id,
                'status': 'processing',
                'created_at': datetime.now()
            }
            
            # For demo purposes, create mock embeddings
            # In production, you'd poll the task status and retrieve actual embeddings
            mock_embeddings = {
                'task_id': task.id,
                'status': 'completed',
                'segments': [
                    {
                        'start_time': i * 2.0,
                        'end_time': (i + 1) * 2.0,
                        'embedding': np.random.rand(768).tolist()
                    }
                    for i in range(30)  # 30 segments of 2 seconds each
                ]
            }
            
            # Update embeddings with mock data
            embeddings[embedding_id].update({
                'embeddings': mock_embeddings,
                'status': 'completed'
            })
            
            # Calculate duration (mock - in production this would come from video metadata)
            duration = 60.0  # 60 seconds
            
            return VideoUploadResponse(
                embeddings=mock_embeddings,
                filename=file.filename or "video.mp4",
                duration=duration,
                embedding_id=embedding_id,
                video_id=video_id
            )
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            
    except Exception as e:
        logger.error(f"Error processing video upload: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process video: {str(e)}")

@app.post("/compare-local-videos", response_model=ComparisonResponse)
async def compare_local_videos(
    embedding_id1: str = Query(...),
    embedding_id2: str = Query(...),
    threshold: float = Query(0.1),
    distance_metric: str = Query("cosine")
):
    """Compare two videos using their embedding IDs."""
    try:
        # Get embeddings
        if embedding_id1 not in embeddings or embedding_id2 not in embeddings:
            raise HTTPException(status_code=404, detail="One or both embeddings not found")
        
        emb1 = embeddings[embedding_id1]
        emb2 = embeddings[embedding_id2]
        
        if emb1['status'] != 'completed' or emb2['status'] != 'completed':
            raise HTTPException(status_code=400, detail="One or both embeddings still processing")
        
        # Get video filenames
        video1_filename = videos[emb1['video_id']]['filename']
        video2_filename = videos[emb2['video_id']]['filename']
        
        # Calculate differences using mock data
        # In production, this would use actual embedding vectors
        differences = []
        total_segments = min(len(emb1['embeddings']['segments']), len(emb2['embeddings']['segments']))
        
        for i in range(total_segments):
            # Mock distance calculation
            distance = np.random.random()
            if distance > threshold:
                start_sec = emb1['embeddings']['segments'][i]['start_time']
                end_sec = emb1['embeddings']['segments'][i]['end_time']
                differences.append(DifferenceSegment(
                    start_sec=start_sec,
                    end_sec=end_sec,
                    distance=distance
                ))
        
        return ComparisonResponse(
            filename1=video1_filename,
            filename2=video2_filename,
            differences=differences,
            total_segments=total_segments,
            differing_segments=len(differences),
            threshold_used=threshold
        )
        
    except Exception as e:
        logger.error(f"Error comparing videos: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to compare videos: {str(e)}")

@app.get("/serve-video/{video_id}")
async def serve_video(video_id: str):
    """Stream video content from backend memory."""
    if video_id not in videos:
        raise HTTPException(status_code=404, detail="Video not found")
    
    video_data = videos[video_id]
    content = video_data['content']
    content_type = video_data['content_type']
    
    return StreamingResponse(
        io.BytesIO(content),
        media_type=content_type,
        headers={"Content-Length": str(len(content))}
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Server health check with detailed status information."""
    uptime = datetime.now() - start_time
    uptime_seconds = uptime.total_seconds()
    
    # Format uptime
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    seconds = int(uptime_seconds % 60)
    uptime_str = f"{hours}:{minutes:02d}:{seconds:02d}"
    
    # Check database status
    try:
        conn.execute("SELECT 1")
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        uptime_seconds=uptime_seconds,
        uptime=uptime_str,
        timestamp=datetime.now(timezone.utc).isoformat(),
        database_status=db_status,
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )

@app.get("/")
async def root():
    """API information endpoint for bots and scanners."""
    return {
        "message": "SAGE API",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
