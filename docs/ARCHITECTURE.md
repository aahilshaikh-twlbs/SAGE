# SAGE Architecture Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Backend Architecture](#backend-architecture)
3. [Frontend Architecture](#frontend-architecture)
4. [Data Flow](#data-flow)
5. [API Endpoints](#api-endpoints)
6. [Deployment](#deployment)

---

## System Overview

SAGE (Streaming Analysis and Generation Engine) is a video comparison platform that uses AI-powered embeddings to detect differences between video files. The system consists of:

- **Backend**: FastAPI-based Python service with S3 storage and TwelveLabs AI integration
- **Frontend**: Next.js 14 React application with TypeScript and Bun package manager
- **Storage**: AWS S3 for video files, in-memory storage for embeddings, SQLite for API keys
- **AI Service**: TwelveLabs API for video embedding generation

### System Architecture Diagram
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   External      │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   Services      │
│                 │    │                 │    │                 │
│ - Video Upload  │    │ - File Upload   │    │ - AWS S3        │
│ - Comparison    │    │ - Embedding Gen │    │ - TwelveLabs    │
│ - Timeline      │    │ - Video Analysis│    │ - SQLite DB     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## Backend Architecture

### Technology Stack
- **Framework**: FastAPI 0.104.1
- **Server**: Uvicorn with ASGI
- **Language**: Python 3.12
- **Storage**: AWS S3, SQLite, In-Memory
- **AI Integration**: TwelveLabs API
- **Logging**: Custom PST timezone formatter
- **Dependencies**: See `requirements.txt`

### Core Modules

#### 1. **Main Application (`app.py`)**

**Entry Point**: `if __name__ == "__main__"`
```python
uvicorn.run(
    app, 
    host="0.0.0.0", 
    port=8000,
    timeout_keep_alive=300,      # 5 minutes keep-alive
    timeout_graceful_shutdown=300, # 5 minutes graceful shutdown
    limit_concurrency=10,        # Limit concurrent connections
    limit_max_requests=1000      # Restart worker after 1000 requests
)
```

**Configuration**:
- **CORS**: Configured for localhost:3000 and Vercel deployment
- **Logging**: PST timezone with custom formatter
- **Database**: SQLite for API key storage only
- **S3**: AWS profile-based authentication

#### 2. **Database Layer**

**SQLite Schema**:
```sql
CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_hash TEXT UNIQUE NOT NULL,
    api_key TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Functions**:
- `init_database()`: Creates/updates API keys table
- `get_stored_api_key()`: Retrieves latest API key from database

#### 3. **S3 Integration**

**Configuration**:
```python
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "tl-sage-bucket")
S3_REGION = os.getenv("S3_REGION", "us-east-2")
S3_PROFILE = os.getenv("S3_PROFILE", "dev")
```

**Core Functions**:

**`upload_to_s3_streaming(file: UploadFile) -> str`**
- **Purpose**: Uploads large video files using multipart upload
- **Chunking Strategy**: 10MB chunks (10,485,760 bytes)
- **Process**:
  1. Creates multipart upload session
  2. Reads file in 10MB chunks using `await file.read(chunk_size)`
  3. Uploads each chunk as a separate part
  4. Completes multipart upload with all parts
  5. Returns S3 URL: `s3://bucket/videos/uuid_filename.mp4`

**`get_s3_presigned_url(s3_url: str, expiration: int = 3600) -> str`**
- **Purpose**: Generates temporary HTTPS URLs for video access
- **Usage**: TwelveLabs API access and frontend video streaming
- **Expiration**: 1 hour by default

#### 4. **TwelveLabs Integration**

**Client Management**:
```python
def get_twelve_labs_client(api_key: str):
    global tl_client, current_api_key
    
    if tl_client and current_api_key == api_key:
        return tl_client  # Reuse existing client
    
    tl_client = TwelveLabs(api_key=api_key)
    current_api_key = api_key
    return tl_client
```

**Embedding Generation**:
- **Model**: `Marengo-retrieval-2.7`
- **Clip Length**: 2 seconds
- **Scopes**: `["clip", "video"]`
- **Task Management**: Async with cancellation support

#### 5. **In-Memory Storage**

**Data Structures**:
```python
embedding_storage: Dict[str, Any] = {}      # Embedding results
video_storage: Dict[str, Dict[str, Any]] = {} # Video metadata
active_tasks: Dict[str, Any] = {}           # Running embedding tasks
```

**Storage Schema**:
```python
# Video Storage
video_storage[video_id] = {
    "filename": str,
    "s3_url": str,
    "status": "uploaded" | "ready",
    "upload_timestamp": str,
    "embedding_id": str,
    "duration": float
}

# Embedding Storage
embedding_storage[embedding_id] = {
    "filename": str,
    "status": "pending" | "processing" | "completed" | "failed" | "cancelled",
    "video_id": str,
    "s3_url": str,
    "embeddings": TwelveLabsEmbedding,
    "duration": float,
    "task_id": str,
    "completed_at": str,
    "error": str
}
```

### Upload Process (Extreme Detail)

#### **Phase 1: File Upload Request**
```python
@app.post("/upload-and-generate-embeddings")
async def upload_and_generate_embeddings(file: UploadFile = File(...)):
```

**Validation**:
1. **Content Type**: Must start with `video/`
2. **File Size**: No limit (S3 supports unlimited)
3. **API Key**: Must be configured in database

#### **Phase 2: S3 Streaming Upload**

**Step 1: Initialize Multipart Upload**
```python
response = s3_client.create_multipart_upload(
    Bucket=S3_BUCKET_NAME,
    Key=file_key,  # f"videos/{uuid.uuid4()}_{file.filename}"
    ContentType=file.content_type,
    Metadata={
        'original_filename': file.filename,
        'upload_timestamp': datetime.now().isoformat()
    }
)
upload_id = response['UploadId']
```

**Step 2: Chunked Upload Process**
```python
chunk_size = 10 * 1024 * 1024  # 10MB chunks
parts = []
part_number = 1

while True:
    chunk = await file.read(chunk_size)  # Async file reading
    if not chunk:
        break
    
    # Upload individual chunk
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
```

**Step 3: Complete Multipart Upload**
```python
s3_client.complete_multipart_upload(
    Bucket=S3_BUCKET_NAME,
    Key=file_key,
    UploadId=upload_id,
    MultipartUpload={'Parts': parts}
)
```

**Error Handling**:
- **Abort on Error**: `s3_client.abort_multipart_upload()`
- **Cleanup**: Removes partial uploads
- **Logging**: Detailed progress for each chunk

#### **Phase 3: Embedding Generation**

**Step 1: Initialize Storage**
```python
video_id = f"video_{uuid.uuid4()}"
embedding_id = f"embed_{uuid.uuid4()}"

video_storage[video_id] = {
    "filename": file.filename,
    "s3_url": s3_url,
    "status": "uploaded",
    "upload_timestamp": datetime.now().isoformat(),
    "embedding_id": embedding_id
}

embedding_storage[embedding_id] = {
    "filename": file.filename,
    "status": "pending",
    "video_id": video_id,
    "s3_url": s3_url
}
```

**Step 2: Async Embedding Task**
```python
asyncio.create_task(generate_embeddings_async(embedding_id, s3_url, api_key))
```

**Step 3: TwelveLabs Processing**
```python
async def generate_embeddings_async(embedding_id: str, s3_url: str, api_key: str):
    # Get presigned URL for TwelveLabs
    presigned_url = get_s3_presigned_url(s3_url)
    
    # Create embedding task
    task = tl.embed.task.create(
        model_name="Marengo-retrieval-2.7",
        video_url=presigned_url,
        video_clip_length=2,
        video_embedding_scopes=["clip", "video"]
    )
    
    # Store for cancellation
    active_tasks[embedding_id] = task
    
    # Wait for completion
    task.wait_for_done(sleep_interval=5, callback=on_task_update)
    
    # Update storage
    embedding_storage[embedding_id].update({
        "status": "completed",
        "embeddings": completed_task.video_embedding,
        "duration": duration,
        "task_id": task.id,
        "completed_at": datetime.now().isoformat()
    })
```

### Video Comparison Algorithm

#### **Time-Based Comparison**
```python
# Compare segments at regular intervals
interval = 2.0  # 2-second intervals
total_intervals = int(max_duration / interval) + 1

for i in range(total_intervals):
    time_sec = i * interval
    
    seg1 = get_segment_at_time(segments1, time_sec)
    seg2 = get_segment_at_time(segments2, time_sec)
    
    if seg1 and seg2:
        # Calculate cosine distance
        v1 = np.array(seg1["embedding"], dtype=np.float32)
        v2 = np.array(seg2["embedding"], dtype=np.float32)
        
        dot = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        dist = 1.0 - (dot / (norm1 * norm2))
        
        if dist > threshold:
            differing_segments.append(DifferenceSegment(
                start_sec=time_sec,
                end_sec=min(time_sec + interval, max_duration),
                distance=float(dist)
            ))
```

#### **Similarity Calculation**
```python
if matched_segments > 0:
    avg_distance = np.mean(all_distances)
    similarity_percent = max(0, 100 - (avg_distance * 100))
```

### API Endpoints

#### **Authentication**
- `POST /validate-key`: Validate and store TwelveLabs API key
- `GET /health`: Server health check with uptime and status

#### **Video Management**
- `POST /upload-and-generate-embeddings`: Upload video and start embedding generation
- `GET /video-status/{video_id}`: Get video processing status
- `GET /serve-video/{video_id}`: Get video streaming URL

#### **Embedding Management**
- `GET /embedding-status/{embedding_id}`: Get embedding generation status
- `POST /cancel-embedding-task`: Cancel active embedding task

#### **Analysis**
- `POST /compare-local-videos`: Compare two videos using embedding IDs

---

## Frontend Architecture

### Technology Stack
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Package Manager**: Bun
- **UI Library**: React with custom components
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **State Management**: React hooks (useState, useEffect)
- **Routing**: Next.js App Router

### Project Structure
```
frontend/
├── src/
│   ├── app/
│   │   ├── page.tsx              # Main upload page
│   │   ├── analysis/page.tsx     # Video comparison page
│   │   └── layout.tsx            # Root layout
│   ├── components/
│   │   ├── ui/                   # Reusable UI components
│   │   └── ApiKeyConfig.tsx      # API key configuration
│   └── lib/
│       └── api.ts                # API client
├── package.json
├── bun.lockb                     # Bun lock file
└── tailwind.config.js
```

### Core Components

#### 1. **Main Upload Page (`page.tsx`)**

**State Management**:
```typescript
interface LocalVideo {
  id: string;
  file: File;
  thumbnail: string;
  video_id?: string;
  embedding_id?: string;
  status: 'uploading' | 'processing' | 'ready' | 'error' | 'cancelled';
  error?: string;
  duration?: number;
  progress?: string;
}

const [uploadedVideos, setUploadedVideos] = useState<LocalVideo[]>([]);
const [error, setError] = useState<string | null>(null);
```

**Key Functions**:

**`handleVideoUpload`**:
1. **File Validation**: Checks content type and file size
2. **Thumbnail Generation**: Creates video thumbnail using Canvas API
3. **Upload Request**: Calls backend upload endpoint
4. **Status Tracking**: Updates video status throughout process

**`pollStatus`**:
- **Interval**: 3 seconds
- **Purpose**: Monitor video processing status
- **Updates**: Status, progress, duration, error messages

**`cancelVideo`**:
- **Task Cancellation**: Calls backend cancel endpoint
- **Status Update**: Sets status to 'cancelled'
- **Cleanup**: Removes from active tasks

#### 2. **Analysis Page (`analysis/page.tsx`)**

**Video Player Management**:
```typescript
const video1Ref = useRef<HTMLVideoElement>(null);
const video2Ref = useRef<HTMLVideoElement>(null);

// Synchronized playback
const handlePlayPause = () => {
  if (video1Ref.current && video2Ref.current) {
    if (isPlaying) {
      video1Ref.current.pause();
      video2Ref.current.pause();
    } else {
      video1Ref.current.play();
      video2Ref.current.play();
    }
    setIsPlaying(!isPlaying);
  }
};
```

**Timeline Implementation**:
```typescript
// Use longer video's duration for timeline
const maxDuration = Math.max(video1Data.duration, video2Data.duration);

// Constrain seeking to shorter video's duration
const seekToTime = (time: number) => {
  const constrainedTime = Math.min(time, Math.min(video1Data.duration, video2Data.duration));
  video1Ref.current.currentTime = constrainedTime;
  video2Ref.current.currentTime = constrainedTime;
  setCurrentTime(constrainedTime);
};
```

**Difference Visualization**:
```typescript
{differences.map((diff, index) => {
  const startPercent = (diff.start_sec / maxDuration) * 100;
  const widthPercent = ((diff.end_sec - diff.start_sec) / maxDuration) * 100;
  
  return (
    <div
      className={`absolute h-full ${getSeverityColor(diff.distance)}`}
      style={{ 
        left: `${startPercent}%`,
        width: `${Math.max(1, widthPercent)}%`
      }}
      onClick={() => seekToTime(diff.start_sec)}
    />
  );
})}
```

#### 3. **API Client (`lib/api.ts`)**

**TypeScript Interfaces**:
```typescript
interface VideoUploadResponse {
  message: string;
  filename: string;
  video_id: string;
  embedding_id: string;
  status: string;
}

interface ComparisonResponse {
  filename1: string;
  filename2: string;
  differences: DifferenceSegment[];
  total_segments: number;
  differing_segments: number;
  threshold_used: number;
}
```

**API Methods**:
```typescript
export const api = {
  validateApiKey: async (key: string): Promise<ApiKeyResponse>,
  uploadVideo: async (file: File): Promise<VideoUploadResponse>,
  getVideoStatus: async (videoId: string): Promise<VideoStatusResponse>,
  getVideoUrl: async (videoId: string): Promise<{ video_url: string }>,
  compareVideos: async (embeddingId1: string, embeddingId2: string, threshold: number, distanceMetric: string): Promise<ComparisonResponse>,
  cancelEmbeddingTask: async (embeddingId: string): Promise<{ message: string }>
};
```

### State Management

#### **Local Storage**
- **API Key**: `localStorage.setItem('sage_api_key', key)`
- **Session Storage**: Video data for analysis page

#### **Session Storage**
```typescript
// Store video data for analysis
sessionStorage.setItem(`video${index + 1}_data`, JSON.stringify({
  id: video.id,
  filename: video.file.name,
  embedding_id: video.embedding_id,
  video_id: video.video_id,
  duration: video.duration || 60
}));
```

### UI/UX Features

#### **Real-Time Status Updates**
- **Polling**: 3-second intervals for status updates
- **Progress Indicators**: Loading spinners and progress text
- **Error Handling**: User-friendly error messages
- **Cancellation**: Stop button for active tasks

#### **Video Timeline**
- **Synchronized Playback**: Both videos play/pause together
- **Interactive Scrubbing**: Click timeline to seek
- **Difference Markers**: Color-coded segments showing differences
- **Time Display**: Current time / total duration

#### **Threshold Settings**
- **Modal Interface**: Adjustable comparison sensitivity
- **Real-Time Updates**: Immediate re-comparison on threshold change
- **Range Slider**: 0.01 to 0.5 threshold values

### Package Management with Bun

#### **Installation**
```bash
# Install Bun
curl -fsSL https://bun.sh/install | bash

# Install dependencies
bun install

# Run development server
bun dev

# Build for production
bun run build
```

#### **Key Dependencies**
```json
{
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "lucide-react": "^0.294.0",
    "tailwindcss": "^3.3.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/react": "^18.0.0",
    "typescript": "^5.0.0"
  }
}
```

---

## Data Flow

### 1. **Video Upload Flow**
```
Frontend → Backend → S3 → TwelveLabs → Backend → Frontend
    ↓         ↓       ↓       ↓         ↓         ↓
  File    Validate  Upload  Generate  Store    Update
  Select   File     Chunks  Embedding Results  Status
```

### 2. **Comparison Flow**
```
Frontend → Backend → Memory → Backend → Frontend
    ↓         ↓        ↓        ↓         ↓
  Select   Retrieve  Compare  Calculate  Display
  Videos   Embeddings Vectors  Differences Results
```

### 3. **Status Polling Flow**
```
Frontend → Backend → Frontend
    ↓         ↓         ↓
  Poll     Check     Update
  Status   Storage   UI
```

---

## Deployment

### Backend Deployment
- **Platform**: Any Python-compatible hosting
- **Environment Variables**:
  - `S3_BUCKET_NAME`: AWS S3 bucket name
  - `S3_REGION`: AWS region
  - `S3_PROFILE`: AWS profile name
- **Requirements**: Python 3.12+, AWS credentials

### Frontend Deployment
- **Platform**: Vercel (recommended)
- **Build Command**: `bun run build`
- **Output Directory**: `.next`
- **Environment Variables**: Backend API URL

### AWS Configuration
- **S3 Bucket**: Configured for multipart uploads
- **CORS**: Configured for frontend domain
- **IAM**: User with S3 read/write permissions
- **SSO**: AWS SSO profile for authentication

---

## Performance Considerations

### Backend
- **Memory Management**: In-memory storage only (no persistence)
- **Concurrency**: 10 concurrent connections limit
- **Chunking**: 10MB chunks for large file uploads
- **Task Management**: Active task tracking for cancellation

### Frontend
- **Thumbnail Generation**: Client-side using Canvas API
- **Status Polling**: 3-second intervals for responsiveness
- **Video Streaming**: Presigned URLs for direct S3 access
- **Memory**: Session storage for temporary data

### Scalability
- **Horizontal Scaling**: Stateless backend design
- **Load Balancing**: Multiple backend instances
- **CDN**: S3 for video file distribution
- **Caching**: Browser caching for static assets

---

## Security Considerations

### Authentication
- **API Keys**: Stored in SQLite with SHA256 hashing
- **Validation**: TwelveLabs API key validation
- **Session Management**: No user sessions (stateless)

### Data Protection
- **File Uploads**: Content type validation
- **S3 Access**: Presigned URLs with expiration
- **Database**: SQLite with API key encryption
- **CORS**: Configured for specific domains

### Network Security
- **HTTPS**: All communications over HTTPS
- **CORS**: Proper cross-origin configuration
- **Rate Limiting**: Uvicorn connection limits
- **Input Validation**: Pydantic model validation
