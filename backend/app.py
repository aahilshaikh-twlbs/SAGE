from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel
from typing import Dict, Any
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

# Configure logging with timestamps
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="SAGE Backend", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://tl-sage.vercel.app",
        "http://209.38.142.207:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware to log all incoming requests with timestamps
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    client_host = request.client.host if request.client else "unknown"
    
    # Log suspicious requests
    path = str(request.url.path)
    if request.url.query:
        path += f"?{request.url.query}"
    
    # Check for suspicious patterns
    suspicious_patterns = [
        "http%3A//", "https%3A//",  # URL encoded URLs
        "CONNECT",  # CONNECT method abuse
        ".php", ".asp", ".cgi",  # Common exploit targets
        "../", "..\\",  # Path traversal attempts
        "admin", "wp-", "phpmyadmin",  # Common admin panels
        ".env", ".git", ".config",  # Sensitive files
    ]
    
    is_suspicious = any(pattern in path.lower() or pattern in request.method for pattern in suspicious_patterns)
    
    if is_suspicious:
        logger.warning(f"Suspicious request from {client_host}: {request.method} {path}")
    
    # Process the request
    try:
        response = await call_next(request)
        
        # Calculate response time
        duration = (datetime.now() - start_time).total_seconds()
        
        # Log based on status code
        if response.status_code == 404:
            logger.warning(f"{client_host} - {request.method} {path} - 404 Not Found ({duration:.3f}s)")
        elif response.status_code >= 400:
            logger.warning(f"{client_host} - {request.method} {path} - {response.status_code} ({duration:.3f}s)")
        elif response.status_code >= 200 and response.status_code < 300:
            logger.info(f"{client_host} - {request.method} {path} - {response.status_code} ({duration:.3f}s)")
        
        return response
        
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"{client_host} - {request.method} {path} - Error: {str(e)} ({duration:.3f}s)")
        raise

DB_PATH = "sage.db"

# Initialize database
conn = sqlite3.connect(DB_PATH)
conn.execute('''
    CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key_hash TEXT UNIQUE NOT NULL,
        api_key TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()
conn.close()

# S3 Configuration
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "tl-sage-bucket")
S3_REGION = os.getenv("S3_REGION", "us-west-2")  # Changed to match your SSO region
S3_PROFILE = os.getenv("S3_PROFILE", "dev")  # Use the dev profile

# Initialize S3 client using AWS profile
s3_client = None
try:
    # Create a session using the AWS profile
    session = boto3.Session(profile_name=S3_PROFILE, region_name=S3_REGION)
    s3_client = session.client('s3')
    
    # Test the connection by listing buckets
    s3_client.list_buckets()
    logger.info(f"S3 client initialized using profile '{S3_PROFILE}' for bucket: {S3_BUCKET_NAME}")
    
except Exception as e:
    logger.warning(f"S3 client initialization failed: {e}")
    logger.warning("S3 functionality will be disabled. Make sure AWS SSO is configured and you're logged in.")
    s3_client = None

def upload_to_s3(file_content: bytes, filename: str, content_type: str = "video/mp4") -> str:
    """
    Upload a file to S3 and return the S3 URL.
    
    Args:
        file_content: The file content as bytes
        filename: The original filename
        content_type: The MIME type of the file
        
    Returns:
        The S3 URL of the uploaded file
    """
    if not s3_client:
        raise Exception("S3 client not initialized")
    
    # Generate unique key for S3
    file_key = f"videos/{uuid.uuid4()}_{filename}"
    
    try:
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=file_key,
            Body=file_content,
            ContentType=content_type,
            Metadata={
                'original_filename': filename,
                'upload_timestamp': datetime.now().isoformat()
            }
        )
        
        # Generate S3 URL
        s3_url = f"s3://{S3_BUCKET_NAME}/{file_key}"
        logger.info(f"File uploaded to S3: {s3_url}")
        return s3_url
        
    except ClientError as e:
        logger.error(f"Failed to upload file to S3: {e}")
        raise Exception(f"S3 upload failed: {str(e)}")

def get_s3_presigned_url(s3_url: str, expiration: int = 3600) -> str:
    """
    Generate a presigned URL for an S3 object.
    
    Args:
        s3_url: The S3 URL (s3://bucket/key)
        expiration: URL expiration time in seconds
        
    Returns:
        Presigned URL for direct access
    """
    if not s3_client:
        raise Exception("S3 client not initialized")
    
    # Parse S3 URL
    if s3_url.startswith("s3://"):
        parts = s3_url[5:].split("/", 1)
        bucket = parts[0]
        key = parts[1] if len(parts) > 1 else ""
    else:
        raise Exception("Invalid S3 URL format")
    
    try:
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=expiration
        )
        return presigned_url
    except ClientError as e:
        logger.error(f"Failed to generate presigned URL: {e}")
        raise Exception(f"Presigned URL generation failed: {str(e)}")

current_api_key = None
tl_client = None
embedding_storage: Dict[str, Any] = {}
video_storage: Dict[str, Dict[str, Any]] = {}  # Store metadata instead of content

# Track server start time
server_start_time = datetime.now(timezone.utc)

@app.get("/")
async def root():
    """Root endpoint to handle scanner traffic"""
    return {"message": "SAGE API", "docs": "/docs"}

@app.get("/robots.txt")
async def robots():
    """Robots.txt to control crawlers"""
    return Response(content="User-agent: *\nDisallow: /", media_type="text/plain")

@app.get("/favicon.ico")
async def favicon():
    """Return 204 No Content for favicon requests"""
    return Response(status_code=204)

@app.get("/health")
async def health_check():
    """Health check endpoint that returns server status and basic info"""
    try:
        # Check database connection
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        db_status = "healthy"
    except Exception as e:
        db_status = "error"
    
    # Calculate uptime
    uptime = datetime.now(timezone.utc) - server_start_time
    uptime_seconds = int(uptime.total_seconds())
    
    return {
        "status": "healthy",
        "version": "2.0.0",
        "uptime_seconds": uptime_seconds,
        "uptime": str(uptime),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database_status": db_status,
        "python_version": sys.version.split()[0]
    }

async def get_api_key(request: Request) -> str:
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header required")
    return api_key

def get_twelve_labs_client(api_key: str = Depends(get_api_key)):
    global tl_client, current_api_key
    
    if tl_client and current_api_key == api_key:
        return tl_client
    
    try:
        tl_client = TwelveLabs(api_key=api_key)
        current_api_key = api_key
        
        # Save API key hash
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        conn = sqlite3.connect(DB_PATH)
        conn.execute('INSERT OR REPLACE INTO api_keys (key_hash, api_key) VALUES (?, ?)', 
                     (key_hash, None))
        conn.commit()
        conn.close()
        
        logger.info("Successfully initialized TwelveLabs client")
        return tl_client
    except Exception as e:
        logger.error(f"Error initializing TwelveLabs client: {e}")
        raise HTTPException(status_code=401, detail="Invalid API key")

class ApiKeyValidation(BaseModel):
    key: str

class ApiKeyResponse(BaseModel):
    key: str
    isValid: bool

@app.post("/validate-key")
async def validate_api_key(request: ApiKeyValidation):
    logger.info("Validating API key...")
    try:
        TwelveLabs(api_key=request.key)
        
        # Save API key hash
        key_hash = hashlib.sha256(request.key.encode()).hexdigest()
        conn = sqlite3.connect(DB_PATH)
        conn.execute('INSERT OR REPLACE INTO api_keys (key_hash, api_key) VALUES (?, ?)', 
                     (key_hash, None))
        conn.commit()
        conn.close()
        
        logger.info("API key validation successful")
        return ApiKeyResponse(key=request.key, isValid=True)
    except Exception as e:
        logger.error(f"API key validation failed: {e}")
        return ApiKeyResponse(key=request.key, isValid=False)

@app.post("/upload-and-generate-embeddings")
async def upload_and_generate_embeddings(
    file: UploadFile = File(...),
    tl: TwelveLabs = Depends(get_twelve_labs_client)
):
    try:
        content = await file.read()
        
        # Upload to S3 first
        logger.info(f"Uploading file {file.filename} to S3...")
        s3_url = upload_to_s3(content, file.filename)
        
        # Generate unique IDs
        video_id = f"video_{uuid.uuid4()}"
        embedding_id = f"embed_{uuid.uuid4()}"
        
        # Store video metadata immediately
        video_storage[video_id] = {
            "filename": file.filename,
            "s3_url": s3_url,
            "status": "uploaded",
            "upload_timestamp": datetime.now().isoformat(),
            "embedding_id": embedding_id
        }
        
        # Initialize embedding storage
        embedding_storage[embedding_id] = {
            "filename": file.filename,
            "status": "pending",
            "video_id": video_id,
            "s3_url": s3_url
        }
        
        # Start async embedding generation
        import asyncio
        asyncio.create_task(generate_embeddings_async(embedding_id, s3_url, tl))
        
        logger.info(f"File {file.filename} uploaded to S3 and embedding generation started")
        
        return {
            "message": "Video uploaded successfully. Embedding generation in progress.",
            "filename": file.filename,
            "video_id": video_id,
            "embedding_id": embedding_id,
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

async def generate_embeddings_async(embedding_id: str, s3_url: str, tl: TwelveLabs):
    """
    Asynchronously generate embeddings for a video from S3.
    """
    try:
        logger.info(f"Starting async embedding generation for {embedding_id}")
        
        # Update status
        embedding_storage[embedding_id]["status"] = "processing"
        
        # Create embedding task using S3 URL
        task = tl.embed.task.create(
            model_name="Marengo-retrieval-2.7",
            video_url=s3_url,  # Use S3 URL instead of local file
            video_clip_length=2,
            video_embedding_scopes=["clip", "video"]
        )
        
        logger.info(f"Embedding task {task.id} created for {embedding_id}")
        
        # Wait for completion
        def on_task_update(task: EmbeddingsTask):
            logger.info(f"Task {task.id} status: {task.status}")
        
        task.wait_for_done(sleep_interval=5, callback=on_task_update)
        
        # Get completed task
        completed_task = tl.embed.task.retrieve(task.id)
        
        # Calculate duration
        duration = 0
        if completed_task.video_embedding and completed_task.video_embedding.segments:
            duration = completed_task.video_embedding.segments[-1].end_offset_sec
        
        # Update embedding storage
        embedding_storage[embedding_id].update({
            "status": "completed",
            "embeddings": completed_task.video_embedding,
            "duration": duration,
            "task_id": task.id,
            "completed_at": datetime.now().isoformat()
        })
        
        # Update video storage with duration
        video_id = embedding_storage[embedding_id]["video_id"]
        if video_id in video_storage:
            video_storage[video_id]["duration"] = duration
            video_storage[video_id]["status"] = "ready"
        
        logger.info(f"Embedding generation completed for {embedding_id}")
        
    except Exception as e:
        logger.error(f"Error in async embedding generation for {embedding_id}: {e}")
        embedding_storage[embedding_id]["status"] = "failed"
        embedding_storage[embedding_id]["error"] = str(e)

@app.post("/compare-local-videos")
async def compare_local_videos(
    embedding_id1: str = Query(...),
    embedding_id2: str = Query(...),
    threshold: float = Query(0.1),
    distance_metric: str = Query("cosine")
):
    try:
        if embedding_id1 not in embedding_storage or embedding_id2 not in embedding_storage:
            raise HTTPException(status_code=404, detail="Embeddings not found")
        
        embed_data1 = embedding_storage[embedding_id1]
        embed_data2 = embedding_storage[embedding_id2]
        
        # Check if embeddings are ready
        if embed_data1["status"] != "completed":
            raise HTTPException(status_code=400, detail=f"Embedding {embedding_id1} is not ready. Status: {embed_data1['status']}")
        
        if embed_data2["status"] != "completed":
            raise HTTPException(status_code=400, detail=f"Embedding {embedding_id2} is not ready. Status: {embed_data2['status']}")
        
        segments1 = []
        segments2 = []
        
        if embed_data1["embeddings"] and embed_data1["embeddings"].segments:
            segments1 = [{
                "start_offset_sec": seg.start_offset_sec,
                "end_offset_sec": seg.end_offset_sec,
                "embedding": seg.embeddings_float
            } for seg in embed_data1["embeddings"].segments]
        
        if embed_data2["embeddings"] and embed_data2["embeddings"].segments:
            segments2 = [{
                "start_offset_sec": seg.start_offset_sec,
                "end_offset_sec": seg.end_offset_sec,
                "embedding": seg.embeddings_float
            } for seg in embed_data2["embeddings"].segments]
        
        logger.info(f"Comparing {len(segments1)} segments from video1 with {len(segments1)} segments from video2, threshold: {threshold}")
        
        # Compare segments
        def keyfunc(s):
            return round(s["start_offset_sec"], 2)
        
        dict_v1 = {keyfunc(seg): seg for seg in segments1}
        dict_v2 = {keyfunc(seg): seg for seg in segments2}
        
        all_keys = set(dict_v1.keys()).union(set(dict_v2.keys()))
        differing_segments = []
        all_distances = []
        
        for k in sorted(all_keys):
            seg1 = dict_v1.get(k)
            seg2 = dict_v2.get(k)
            
            if not seg1 or not seg2:
                valid_seg = seg1 if seg1 else seg2
                differing_segments.append({
                    "start_sec": valid_seg["start_offset_sec"],
                    "end_sec": valid_seg["end_offset_sec"],
                    "distance": float('inf')
                })
                continue
            
            v1 = np.array(seg1["embedding"], dtype=np.float32)
            v2 = np.array(seg2["embedding"], dtype=np.float32)
            
            if distance_metric == "cosine":
                # Cosine distance
                dot = np.dot(v1, v2)
                norm1 = np.linalg.norm(v1)
                norm2 = np.linalg.norm(v2)
                dist = 1.0 - (dot / (norm1 * norm2)) if norm1 > 0 and norm2 > 0 else 1.0
            else:
                # Euclidean distance
                dist = float(np.linalg.norm(v1 - v2))
            
            all_distances.append(float(dist))
            
            if float(dist) > threshold:
                differing_segments.append({
                    "start_sec": seg1["start_offset_sec"],
                    "end_sec": seg1["end_offset_sec"],
                    "distance": float(dist)
                })
        
        if all_distances:
            logger.info(f"Distance stats - Min: {min(all_distances):.4f}, Max: {max(all_distances):.4f}, Mean: {np.mean(all_distances):.4f}")
        
        logger.info(f"Found {len(differing_segments)} differences with threshold {threshold}")
        
        return {
            "filename1": embed_data1["filename"],
            "filename2": embed_data2["filename"],
            "differences": differing_segments,
            "total_segments": max(len(segments1), len(segments2)),
            "differing_segments": len(differing_segments),
            "threshold_used": threshold
        }
        
    except Exception as e:
        logger.error(f"Error comparing videos: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to compare videos: {str(e)}")

@app.get("/serve-video/{video_id}")
async def serve_video(video_id: str):
    if video_id not in video_storage:
        raise HTTPException(status_code=404, detail="Video not found")
    
    video_data = video_storage[video_id]
    s3_url = video_data["s3_url"]
    
    # Generate a presigned URL for direct access
    presigned_url = get_s3_presigned_url(s3_url)
    
    return {"video_url": presigned_url}

@app.get("/embedding-status/{embedding_id}")
async def get_embedding_status(embedding_id: str):
    """Get the status of embedding generation for a video."""
    if embedding_id not in embedding_storage:
        raise HTTPException(status_code=404, detail="Embedding not found")
    
    embedding_data = embedding_storage[embedding_id]
    return {
        "embedding_id": embedding_id,
        "filename": embedding_data["filename"],
        "status": embedding_data["status"],
        "duration": embedding_data.get("duration"),
        "completed_at": embedding_data.get("completed_at"),
        "error": embedding_data.get("error")
    }

@app.get("/video-status/{video_id}")
async def get_video_status(video_id: str):
    """Get the status of a video including its embedding status."""
    if video_id not in video_storage:
        raise HTTPException(status_code=404, detail="Video not found")
    
    video_data = video_storage[video_id]
    embedding_id = video_data["embedding_id"]
    
    embedding_status = "unknown"
    if embedding_id in embedding_storage:
        embedding_status = embedding_storage[embedding_id]["status"]
    
    return {
        "video_id": video_id,
        "filename": video_data["filename"],
        "status": video_data["status"],
        "embedding_status": embedding_status,
        "duration": video_data.get("duration"),
        "upload_timestamp": video_data["upload_timestamp"]
    }

# Custom 404 handler
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    client_host = request.client.host if request.client else "unknown"
    path = str(request.url.path)
    if request.url.query:
        path += f"?{request.url.query}"
    
    logger.warning(f"404 Not Found: {client_host} attempted to access {request.method} {path}")
    
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The requested resource {path} was not found",
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)