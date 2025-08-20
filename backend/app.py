from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
import logging
import sqlite3
from twelvelabs import TwelveLabs
from twelvelabs.models.embed import EmbeddingsTask
import hashlib
import numpy as np
import os
from datetime import datetime, timezone
import sys
import boto3
from botocore.exceptions import ClientError
import uuid
import asyncio
import pytz

# Configure logging with PST timezone
pst = pytz.timezone('US/Pacific')

class PSTFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=pst)
        if datefmt:
            return dt.strftime(datefmt)
        else:
            return dt.strftime('%Y-%m-%d %H:%M:%S %Z')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set the formatter for the root logger
for handler in logging.root.handlers:
    handler.setFormatter(PSTFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Pydantic models
class ApiKeyRequest(BaseModel):
    key: str

class ApiKeyResponse(BaseModel):
    key: str
    isValid: bool

class VideoUploadResponse(BaseModel):
    message: str
    filename: str
    video_id: str
    embedding_id: str
    status: str

class DifferenceSegment(BaseModel):
    start_sec: float
    end_sec: float
    distance: float
    
    class Config:
        json_encoders = {
            float: lambda v: float(v) if v != float('inf') else 999999.0
        }

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

class CancelTaskRequest(BaseModel):
    embedding_id: str

# FastAPI app
app = FastAPI(title="SAGE Backend", version="2.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://tl-sage.vercel.app",
        "https://tl-sage.vercel.app/",
        "https://tl-sage.vercel.app/*"
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

def init_database():
    """Initialize the database with API keys table."""
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.execute("PRAGMA table_info(api_keys)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'api_key' not in columns:
            conn.execute('ALTER TABLE api_keys ADD COLUMN api_key TEXT')
            conn.commit()
            logger.info("Added api_key column to existing api_keys table")
    except Exception:
        logger.info("Creating new api_keys table")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_hash TEXT UNIQUE NOT NULL,
                api_key TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
    finally:
        conn.close()

# Initialize database
init_database()

# S3 Configuration
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "tl-sage-bucket")
S3_REGION = os.getenv("S3_REGION", "us-east-2")
S3_PROFILE = os.getenv("S3_PROFILE", "dev")

# Initialize S3 client
s3_client = None
try:
    session = boto3.Session(profile_name=S3_PROFILE, region_name=S3_REGION)
    s3_client = session.client('s3')
    s3_client.list_buckets()
    logger.info(f"S3 client initialized using profile '{S3_PROFILE}' for bucket: {S3_BUCKET_NAME}")
except Exception as e:
    logger.warning(f"S3 client initialization failed: {e}")
    logger.warning("S3 functionality will be disabled. Make sure AWS SSO is configured and you're logged in.")
    s3_client = None

# Global state
embedding_storage: Dict[str, Any] = {}
video_storage: Dict[str, Dict[str, Any]] = {}
current_api_key = None
tl_client = None
start_time = datetime.now()
active_tasks: Dict[str, Any] = {}

# Add a queue for pending videos at the top of the file, after the existing storage variables
pending_videos = []  # Queue for videos waiting to be processed
processing_video = None  # Currently processing video ID

# Utility functions
def get_s3_presigned_url(s3_url: str, expiration: int = 3600) -> str:
    """Generate a presigned URL for an S3 object."""
    if not s3_client:
        raise Exception("S3 client not initialized")
    
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

async def upload_to_s3_streaming(file: UploadFile) -> str:
    """Upload a file to S3 using streaming to avoid memory issues."""
    if not s3_client:
        raise Exception("S3 client not initialized")
    
    file_key = f"videos/{uuid.uuid4()}_{file.filename}"
    
    try:
        logger.info(f"Starting streaming S3 upload for {file.filename}")
        
        # Use multipart upload for large files
        response = s3_client.create_multipart_upload(
            Bucket=S3_BUCKET_NAME,
            Key=file_key,
            ContentType=file.content_type,
            Metadata={
                'original_filename': file.filename,
                'upload_timestamp': datetime.now().isoformat()
            }
        )
        
        upload_id = response['UploadId']
        parts = []
        part_number = 1
        chunk_size = 10 * 1024 * 1024  # 10MB chunks
        
        try:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                
                logger.info(f"Uploading part {part_number} for {file.filename} ({len(chunk)} bytes)")
                
                part_response = s3_client.upload_part(
                    Bucket=S3_BUCKET_NAME,
                    Key=file_key,
                    PartNumber=part_number,
                    UploadId=upload_id,
                    Body=chunk
                )
                
                parts.append({
                    'ETag': part_response['ETag'],
                    'PartNumber': part_number
                })
                
                part_number += 1
            
            # Complete multipart upload
            s3_client.complete_multipart_upload(
                Bucket=S3_BUCKET_NAME,
                Key=file_key,
                UploadId=upload_id,
                MultipartUpload={'Parts': parts}
            )
            
            s3_url = f"s3://{S3_BUCKET_NAME}/{file_key}"
            logger.info(f"File uploaded to S3: {s3_url}")
            return s3_url
            
        except Exception as e:
            # Abort multipart upload on error
            try:
                s3_client.abort_multipart_upload(
                    Bucket=S3_BUCKET_NAME,
                    Key=file_key,
                    UploadId=upload_id
                )
            except:
                pass
            raise e
        
    except ClientError as e:
        logger.error(f"Failed to upload file to S3: {e}")
        raise Exception(f"S3 upload failed: {str(e)}")

def get_twelve_labs_client(api_key: str):
    """Get or create TwelveLabs client."""
    global tl_client, current_api_key
    
    if tl_client and current_api_key == api_key:
        return tl_client
    
    try:
        tl_client = TwelveLabs(api_key=api_key)
        current_api_key = api_key
        
        # Save API key hash and the actual key
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        conn = sqlite3.connect(DB_PATH)
        conn.execute('INSERT OR REPLACE INTO api_keys (key_hash, api_key) VALUES (?, ?)', 
                     (key_hash, api_key))
        conn.commit()
        conn.close()
        
        logger.info("Successfully initialized TwelveLabs client")
        return tl_client
    except Exception as e:
        logger.error(f"Error initializing TwelveLabs client: {e}")
        raise HTTPException(status_code=401, detail="Invalid API key")

def get_stored_api_key() -> str:
    """Get the stored API key from database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute('SELECT api_key FROM api_keys ORDER BY created_at DESC LIMIT 1')
    stored_api_key = cursor.fetchone()
    conn.close()
    
    if not stored_api_key or not stored_api_key[0]:
        raise HTTPException(status_code=400, detail="No API key found. Please validate your API key first.")
    
    return stored_api_key[0]

# Async functions
async def generate_embeddings_async(embedding_id: str, s3_url: str, api_key: str):
    """Asynchronously generate embeddings for a video from S3."""
    global processing_video
    
    try:
        logger.info(f"Starting async embedding generation for {embedding_id}")
        
        # Update status
        embedding_storage[embedding_id]["status"] = "processing"
        
        # Get TwelveLabs client
        tl = get_twelve_labs_client(api_key)
        
        # Generate presigned URL for TwelveLabs to access the video
        logger.info(f"Generating presigned URL for {embedding_id}")
        presigned_url = get_s3_presigned_url(s3_url)
        
        # Create embedding task using presigned HTTPS URL
        logger.info(f"Creating embedding task for {embedding_id}")
        task = tl.embed.task.create(
            model_name="Marengo-retrieval-2.7",
            video_url=presigned_url,
            video_clip_length=2,
            video_embedding_scopes=["clip", "video"]
        )
        
        # Store task for potential cancellation
        active_tasks[embedding_id] = task
        
        logger.info(f"Embedding task {task.id} created for {embedding_id}")
        
        # Wait for completion
        def on_task_update(task: EmbeddingsTask):
            logger.info(f"Task {task.id} status: {task.status}")
        
        # Add timeout for very long videos (over 15 minutes)
        # TwelveLabs might have issues with extremely long videos
        timeout_seconds = 1800  # 30 minutes default
        logger.info(f"Starting to wait for task {task.id} completion with timeout: {timeout_seconds}s")
        
        try:
            task.wait_for_done(sleep_interval=5, callback=on_task_update, timeout=timeout_seconds)
            logger.info(f"Task {task.id} completed, retrieving results...")
        except Exception as e:
            logger.error(f"Task {task.id} timed out or failed during wait: {e}")
            raise Exception(f"Embedding task timed out after {timeout_seconds}s")
        
        # Remove from active tasks
        if embedding_id in active_tasks:
            del active_tasks[embedding_id]
        
        # Get completed task
        completed_task = tl.embed.task.retrieve(task.id)
        
        # Validate that the task actually succeeded
        if completed_task.status != "ready":
            raise Exception(f"Task {completed_task.id} failed with status: {completed_task.status}")
        
        # Check if we have embeddings
        if not completed_task.video_embedding:
            logger.error(f"Task {completed_task.id} completed but no video_embedding found")
            logger.error(f"Task status: {completed_task.status}")
            logger.error(f"Task error: {getattr(completed_task, 'error', 'No error field')}")
            raise Exception(f"Task {completed_task.id} completed but no video_embedding found")
        
        if not completed_task.video_embedding.segments:
            logger.error(f"Task {completed_task.id} completed but no segments found in video_embedding")
            logger.error(f"Video embedding object: {completed_task.video_embedding}")
            logger.error(f"Video embedding type: {type(completed_task.video_embedding)}")
            logger.error(f"Video embedding attributes: {dir(completed_task.video_embedding)}")
            raise Exception(f"Task {completed_task.id} completed but no segments found in video_embedding")
        
        # Log successful embedding generation details
        logger.info(f"Successfully generated embeddings for {embedding_id}")
        logger.info(f"Task ID: {completed_task.id}")
        logger.info(f"Task status: {completed_task.status}")
        logger.info(f"Video embedding type: {type(completed_task.video_embedding)}")
        logger.info(f"Number of segments: {len(completed_task.video_embedding.segments)}")
        
        # Calculate duration from video metadata or segments
        duration = 0
        if completed_task.video_embedding and completed_task.video_embedding.segments:
            # Get the actual end time of the last segment
            last_segment = completed_task.video_embedding.segments[-1]
            duration = last_segment.end_offset_sec
            
            # Log segment information for debugging
            total_segments = len(completed_task.video_embedding.segments)
            logger.info(f"Video has {total_segments} segments")
            logger.info(f"First segment: {completed_task.video_embedding.segments[0].start_offset_sec}s - {completed_task.video_embedding.segments[0].end_offset_sec}s")
            logger.info(f"Last segment: {last_segment.start_offset_sec}s - {last_segment.end_offset_sec}s")
            logger.info(f"Calculated duration: {duration}s")
            
            # Verify segment spacing is correct (should be 2 seconds apart)
            if total_segments > 1:
                first_gap = completed_task.video_embedding.segments[1].start_offset_sec - completed_task.video_embedding.segments[0].start_offset_sec
                logger.info(f"Segment spacing: {first_gap}s (should be 2s)")
                
            # Additional validation for long videos
            if duration > 600:  # 10 minutes
                logger.info(f"Long video detected ({duration}s), validating segment count")
                expected_segments = duration / 2  # 2-second segments
                if abs(total_segments - expected_segments) > 10:  # Allow some tolerance
                    logger.warning(f"Segment count mismatch for long video. Expected ~{expected_segments}, got {total_segments}")
                    
                # Additional validation for very long videos
                if duration > 900:  # 15 minutes
                    logger.info(f"Very long video detected ({duration}s), performing additional validation")
                    if total_segments < 100:  # Should have at least 100 segments for a 15+ min video
                        logger.error(f"Very long video has suspiciously few segments: {total_segments}")
                        logger.error(f"This suggests the embedding generation may have failed")
                        raise Exception(f"Very long video ({duration}s) has insufficient segments ({total_segments}) - embedding generation likely failed")
                    
                    # Check if segments cover the full duration
                    if last_segment.end_offset_sec < duration * 0.8:  # Should cover at least 80% of duration
                        logger.error(f"Segments don't cover full video duration. Last segment ends at {last_segment.end_offset_sec}s, video is {duration}s")
                        raise Exception(f"Segments don't cover full video duration - embedding generation incomplete")
        else:
            raise Exception(f"No segments found in completed task {completed_task.id}")
        
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
        
        # Process next video in queue if available
        if pending_videos:
            next_video = pending_videos.pop(0)
            logger.info(f"Starting processing for next video in queue: {next_video['video_id']}")
            processing_video = next_video['video_id']
            asyncio.create_task(generate_embeddings_async(
                next_video['embedding_id'], 
                next_video['s3_url'], 
                next_video['api_key']
            ))
        else:
            # No more videos to process
            processing_video = None
            logger.info("No more videos in queue, processing complete")
        
    except Exception as e:
        logger.error(f"Error in async embedding generation for {embedding_id}: {e}")
        embedding_storage[embedding_id]["status"] = "failed"
        embedding_storage[embedding_id]["error"] = str(e)
        
        # Remove from active tasks
        if embedding_id in active_tasks:
            del active_tasks[embedding_id]
        
        # Even on error, try to process next video in queue
        if pending_videos:
            next_video = pending_videos.pop(0)
            logger.info(f"Starting processing for next video in queue after error: {next_video['video_id']}")
            processing_video = next_video['video_id']
            asyncio.create_task(generate_embeddings_async(
                next_video['embedding_id'], 
                next_video['s3_url'], 
                next_video['api_key']
            ))
        else:
            processing_video = None
            logger.info("No more videos in queue after error, processing complete")

# API endpoints
@app.post("/validate-key", response_model=ApiKeyResponse)
async def validate_api_key(request: ApiKeyRequest):
    """Validate TwelveLabs API key and store hash securely."""
    logger.info("Validating API key...")
    try:
        # Test the API key
        client = TwelveLabs(api_key=request.key)
        client.task.list()  # Test API call
        
        # Save API key hash and the actual key
        key_hash = hashlib.sha256(request.key.encode()).hexdigest()
        conn = sqlite3.connect(DB_PATH)
        conn.execute('INSERT OR REPLACE INTO api_keys (key_hash, api_key) VALUES (?, ?)', 
                     (key_hash, request.key))
        conn.commit()
        conn.close()
        
        logger.info("API key validation successful")
        return ApiKeyResponse(key=request.key, isValid=True)
    except Exception as e:
        logger.error(f"API key validation failed: {e}")
        return ApiKeyResponse(key=request.key, isValid=False)

@app.post("/upload-and-generate-embeddings", response_model=VideoUploadResponse)
async def upload_and_generate_embeddings(file: UploadFile = File(...)):
    """Upload video file and start AI embedding generation."""
    global processing_video
    
    logger.info(f"=== UPLOAD REQUEST RECEIVED ===")
    logger.info(f"File: {file.filename}")
    logger.info(f"Content-Type: {file.content_type}")
    logger.info(f"File size: {file.size if hasattr(file, 'size') else 'Unknown'}")
    
    if not file.content_type or not file.content_type.startswith('video/'):
        logger.error(f"Invalid content type: {file.content_type}")
        raise HTTPException(status_code=400, detail="File must be a video")
    
    try:
        logger.info(f"Starting upload for {file.filename}")
        
        # Get stored API key
        api_key = get_stored_api_key()
        logger.info("API key retrieved successfully")
        
        # Upload to S3 using streaming
        logger.info(f"Starting S3 upload for {file.filename}...")
        s3_url = await upload_to_s3_streaming(file)
        logger.info(f"S3 upload completed: {s3_url}")
        
        # Generate unique IDs
        video_id = f"video_{uuid.uuid4()}"
        embedding_id = f"embed_{uuid.uuid4()}"
        logger.info(f"Generated IDs - Video: {video_id}, Embedding: {embedding_id}")
        
        # Store video metadata (in-memory only)
        video_storage[video_id] = {
            "filename": file.filename,
            "s3_url": s3_url,
            "status": "uploaded",
            "upload_timestamp": datetime.now().isoformat(),
            "embedding_id": embedding_id
        }
        
        # Initialize embedding storage (in-memory only)
        embedding_storage[embedding_id] = {
            "filename": file.filename,
            "status": "pending",
            "video_id": video_id,
            "s3_url": s3_url
        }
        
        logger.info("Video and embedding data stored in memory")

        # Check if we can start processing immediately or need to queue
        if processing_video is None:
            # No video currently processing, start immediately
            logger.info("Starting embedding generation immediately...")
            processing_video = video_id
            asyncio.create_task(generate_embeddings_async(embedding_id, s3_url, api_key))
        else:
            # Another video is processing, add to queue
            logger.info(f"Video {video_id} queued, waiting for {processing_video} to complete")
            pending_videos.append({
                "video_id": video_id,
                "embedding_id": embedding_id,
                "s3_url": s3_url,
                "api_key": api_key
            })
        
        logger.info(f"=== UPLOAD COMPLETED SUCCESSFULLY ===")
        logger.info(f"File {file.filename} uploaded to S3 and {'embedding generation started' if processing_video == video_id else 'queued for processing'}")
        
        return VideoUploadResponse(
            message="Video uploaded successfully. Embedding generation in progress." if processing_video == video_id else "Video uploaded successfully. Waiting for previous video to complete.",
            filename=file.filename,
            video_id=video_id,
            embedding_id=embedding_id,
            status="processing" if processing_video == video_id else "queued"
        )
        
    except Exception as e:
        logger.error(f"=== UPLOAD FAILED ===")
        logger.error(f"Error uploading file {file.filename}: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

@app.post("/cancel-embedding-task")
async def cancel_embedding_task(request: CancelTaskRequest):
    """Cancel an active embedding task."""
    embedding_id = request.embedding_id
    
    if embedding_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found or already completed")
    
    try:
        task = active_tasks[embedding_id]
        logger.info(f"Cancelling embedding task {task.id} for {embedding_id}")
        
        # Update status to cancelled
        embedding_storage[embedding_id]["status"] = "cancelled"
        embedding_storage[embedding_id]["error"] = "Task cancelled by user"
        
        # Remove from active tasks
        del active_tasks[embedding_id]
        
        logger.info(f"Successfully cancelled embedding task for {embedding_id}")
        return {"message": "Task cancelled successfully"}
        
    except Exception as e:
        logger.error(f"Error cancelling task for {embedding_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")

@app.post("/compare-local-videos", response_model=ComparisonResponse)
async def compare_local_videos(
    embedding_id1: str = Query(...),
    embedding_id2: str = Query(...),
    threshold: float = Query(0.1),
    distance_metric: str = Query("cosine")
):
    """Compare two videos using their embedding IDs."""
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
        
        # Get actual embedding segments from TwelveLabs
        segments1 = []
        segments2 = []
        
        if embed_data1["embeddings"] and embed_data1["embeddings"].segments:
            segments1 = [{
                "start_offset_sec": seg.start_offset_sec,
                "end_offset_sec": seg.end_offset_sec,
                "embedding": seg.embeddings_float
            } for seg in embed_data1["embeddings"].segments]
            logger.info(f"Video1 segments extracted: {len(segments1)}")
        else:
            logger.error(f"Video1 has no embeddings or segments! Embeddings object: {embed_data1.get('embeddings')}")
        
        if embed_data2["embeddings"] and embed_data2["embeddings"].segments:
            segments2 = [{
                "start_offset_sec": seg.start_offset_sec,
                "end_offset_sec": seg.end_offset_sec,
                "embedding": seg.embeddings_float
            } for seg in embed_data2["embeddings"].segments]
            logger.info(f"Video2 segments extracted: {len(segments2)}")
        else:
            logger.error(f"Video2 has no embeddings or segments! Embeddings object: {embed_data2.get('embeddings')}")
        
        # Validate segment data integrity
        if segments1:
            logger.info(f"Video1 first segment: {segments1[0]}")
            logger.info(f"Video1 last segment: {segments1[-1]}")
        if segments2:
            logger.info(f"Video2 first segment: {segments2[0]}")
            logger.info(f"Video2 last segment: {segments2[-1]}")
        
        logger.info(f"Comparing {len(segments1)} segments from video1 with {len(segments2)} segments from video2, threshold: {threshold}")
        
        # Log first few and last few segments for debugging (don't log all for large videos)
        if len(segments1) > 0:
            first_segments1 = segments1[:3]
            last_segments1 = segments1[-3:] if len(segments1) > 3 else []
            logger.info(f"Video1 first 3 segments: {[(s['start_offset_sec'], s['end_offset_sec']) for s in first_segments1]}")
            if last_segments1:
                logger.info(f"Video1 last 3 segments: {[(s['start_offset_sec'], s['end_offset_sec']) for s in last_segments1]}")
        
        if len(segments2) > 0:
            first_segments2 = segments2[:3]
            last_segments2 = segments2[-3:] if len(segments2) > 3 else []
            logger.info(f"Video2 first 3 segments: {[(s['start_offset_sec'], s['end_offset_sec']) for s in first_segments2]}")
            if last_segments2:
                logger.info(f"Video2 last 3 segments: {[(s['start_offset_sec'], s['end_offset_sec']) for s in last_segments2]}")
        
        logger.info(f"Embedding data1 keys: {list(embed_data1.keys())}")
        logger.info(f"Embedding data2 keys: {list(embed_data2.keys())}")
        logger.info(f"Embedding1 has embeddings: {embed_data1.get('embeddings') is not None}")
        logger.info(f"Embedding2 has embeddings: {embed_data2.get('embeddings') is not None}")
        
        # Get video durations for proper timeline handling
        duration1 = embed_data1.get("duration", 0)
        duration2 = embed_data2.get("duration", 0)
        max_duration = max(duration1, duration2)
        
        logger.info(f"Video durations - Video1: {duration1}s, Video2: {duration2}s, Max: {max_duration}s")
        
        # Validate segment data
        if len(segments1) == 0:
            logger.error(f"Video1 has no segments! Duration: {duration1}s")
            raise HTTPException(status_code=400, detail=f"Video1 has no segments - embedding generation may have failed. Duration: {duration1}s")
        if len(segments2) == 0:
            logger.error(f"Video2 has no segments! Duration: {duration2}s")
            raise HTTPException(status_code=400, detail=f"Video2 has no segments - embedding generation may have failed. Duration: {duration2}s")
        
        # Expected segment count based on duration
        expected_segments1 = max(1, int(duration1 / 2))  # 2-second segments
        expected_segments2 = max(1, int(duration2 / 2))
        logger.info(f"Expected segments - Video1: {expected_segments1}, Video2: {expected_segments2}")
        logger.info(f"Actual segments - Video1: {len(segments1)}, Video2: {len(segments2)}")
        
        # Additional validation for segment count vs duration
        if len(segments1) < expected_segments1 * 0.8:  # Allow 20% tolerance
            logger.error(f"Video1 has insufficient segments. Expected at least {expected_segments1 * 0.8}, got {len(segments1)}")
            raise HTTPException(status_code=400, detail=f"Video1 has insufficient segments - embedding generation incomplete. Expected ~{expected_segments1}, got {len(segments1)}")
        
        if len(segments2) < expected_segments2 * 0.8:  # Allow 20% tolerance
            logger.error(f"Video2 has insufficient segments. Expected at least {expected_segments2 * 0.8}, got {len(segments2)}")
            raise HTTPException(status_code=400, detail=f"Video2 has insufficient segments - embedding generation incomplete. Expected ~{expected_segments2}, got {len(segments2)}")
        
        # Validate that segments cover the full duration
        if segments1 and segments1[-1]['end_offset_sec'] < duration1 * 0.8:
            logger.error(f"Video1 segments don't cover full duration. Last segment ends at {segments1[-1]['end_offset_sec']}s, video is {duration1}s")
            raise HTTPException(status_code=400, detail=f"Video1 segments don't cover full duration - embedding generation incomplete")
        
        if segments2 and segments2[-1]['end_offset_sec'] < duration2 * 0.8:
            logger.error(f"Video2 segments don't cover full duration. Last segment ends at {segments2[-1]['end_offset_sec']}s, video is {duration2}s")
            raise HTTPException(status_code=400, detail=f"Video2 segments don't cover full duration - embedding generation incomplete")
        
        logger.info(f"Segment validation passed - both videos have sufficient segments covering full duration")
        
        # Compare segments using actual embedding data
        differing_segments = []
        all_distances = []
        matched_segments = 0
        
        # Handle case where one or both videos have no segments
        if len(segments1) == 0 or len(segments2) == 0:
            logger.error(f"Cannot compare videos - missing segments! Video1: {len(segments1)}, Video2: {len(segments2)}")
            
            # Mark entire duration as different
            differing_segments.append(DifferenceSegment(
                start_sec=0,
                end_sec=max_duration,
                distance=999999.0  # Use large number instead of infinity
            ))
            
            # Return early with error response
            return ComparisonResponse(
                filename1=embed_data1["filename"],
                filename2=embed_data2["filename"],
                differences=differing_segments,
                total_segments=0,
                differing_segments=1,
                threshold_used=threshold
            )
        
        # Compare segments at regular intervals based on the shorter video's segments
        min_segments = min(len(segments1), len(segments2))
        logger.info(f"Will compare {min_segments} segments (minimum of both videos)")
        
        if min_segments == 0:
            # This shouldn't happen now due to the check above, but just in case
            logger.error("min_segments is 0 despite having segments - this is a bug!")
            differing_segments.append(DifferenceSegment(
                start_sec=0,
                end_sec=max_duration,
                distance=999999.0
            ))
        else:
            # Compare corresponding segments - this should give us exactly min_segments results
            for i in range(min_segments):
                seg1 = segments1[i]
                seg2 = segments2[i]
                
                logger.info(f"Comparing segment {i}: Video1 {seg1['start_offset_sec']}-{seg1['end_offset_sec']}s vs Video2 {seg2['start_offset_sec']}-{seg2['end_offset_sec']}s")
                
                # Calculate distance between embeddings
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
                matched_segments += 1
                
                logger.info(f"Segment {i} distance: {dist:.4f} (threshold: {threshold})")
                
                # Only add segments that exceed the threshold
                if float(dist) > threshold:
                    differing_segments.append(DifferenceSegment(
                        start_sec=seg1["start_offset_sec"],
                        end_sec=seg1["end_offset_sec"],
                        distance=float(dist)
                    ))
            
            # Only add remaining segments if they don't overlap with existing ones
            if len(segments1) > len(segments2):
                # Video1 has more segments - only add if they don't overlap
                for i in range(len(segments2), len(segments1)):
                    seg = segments1[i]
                    # Check if this segment overlaps with any existing segment
                    overlaps = False
                    for existing in differing_segments:
                        if (seg["start_offset_sec"] < existing.end_sec and 
                            seg["end_offset_sec"] > existing.start_sec):
                            overlaps = True
                            break
                    
                    if not overlaps:
                        differing_segments.append(DifferenceSegment(
                            start_sec=seg["start_offset_sec"],
                            end_sec=seg["end_offset_sec"],
                            distance=999999.0  # Use large number instead of infinity
                        ))
            elif len(segments2) > len(segments1):
                # Video2 has more segments - only add if they don't overlap
                for i in range(len(segments1), len(segments2)):
                    seg = segments2[i]
                    # Check if this segment overlaps with any existing segment
                    overlaps = False
                    for existing in differing_segments:
                        if (seg["start_offset_sec"] < existing.end_sec and 
                            seg["end_offset_sec"] > existing.start_sec):
                            overlaps = True
                            break
                    
                    if not overlaps:
                        differing_segments.append(DifferenceSegment(
                            start_sec=seg["start_offset_sec"],
                            end_sec=seg["end_offset_sec"],
                            distance=999999.0  # Use large number instead of infinity
                        ))
        
        # Calculate similarity percentage based on segments that are NOT different
        if min_segments > 0:
            # Only count segments that were actually compared (not the 999999.0 ones)
            actual_differing = len([d for d in differing_segments if d.distance < 999999.0])
            similar_segments = min_segments - actual_differing
            similarity_percent = max(0, (similar_segments / min_segments) * 100)
        else:
            similarity_percent = 0
        
        if all_distances:
            logger.info(f"Distance stats - Min: {min(all_distances):.4f}, Max: {max(all_distances):.4f}, Mean: {np.mean(all_distances):.4f}")
            logger.info(f"Similarity: {similarity_percent:.2f}%")
        
        # Count actual differing segments (excluding 999999.0 ones)
        actual_differing = len([d for d in differing_segments if d.distance < 999999.0])
        extra_segments = len([d for d in differing_segments if d.distance >= 999999.0])
        
        logger.info(f"Found {len(differing_segments)} total segments in response")
        logger.info(f"  - {actual_differing} actual differing segments (distance > {threshold})")
        logger.info(f"  - {extra_segments} extra segments from different video lengths")
        logger.info(f"Matched segments: {matched_segments}, Total segments: {min_segments}")
        logger.info(f"Similarity calculation: {min_segments - actual_differing}/{min_segments} = {similarity_percent:.2f}%")
        
        return ComparisonResponse(
            filename1=embed_data1["filename"],
            filename2=embed_data2["filename"],
            differences=differing_segments,
            total_segments=min_segments,
            differing_segments=len(differing_segments),
            threshold_used=threshold
        )
        
    except Exception as e:
        logger.error(f"Error comparing videos: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to compare videos: {str(e)}")

@app.get("/serve-video/{video_id}")
async def serve_video(video_id: str):
    """Get video URL for streaming."""
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
    """Get video processing status."""
    logger.info(f"Video status request for {video_id}")
    logger.info(f"Available video IDs: {list(video_storage.keys())}")
    
    if video_id not in video_storage:
        logger.warning(f"Video {video_id} not found in storage")
        raise HTTPException(status_code=404, detail="Video not found")
    
    video_data = video_storage[video_id]
    embedding_id = video_data.get("embedding_id")
    
    if embedding_id and embedding_id in embedding_storage:
        embed_data = embedding_storage[embedding_id]
        return {
            "video_id": video_id,
            "filename": video_data["filename"],
            "status": video_data["status"],
            "embedding_status": embed_data["status"],
            "duration": video_data.get("duration"),
            "upload_timestamp": video_data["upload_timestamp"]
        }
    else:
        return {
            "video_id": video_id,
            "filename": video_data["filename"],
            "status": video_data["status"],
            "embedding_status": "unknown",
            "duration": video_data.get("duration"),
            "upload_timestamp": video_data["upload_timestamp"]
        }

@app.post("/cancel-video/{video_id}")
async def cancel_video_processing(video_id: str):
    """Cancel video processing and cleanup resources."""
    try:
        logger.info(f"Cancelling video processing for {video_id}")
        
        if video_id not in video_storage:
            raise HTTPException(status_code=404, detail="Video not found")
        
        video_data = video_storage[video_id]
        embedding_id = video_data.get("embedding_id")
        
        # Cancel embedding task if it exists and is still processing
        if embedding_id and embedding_id in embedding_storage:
            embed_data = embedding_storage[embedding_id]
            if embed_data["status"] in ["processing", "pending"]:
                logger.info(f"Cancelling embedding task for {embedding_id}")
                try:
                    # Cancel the TwelveLabs task
                    if "task_id" in embed_data:
                        task_id = embed_data["task_id"]
                        twelve_labs_client = get_twelve_labs_client()
                        twelve_labs_client.embed_tasks.delete(task_id)
                        logger.info(f"Cancelled TwelveLabs task {task_id}")
                except Exception as e:
                    logger.warning(f"Failed to cancel TwelveLabs task: {e}")
                
                # Mark embedding as cancelled
                embed_data["status"] = "cancelled"
                embed_data["error"] = "Cancelled by user"
        
        # Remove from storage
        del video_storage[video_id]
        if embedding_id and embedding_id in embedding_storage:
            del embedding_storage[embedding_id]
        
        logger.info(f"Successfully cancelled and cleaned up {video_id}")
        return {"message": "Video processing cancelled successfully"}
        
    except Exception as e:
        logger.error(f"Error cancelling video {video_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel video: {str(e)}")

@app.post("/cancel-embedding-task/{embedding_id}")
async def cancel_embedding_task(embedding_id: str):
    """Cancel a specific embedding task."""
    try:
        logger.info(f"Cancelling embedding task for {embedding_id}")
        
        if embedding_id not in embedding_storage:
            raise HTTPException(status_code=404, detail="Embedding not found")
        
        embed_data = embedding_storage[embedding_id]
        
        if embed_data["status"] not in ["processing", "pending"]:
            raise HTTPException(status_code=400, detail="Embedding is not in a cancellable state")
        
        # Cancel the TwelveLabs task
        if "task_id" in embed_data:
            task_id = embed_data["task_id"]
            try:
                twelve_labs_client = get_twelve_labs_client()
                twelve_labs_client.embed_tasks.delete(task_id)
                logger.info(f"Cancelled TwelveLabs task {task_id}")
            except Exception as e:
                logger.warning(f"Failed to cancel TwelveLabs task: {e}")
        
        # Mark as cancelled
        embed_data["status"] = "cancelled"
        embed_data["error"] = "Cancelled by user"
        
        logger.info(f"Successfully cancelled embedding task {embedding_id}")
        return {"message": "Embedding task cancelled successfully"}
        
    except Exception as e:
        logger.error(f"Error cancelling embedding task {embedding_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel embedding task: {str(e)}")

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
    
    # Check database status (only for API keys)
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("SELECT 1")
        db_status = "healthy"
        conn.close()
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
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        timeout_keep_alive=300,  # 5 minutes keep-alive
        timeout_graceful_shutdown=300,  # 5 minutes graceful shutdown
        limit_concurrency=10,  # Limit concurrent connections
        limit_max_requests=1000  # Restart worker after 1000 requests
    )
