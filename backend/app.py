from fastapi import FastAPI, HTTPException, Request, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
import sqlite3
from twelvelabs import TwelveLabs
import pytz
from twelvelabs.models.embed import EmbeddingsTask
import hashlib
import numpy as np
import tempfile
import os
from datetime import datetime, timezone
import sys
from pathlib import Path
import subprocess
import shutil
from urllib.request import urlopen

# Configure logging with PST timestamps
class PSTFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        # Convert to PST
        pst = pytz.timezone('US/Pacific')
        dt = datetime.fromtimestamp(record.created, tz=pytz.UTC)
        pst_time = dt.astimezone(pst)
        if datefmt:
            return pst_time.strftime(datefmt)
        return pst_time.strftime('%Y-%m-%d %H:%M:%S PST')

# Set up logger with PST formatter
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = PSTFormatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S PST'
)
handler.setFormatter(formatter)
logger.handlers = [handler]
logger.setLevel(logging.INFO)

app = FastAPI(title="SAGE Backend", version="2.0.0")

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

# Minimal CORS to allow direct browser calls from Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tl-sage.vercel.app",
        "https://sage-git-main-jockey.vercel.app",
        "https://sage.vercel.app",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

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

current_api_key = None
tl_client = None
embedding_storage: Dict[str, Any] = {}
video_storage: Dict[str, bytes] = {}
video_path_storage: Dict[str, str] = {}

BASE_DIR = Path(__file__).resolve().parent
VIDEOS_DIR = BASE_DIR / "videos"
VIDEOS_DIR.mkdir(exist_ok=True)

MAX_EMBED_DURATION_SEC = 7200  # 2 hours
MAX_EMBED_SIZE_BYTES = 2 * 1024 * 1024 * 1024  # 2GB

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

class BlobIngestRequest(BaseModel):
    blob_url: str
    filename: Optional[str] = None

# Store for async tasks
embedding_tasks: Dict[str, Dict[str, Any]] = {}

@app.post("/ingest-blob")
async def ingest_blob(request: BlobIngestRequest, tl: TwelveLabs = Depends(get_twelve_labs_client)):
    """Start async processing of video from a Vercel Blob URL.
    Returns immediately with a task ID that can be polled for status.
    """
    try:
        # Generate task ID
        task_id = f"task_{hashlib.sha256((request.blob_url + str(datetime.now())).encode()).hexdigest()[:16]}"
        
        # Store initial task info
        embedding_tasks[task_id] = {
            "status": "starting",
            "blob_url": request.blob_url,
            "filename": request.filename or os.path.basename(request.blob_url),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "error": None,
            "result": None,
            "twelvelabs_tasks": []
        }
        
        # Start async processing in background
        import threading
        thread = threading.Thread(
            target=process_blob_async,
            args=(task_id, request.blob_url, request.filename, tl)
        )
        thread.daemon = True
        thread.start()
        
        return {
            "task_id": task_id,
            "status": "started",
            "message": "Processing started. Poll /ingest-blob/status/{task_id} for updates."
        }
    except Exception as e:
        logger.error(f"Error starting blob ingest: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start blob ingest: {str(e)}")


def process_blob_async(task_id: str, blob_url: str, filename: Optional[str], tl: TwelveLabs):
    """Process blob in background thread."""
    tmp_file_path = None
    try:
        embedding_tasks[task_id]["status"] = "downloading"
        logger.info(f"[Task {task_id}] Starting download from Vercel Blob: {filename or 'unnamed'}")
        logger.info(f"[Task {task_id}] Blob URL: {blob_url[:100]}...")  # Log first 100 chars of URL
        
        # Download blob to a temp mp4 file
        download_start = datetime.now()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
            tmp_file_path = tmp_file.name
            with urlopen(blob_url) as resp:
                # Get content length if available
                content_length = resp.headers.get('Content-Length')
                if content_length:
                    logger.info(f"[Task {task_id}] Downloading {int(content_length) / (1024*1024):.2f} MB")
                
                # Download with progress logging
                downloaded = 0
                chunk_size = 1024 * 1024  # 1MB chunks
                last_log = download_start
                
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    tmp_file.write(chunk)
                    downloaded += len(chunk)
                    
                    # Log progress every 5 seconds
                    now = datetime.now()
                    if (now - last_log).total_seconds() > 5:
                        if content_length:
                            progress = (downloaded / int(content_length)) * 100
                            logger.info(f"[Task {task_id}] Download progress: {progress:.1f}% ({downloaded / (1024*1024):.1f} MB)")
                        else:
                            logger.info(f"[Task {task_id}] Downloaded: {downloaded / (1024*1024):.1f} MB")
                        last_log = now
        
        download_duration = (datetime.now() - download_start).total_seconds()
        file_size = os.path.getsize(tmp_file_path) / (1024*1024)  # MB
        logger.info(f"[Task {task_id}] Download completed: {file_size:.2f} MB in {download_duration:.1f}s ({file_size/download_duration:.1f} MB/s)")

        embedding_tasks[task_id]["status"] = "processing"
        
        # Split if needed based on size/duration
        session_root = Path(tempfile.mkdtemp(prefix="ingest_"))
        parts_dir = session_root / "parts"
        logger.info(f"[Task {task_id}] Checking if video needs splitting...")
        parts = split_video_if_needed(tmp_file_path, parts_dir)
        logger.info(f"[Task {task_id}] Video split into {len(parts)} part(s)")

        # Start all embedding tasks
        for idx, part_path in enumerate(parts):
            logger.info(f"[Task {task_id}] Creating TwelveLabs embedding task for part {idx+1}/{len(parts)}: {part_path}")
            
            try:
                task = tl.embed.task.create(
                    model_name="Marengo-retrieval-2.7",
                    video_file=part_path,
                    video_clip_length=2,
                    video_embedding_scopes=["clip", "video"],
                )
                logger.info(f"[Task {task_id}] TwelveLabs task created: {task.id}")
                
                # Immediately check if embeddings are ready (would indicate TL caching)
                immediate_check = tl.embed.task.retrieve(task.id)
                if immediate_check.status == "ready":
                    logger.info(f"[Task {task_id}] WOW! TwelveLabs returned embeddings IMMEDIATELY for task {task.id} - they must be caching!")
                else:
                    logger.info(f"[Task {task_id}] Initial status: {immediate_check.status} - no immediate cache hit")
                
                embedding_tasks[task_id]["twelvelabs_tasks"].append({
                    "id": task.id,
                    "part_index": idx,
                    "part_path": part_path,
                    "status": "processing"
                })
            except Exception as e:
                logger.error(f"[Task {task_id}] Failed to create TwelveLabs task for part {idx+1}: {e}")
                raise

        # Poll for completion
        all_segments: List[Dict[str, Any]] = []
        total_duration: float = 0.0
        
        while True:
            all_done = True
            for tl_task in embedding_tasks[task_id]["twelvelabs_tasks"]:
                if tl_task["status"] == "completed":
                    continue
                    
                task_status = tl.embed.task.retrieve(tl_task["id"])
                logger.info(f"[Task {task_id}] TwelveLabs task {tl_task['id']} (part {tl_task['part_index']+1}) status: {task_status.status}")
                
                # Log if embeddings are already available on first check
                if hasattr(task_status, 'video_embedding') and task_status.video_embedding and task_status.status != "ready":
                    logger.info(f"[Task {task_id}] TwelveLabs returned embeddings immediately for task {tl_task['id']} - possible server-side optimization")
                
                if task_status.status == "ready":
                    tl_task["status"] = "completed"
                    completed_parts = sum(1 for t in embedding_tasks[task_id]['twelvelabs_tasks'] if t['status'] == 'completed')
                    total_parts = len(embedding_tasks[task_id]['twelvelabs_tasks'])
                    logger.info(f"[Task {task_id}] Part {tl_task['part_index']+1} completed. Progress: {completed_parts}/{total_parts}")
                    
                    # Update progress in task
                    embedding_tasks[task_id]["progress"] = f"{completed_parts}/{total_parts} parts processed"
                    idx = tl_task["part_index"]
                    part_start_offset = sum(run_ffprobe_duration_seconds(parts[i]) or 0.0 for i in range(idx))
                    
                    if task_status.video_embedding and task_status.video_embedding.segments:
                        for seg in task_status.video_embedding.segments:
                            all_segments.append({
                                "start_offset_sec": seg.start_offset_sec + part_start_offset,
                                "end_offset_sec": seg.end_offset_sec + part_start_offset,
                                "embedding": seg.embeddings_float,
                            })
                        total_duration = max(total_duration, part_start_offset + task_status.video_embedding.segments[-1].end_offset_sec)
                elif task_status.status == "failed":
                    # Log all available error information
                    error_details = {
                        "task_id": tl_task['id'],
                        "status": task_status.status,
                    }
                    
                    # Check various possible error fields
                    for attr in ['error', 'error_message', 'message', 'status_message', 'failure_reason']:
                        if hasattr(task_status, attr):
                            error_details[attr] = getattr(task_status, attr)
                    
                    logger.error(f"[Task {task_id}] TwelveLabs task failed with details: {error_details}")
                    
                    # Extract the most relevant error message
                    error_msg = (
                        error_details.get('error_message') or 
                        error_details.get('error') or 
                        error_details.get('message') or 
                        error_details.get('failure_reason') or
                        'Unknown error'
                    )
                    
                    raise Exception(f"TwelveLabs task {tl_task['id']} failed: {error_msg}")
                else:
                    all_done = False
            
            if all_done:
                break
            
            import time
            time.sleep(5)

        # Store results
        embedding_id = f"embed_{hashlib.sha256((blob_url).encode()).hexdigest()[:16]}"
        embedding_storage[embedding_id] = {
            "filename": filename or os.path.basename(blob_url),
            "embeddings": {"segments": all_segments},
            "duration": total_duration,
            "source": "blob",
            "blob_url": blob_url,
        }

        embedding_tasks[task_id]["status"] = "completed"
        embedding_tasks[task_id]["result"] = {
            "embeddings": {"segments": all_segments},
            "filename": filename or os.path.basename(blob_url),
            "duration": total_duration,
            "embedding_id": embedding_id,
            "video_url": blob_url,
        }
        
        # Cleanup parts
        shutil.rmtree(session_root, ignore_errors=True)
        
    except Exception as e:
        logger.error(f"Error processing blob async: {e}")
        embedding_tasks[task_id]["status"] = "failed"
        embedding_tasks[task_id]["error"] = str(e)
    finally:
        try:
            if tmp_file_path and os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
        except Exception:
            pass


@app.get("/ingest-blob/status/{task_id}")
async def get_ingest_status(task_id: str):
    """Get status of async blob ingest task."""
    if task_id not in embedding_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = embedding_tasks[task_id]
    response = {
        "task_id": task_id,
        "status": task["status"],
        "created_at": task["created_at"],
    }
    
    if task["status"] == "completed" and task["result"]:
        response.update(task["result"])
    elif task["status"] == "failed" and task["error"]:
        response["error"] = task["error"]
    elif task["status"] == "processing" and task["twelvelabs_tasks"]:
        # Include progress info
        total = len(task["twelvelabs_tasks"])
        completed = sum(1 for t in task["twelvelabs_tasks"] if t["status"] == "completed")
        response["progress"] = f"{completed}/{total} parts processed"
        
        # Add estimated time remaining if we have progress
        if completed > 0:
            elapsed = (datetime.now(timezone.utc) - datetime.fromisoformat(task["created_at"])).total_seconds()
            avg_time_per_part = elapsed / completed
            remaining_parts = total - completed
            estimated_remaining_seconds = remaining_parts * avg_time_per_part
            response["estimated_remaining_seconds"] = int(estimated_remaining_seconds)
            response["elapsed_seconds"] = int(elapsed)
    
    return response


def run_ffprobe_duration_seconds(file_path: str) -> Optional[float]:
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", file_path
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        return float(result.stdout.strip())
    except Exception:
        return None


def split_video_if_needed(src_path: str, dest_dir: Path) -> List[str]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    duration = run_ffprobe_duration_seconds(src_path) or 0.0
    size_bytes = os.path.getsize(src_path)
    needs_split = (duration and duration > MAX_EMBED_DURATION_SEC) or size_bytes > MAX_EMBED_SIZE_BYTES
    if not needs_split:
        return [src_path]

    # Split by time into chunks no longer than 3600 seconds to stay safely under 2h and reduce size
    segment_time = 3600
    pattern = str(dest_dir / "part_%03d.mp4")
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", src_path, "-c", "copy", "-f", "segment",
                "-reset_timestamps", "1", "-segment_time", str(segment_time), pattern
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except Exception as e:
        logger.error(f"ffmpeg split failed: {e}")
        # If split fails, fallback to single file
        return [src_path]

    # Collect generated parts
    parts = sorted([str(p) for p in dest_dir.glob("part_*.mp4")])
    return parts if parts else [src_path]


def concat_chunks_to_file(chunks_dir: Path, output_path: Path, total_chunks: int) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as out_f:
        for i in range(total_chunks):
            chunk_file = chunks_dir / f"chunk_{i}.bin"
            if not chunk_file.exists():
                raise HTTPException(status_code=400, detail=f"Missing chunk {i}")
            with open(chunk_file, "rb") as cf:
                out_f.write(cf.read())


# Removed legacy chunking endpoints to simplify flow with Vercel Blob

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
        
        segments1 = []
        segments2 = []
        
        if embed_data1.get("embeddings"):
            emb1 = embed_data1["embeddings"]
            if hasattr(emb1, "segments"):
                segments1 = [{
                    "start_offset_sec": seg.start_offset_sec,
                    "end_offset_sec": seg.end_offset_sec,
                    "embedding": seg.embeddings_float
                } for seg in emb1.segments]
            elif isinstance(emb1, dict) and isinstance(emb1.get("segments"), list):
                segments1 = [{
                    "start_offset_sec": seg["start_offset_sec"],
                    "end_offset_sec": seg["end_offset_sec"],
                    "embedding": seg.get("embedding") or seg.get("embeddings_float")
                } for seg in emb1["segments"]]
        
        if embed_data2.get("embeddings"):
            emb2 = embed_data2["embeddings"]
            if hasattr(emb2, "segments"):
                segments2 = [{
                    "start_offset_sec": seg.start_offset_sec,
                    "end_offset_sec": seg.end_offset_sec,
                    "embedding": seg.embeddings_float
                } for seg in emb2.segments]
            elif isinstance(emb2, dict) and isinstance(emb2.get("segments"), list):
                segments2 = [{
                    "start_offset_sec": seg["start_offset_sec"],
                    "end_offset_sec": seg["end_offset_sec"],
                    "embedding": seg.get("embedding") or seg.get("embeddings_float")
                } for seg in emb2["segments"]]
        
        logger.info(f"Comparing {len(segments1)} segments from video1 with {len(segments2)} segments from video2, threshold: {threshold}")
        
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
    # Prefer disk path serving for large files
    from fastapi.responses import FileResponse
    path = video_path_storage.get(video_id)
    if path and os.path.exists(path):
        return FileResponse(path, media_type="video/mp4")
    if video_id in video_storage:
        return Response(content=video_storage[video_id], media_type="video/mp4")
    raise HTTPException(status_code=404, detail="Video not found")

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