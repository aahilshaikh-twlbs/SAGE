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

# Configure comprehensive logging with timestamps and file output
import logging.handlers
import traceback

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Configure logging with both file and console output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.handlers.RotatingFileHandler(
            'logs/sage_backend.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        ),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Set specific loggers to appropriate levels
logging.getLogger('uvicorn').setLevel(logging.INFO)
logging.getLogger('httpx').setLevel(logging.INFO)
logging.getLogger('asyncio').setLevel(logging.WARNING)

app = FastAPI(title="SAGE Backend", version="2.0.0")

@app.on_event("startup")
async def startup_event():
    """Log application startup information"""
    logger.info("=" * 60)
    logger.info("SAGE BACKEND STARTING UP")
    logger.info("=" * 60)
    logger.info(f"Application: {app.title} v{app.version}")
    logger.info(f"Startup time: {datetime.now(timezone.utc)}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"CORS origins: {CORS_ORIGINS}")
    logger.info(f"Database path: {DB_PATH}")
    logger.info("=" * 60)

@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown information"""
    logger.info("=" * 60)
    logger.info("SAGE BACKEND SHUTTING DOWN")
    logger.info("=" * 60)
    logger.info(f"Shutdown time: {datetime.now(timezone.utc)}")
    logger.info(f"Total uptime: {datetime.now(timezone.utc) - server_start_time}")
    logger.info("=" * 60)

import os

# Get CORS origins from environment variable or use defaults
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,https://tl-sage.vercel.app,http://209.38.142.207:8000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
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
        error_traceback = traceback.format_exc()
        logger.error(f"{client_host} - {request.method} {path} - Error: {str(e)} ({duration:.3f}s)")
        logger.error(f"Error traceback: {error_traceback}")
        logger.error(f"Request headers: {dict(request.headers)}")
        logger.error(f"Request body preview: {getattr(request, 'body', 'N/A')}")
        raise

DB_PATH = "sage.db"

# Initialize database with error logging
def init_database():
    try:
        conn = sqlite3.connect(DB_PATH)
        logger.info(f"Database connection established to {DB_PATH}")
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_hash TEXT UNIQUE NOT NULL,
                api_key TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        logger.info("Database tables initialized successfully")
        conn.close()
        logger.info("Database connection closed")
        
    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {e}")
        logger.error(f"SQLite error details: {e.sqlite_errorcode if hasattr(e, 'sqlite_errorcode') else 'Unknown'}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during database initialization: {e}")
        logger.error(f"Error traceback: {traceback.format_exc()}")
        raise

# Initialize database
try:
    init_database()
except Exception as e:
    logger.critical(f"Failed to initialize database: {e}")
    logger.critical(f"Application cannot start without database: {traceback.format_exc()}")
    sys.exit(1)

# Error logging decorator
def log_errors(func):
    async def wrapper(*args, **kwargs):
        try:
            logger.debug(f"Calling {func.__name__} with args: {args}, kwargs: {kwargs}")
            result = await func(*args, **kwargs)
            logger.debug(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            logger.error(f"Error traceback: {traceback.format_exc()}")
            logger.error(f"Function arguments: args={args}, kwargs={kwargs}")
            raise
    return wrapper

current_api_key = None
tl_client = None
embedding_storage: Dict[str, Any] = {}
video_storage: Dict[str, bytes] = {}

# Track server start time
server_start_time = datetime.now(timezone.utc)
logger.info(f"Server started at {server_start_time}")
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"Python version: {sys.version}")
logger.info(f"Environment variables: CORS_ORIGINS={CORS_ORIGINS}")

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
@log_errors
async def health_check():
    """Health check endpoint that returns server status and basic info"""
    logger.debug("Health check requested")
    
    try:
        # Check database connection
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        db_status = "healthy"
        logger.debug("Database health check passed")
    except Exception as e:
        db_status = "error"
        logger.error(f"Database health check failed: {e}")
        logger.error(f"Database error traceback: {traceback.format_exc()}")
    
    # Calculate uptime
    uptime = datetime.now(timezone.utc) - server_start_time
    uptime_seconds = int(uptime.total_seconds())
    
    # Get system info
    import psutil
    try:
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')
        cpu_percent = psutil.cpu_percent(interval=1)
        
        system_status = {
            "memory_used_percent": memory_info.percent,
            "memory_available_gb": round(memory_info.available / (1024**3), 2),
            "disk_used_percent": disk_info.percent,
            "disk_free_gb": round(disk_info.free / (1024**3), 2),
            "cpu_percent": cpu_percent
        }
    except Exception as e:
        logger.warning(f"Could not get system info: {e}")
        system_status = {"error": str(e)}
    
    logger.info(f"Health check completed - DB: {db_status}, Uptime: {uptime_seconds}s")
    
    return {
        "status": "healthy",
        "version": "2.0.0",
        "uptime_seconds": uptime_seconds,
        "uptime": str(uptime),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database_status": db_status,
        "python_version": sys.version.split()[0],
        "system_status": system_status,
        "storage_info": {
            "embedding_storage_count": len(embedding_storage),
            "video_storage_count": len(video_storage),
            "embedding_storage_keys": list(embedding_storage.keys()),
            "video_storage_keys": list(video_storage.keys())
        }
    }

@app.get("/logs")
@log_errors
async def get_logs(limit: int = Query(default=100, le=1000)):
    """Get recent log entries for debugging"""
    try:
        log_file = "logs/sage_backend.log"
        if not os.path.exists(log_file):
            return {"error": "Log file not found", "logs": []}
        
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        # Get the last N lines
        recent_logs = lines[-limit:] if len(lines) > limit else lines
        
        return {
            "log_file": log_file,
            "total_lines": len(lines),
            "requested_lines": limit,
            "returned_lines": len(recent_logs),
            "logs": recent_logs
        }
    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        logger.error(f"Error traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to read logs: {str(e)}")

@app.get("/logs/error")
@log_errors
async def get_error_logs(limit: int = Query(default=50, le=500)):
    """Get recent error log entries"""
    try:
        log_file = "logs/sage_backend.log"
        if not os.path.exists(log_file):
            return {"error": "Log file not found", "error_logs": []}
        
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        # Filter for error lines
        error_lines = [line for line in lines if 'ERROR' in line or 'CRITICAL' in line]
        
        # Get the last N error lines
        recent_errors = error_lines[-limit:] if len(error_lines) > limit else error_lines
        
        return {
            "log_file": log_file,
            "total_lines": len(lines),
            "total_error_lines": len(error_lines),
            "requested_error_lines": limit,
            "returned_error_lines": len(recent_errors),
            "error_logs": recent_errors
        }
    except Exception as e:
        logger.error(f"Error reading error logs: {e}")
        logger.error(f"Error traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to read error logs: {str(e)}")

@app.get("/debug")
@log_errors
async def debug_info():
    """Get comprehensive debug information"""
    try:
        import psutil
        
        # System information
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu_count = psutil.cpu_count()
        
        # Process information
        process = psutil.Process()
        process_memory = process.memory_info()
        
        # Network information
        network_io = psutil.net_io_counters()
        
        # Environment information
        env_vars = {k: v for k, v in os.environ.items() if not k.lower().startswith(('password', 'secret', 'key', 'token'))}
        
        debug_info = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system": {
                "platform": sys.platform,
                "python_version": sys.version,
                "cpu_count": cpu_count,
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "memory_used_percent": memory.percent,
                "disk_total_gb": round(disk.total / (1024**3), 2),
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "disk_used_percent": disk.percent
            },
            "process": {
                "pid": process.pid,
                "memory_rss_mb": round(process_memory.rss / (1024**2), 2),
                "memory_vms_mb": round(process_memory.vms / (1024**2), 2),
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads(),
                "open_files": len(process.open_files()),
                "connections": len(process.connections())
            },
            "network": {
                "bytes_sent_mb": round(network_io.bytes_sent / (1024**2), 2),
                "bytes_recv_mb": round(network_io.bytes_recv / (1024**2), 2),
                "packets_sent": network_io.packets_sent,
                "packets_recv": network_io.packets_recv
            },
            "application": {
                "uptime_seconds": int((datetime.now(timezone.utc) - server_start_time).total_seconds()),
                "embedding_storage_count": len(embedding_storage),
                "video_storage_count": len(video_storage),
                "current_api_key": current_api_key[:8] + "..." if current_api_key else None,
                "twelvelabs_client_initialized": tl_client is not None
            },
            "environment": {
                "working_directory": os.getcwd(),
                "environment_variables": env_vars,
                "cors_origins": CORS_ORIGINS
            }
        }
        
        logger.info("Debug information requested and generated successfully")
        return debug_info
        
    except Exception as e:
        logger.error(f"Error generating debug info: {e}")
        logger.error(f"Error traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to generate debug info: {str(e)}")

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
@log_errors
async def validate_api_key(request: ApiKeyValidation):
    logger.info("Validating API key...")
    logger.debug(f"Received API key validation request for key: {request.key[:8]}...")
    
    try:
        # Test the API key with TwelveLabs
        logger.debug("Testing API key with TwelveLabs...")
        TwelveLabs(api_key=request.key)
        logger.info("API key validated successfully with TwelveLabs")
        
        # Save API key hash to database
        try:
            key_hash = hashlib.sha256(request.key.encode()).hexdigest()
            logger.debug(f"Generated key hash: {key_hash[:16]}...")
            
            conn = sqlite3.connect(DB_PATH)
            logger.debug("Database connection established")
            
            conn.execute('INSERT OR REPLACE INTO api_keys (key_hash, api_key) VALUES (?, ?)', 
                         (key_hash, None))
            conn.commit()
            logger.debug("API key hash saved to database")
            conn.close()
            logger.debug("Database connection closed")
            
        except sqlite3.Error as db_error:
            logger.error(f"Database error while saving API key: {db_error}")
            logger.error(f"SQLite error code: {db_error.sqlite_errorcode if hasattr(db_error, 'sqlite_errorcode') else 'Unknown'}")
            # Don't fail the request for database errors
        except Exception as db_error:
            logger.error(f"Unexpected error while saving API key: {db_error}")
            logger.error(f"Error traceback: {traceback.format_exc()}")
            # Don't fail the request for database errors
        
        logger.info("API key validation completed successfully")
        return ApiKeyResponse(key=request.key, isValid=True)
        
    except Exception as e:
        logger.error(f"API key validation failed: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error traceback: {traceback.format_exc()}")
        logger.error(f"Request details: key_length={len(request.key)}, key_prefix={request.key[:8]}...")
        return ApiKeyResponse(key=request.key, isValid=False)

@app.post("/upload-and-generate-embeddings")
@log_errors
async def upload_and_generate_embeddings(
    request: Request,
    tl: TwelveLabs = Depends(get_twelve_labs_client)
):
    logger.info("Starting video upload and embedding generation")
    logger.debug(f"Request content type: {request.headers.get('content-type', 'Unknown')}")
    
    tmp_file_path = None
    try:
        # Parse FormData manually
        logger.debug("Parsing FormData from request...")
        form_data = await request.form()
        
        # Extract file from FormData
        if 'file' not in form_data:
            logger.error("No 'file' field found in FormData")
            raise HTTPException(status_code=400, detail="No file field found in request")
        
        file_item = form_data['file']
        logger.debug(f"File item type: {type(file_item)}")
        
        # Handle both UploadFile and SpooledTemporaryFile
        if hasattr(file_item, 'filename'):
            filename = file_item.filename
            content = await file_item.read()
        else:
            # Handle case where file might be a string or other type
            logger.error(f"Unexpected file type: {type(file_item)}")
            raise HTTPException(status_code=400, detail=f"Invalid file type: {type(file_item)}")
        
        logger.debug(f"File details: filename={filename}, size={len(content)} bytes")
        
        # Create temporary file
        logger.debug("Creating temporary file...")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        logger.debug(f"Temporary file created: {tmp_file_path}")
        
        # Create embedding task
        logger.info(f"Creating embedding task for file: {filename}")
        logger.debug(f"Using model: Marengo-retrieval-2.7, clip_length: 2")
        
        task = tl.embed.task.create(
            model_name="Marengo-retrieval-2.7",
            video_file=tmp_file_path,
            video_clip_length=2,
            video_embedding_scopes=["clip", "video"]
        )
        logger.info(f"Embedding task created with ID: {task.id}")
        
        # Wait for task completion
        logger.info(f"Waiting for embedding task {task.id} to complete...")
        def on_task_update(task: EmbeddingsTask):
            logger.info(f"Task {task.id} status update: {task.status}")
        
        task.wait_for_done(sleep_interval=5, callback=on_task_update)
        logger.info(f"Task {task.id} completed, retrieving results...")
        
        # Retrieve completed task
        completed_task = tl.embed.task.retrieve(task.id)
        logger.debug(f"Task results retrieved, status: {completed_task.status}")
        
        # Clean up temporary file
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
            logger.debug(f"Temporary file cleaned up: {tmp_file_path}")
            tmp_file_path = None
        
        # Generate IDs
        embedding_id = f"embed_{task.id}"
        video_id = f"video_{task.id}"
        logger.debug(f"Generated IDs - embedding: {embedding_id}, video: {video_id}")
        
        # Calculate duration
        duration = 0
        if completed_task.video_embedding and completed_task.video_embedding.segments:
            duration = completed_task.video_embedding.segments[-1].end_offset_sec
            logger.debug(f"Calculated video duration: {duration} seconds")
        
        # Store in memory
        embedding_storage[embedding_id] = {
            "filename": filename,
            "embeddings": completed_task.video_embedding,
            "duration": duration
        }
        video_storage[video_id] = content
        logger.debug(f"Data stored in memory - embedding_storage keys: {list(embedding_storage.keys())}")
        logger.debug(f"video_storage keys: {list(video_storage.keys())}")
        
        logger.info(f"Video upload and embedding generation completed successfully")
        logger.info(f"File: {filename}, Duration: {duration}s, Embedding ID: {embedding_id}")
        
        return {
            "embeddings": completed_task.video_embedding,
            "filename": filename,
            "duration": duration,
            "embedding_id": embedding_id,
            "video_id": video_id
        }
        
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error traceback: {traceback.format_exc()}")
        logger.error(f"File details: filename={filename if 'filename' in locals() else 'Unknown'}, size={len(content) if 'content' in locals() else 'Unknown'}")
        
        # Clean up temporary file on error
        if tmp_file_path and os.path.exists(tmp_file_path):
            try:
                os.unlink(tmp_file_path)
                logger.debug(f"Cleaned up temporary file on error: {tmp_file_path}")
            except Exception as cleanup_error:
                logger.error(f"Failed to clean up temporary file: {cleanup_error}")
        
        raise HTTPException(status_code=500, detail=f"Failed to generate embeddings: {str(e)}")

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
    if video_id not in video_storage:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return Response(content=video_storage[video_id], media_type="video/mp4")

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