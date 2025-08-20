# SAGE Developer Guide - Technical Implementation

## 🎯 **System Overview**

SAGE (Streaming Analysis and Generation Engine) is a video comparison platform that uses AI-powered embeddings to detect differences between video files. The system consists of:

- **Backend**: FastAPI-based Python service with S3 storage and TwelveLabs AI integration
- **Frontend**: Next.js 15 React application with TypeScript and Bun package manager
- **Storage**: AWS S3 for video files, in-memory storage for embeddings, SQLite for API keys
- **AI Service**: TwelveLabs API for video embedding generation

## 🏗️ **System Architecture**

### **High-Level Architecture**
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

### **Data Flow Architecture**

#### **Phase 1: Initialization**
1. User provides AI service API credentials
2. System validates credentials against external AI service
3. Credentials are cryptographically hashed and stored
4. User session is established with credential caching

#### **Phase 2: Video Processing**
1. User selects video files through web interface
2. Files are uploaded to backend server via HTTP multipart requests
3. Backend creates processing tasks with AI service
4. AI service processes videos asynchronously:
   - Extracts video segments at regular time intervals
   - Generates embedding vectors for each segment
   - Returns structured data with timestamps and vectors
5. Backend stores processed data in memory for comparison operations

#### **Phase 3: Comparison Analysis**
1. User initiates comparison between two processed videos
2. System retrieves embedding vectors for both videos
3. For each time segment, system calculates similarity metrics:
   - Cosine distance between corresponding segment vectors
   - Euclidean distance as alternative metric
   - Threshold-based filtering of differences
4. Results are structured with timestamps, distance values, and metadata

#### **Phase 4: Visualization**
1. Comparison results are transmitted to frontend
2. Frontend renders synchronized video players
3. Timeline overlay displays difference markers
4. User can adjust similarity thresholds for real-time filtering
5. Video playback controls are synchronized between both players

## 💻 **Technology Stack**

### **Backend (FastAPI)**
```
Python 3.12+
├── FastAPI 0.104.1 - Modern web framework with automatic API docs
├── Uvicorn 0.24.0 - High-performance ASGI server
├── TwelveLabs SDK 0.0.1 - AI video embeddings and analysis
├── NumPy 1.24.3 - Efficient vector operations for similarity calculations
├── SQLite - Lightweight database for API key storage
├── Python-multipart 0.0.6 - File upload handling
├── Pydantic 2.5.0 - Data validation and serialization
├── Boto3 1.34.0 - AWS S3 integration
├── Psutil 5.9.6 - System monitoring and health checks
└── Python-dotenv 1.0.0 - Environment variable management
```

### **Frontend (Next.js)**
```
Next.js 15.4.5 (App Router)
├── React 19.1.0 - Modern UI framework with hooks
├── TypeScript 5 - Type-safe development
├── Tailwind CSS 3 - Utility-first CSS framework
├── Lucide React 0.534.0 - Beautiful icon library
├── Bun - Fast JavaScript runtime and package manager
├── Clsx 2.1.1 - Conditional className utility
├── Tailwind-merge 3.3.1 - Tailwind class merging
└── Class-variance-authority 0.7.1 - Component variant system
```

### **Infrastructure**
- **Backend Hosting**: Digital Ocean droplet (Ubuntu)
- **Frontend Hosting**: Vercel deployment with automatic CI/CD
- **Storage**: In-memory for videos/embeddings, SQLite for API keys
- **API Proxy**: Next.js rewrites to avoid CORS issues
- **Domain**: Custom domain with SSL certificates
- **Video Limits**: Maximum 20 minutes per video (TwelveLabs API limitation)

## 🔧 **Core Technical Concepts**

### **Video Processing Pipeline**

#### **Segment-Based Analysis**
- **Concept**: Videos are divided into fixed-duration segments (typically 2-second intervals)
- **Purpose**: Enables granular comparison at specific time points
- **Implementation**: Each segment becomes a discrete unit for AI analysis and comparison

#### **Embedding Vector Generation**
- **Concept**: AI service converts visual content into high-dimensional numerical vectors
- **Purpose**: Enables mathematical comparison of video content
- **Characteristics**: 
  - Vectors represent semantic meaning, not just pixel data
  - Similar content produces similar vectors regardless of exact pixel values
  - Vectors are normalized for consistent comparison

#### **Asynchronous Processing**
- **Concept**: AI processing happens in background while user interface remains responsive
- **Purpose**: Handles long-running AI tasks without blocking user interaction
- **Implementation**: Task queuing, status polling, and progress reporting

### **Similarity Calculation**

#### **Distance Metrics**
- **Cosine Distance**: Measures angle between vectors (0 = identical, 1 = completely different)
- **Euclidean Distance**: Measures straight-line distance between vectors
- **Normalization**: Vectors are normalized to unit length for consistent comparison

#### **Threshold-Based Filtering**
- **Configurable Sensitivity**: User can adjust threshold from 0.01 (very sensitive) to 0.5 (less sensitive)
- **Real-Time Updates**: Threshold changes immediately update comparison results
- **Segment Classification**: Segments below threshold are marked as "different"

## 🏗️ **Backend Architecture**

### **Core Modules**

#### **1. Main Application (`app.py`)**

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

#### **2. Database Layer**

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

#### **3. S3 Integration**

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
  1. Create multipart upload
  2. Read file in 10MB chunks
  3. Upload each chunk individually
  4. Complete multipart upload
  5. Return S3 URL

**Chunking Benefits**:
- **Memory Efficiency**: Only 10MB in memory at any time
- **Reliability**: Failed chunks can be retried individually
- **Progress Tracking**: Can monitor upload progress per chunk
- **Large File Support**: Handles files up to 5TB

#### **4. Embedding Generation**

**TwelveLabs Integration**:
```python
async def generate_embeddings_async(embedding_id: str, s3_url: str, api_key: str):
    # Get TwelveLabs client
    tl = get_twelve_labs_client(api_key)
    
    # Generate presigned URL for TwelveLabs access
    presigned_url = get_s3_presigned_url(s3_url)
    
    # Create embedding task
    task = tl.embed.task.create(
        model_name="Marengo-retrieval-2.7",
        video_url=presigned_url,
        video_clip_length=2,
        video_embedding_scopes=["clip", "video"]
    )
    
    # Wait for completion with timeout
    task.wait_for_done(sleep_interval=5, callback=on_task_update, timeout=1800)
```

**Model Configuration**:
- **Model**: Marengo-retrieval-2.7 (optimized for video retrieval)
- **Segment Length**: 2 seconds (configurable)
- **Scopes**: Both clip-level and video-level embeddings
- **Timeout**: 30 minutes for very long videos

#### **5. Video Comparison Engine**

**Comparison Algorithm**:
```python
def compare_videos(segments1, segments2, threshold, distance_metric="cosine"):
    differences = []
    
    for i, seg1 in enumerate(segments1):
        if i < len(segments2):
            seg2 = segments2[i]
            
            # Calculate distance based on metric
            if distance_metric == "cosine":
                distance = cosine_distance(seg1.embedding, seg2.embedding)
            else:
                distance = euclidean_distance(seg1.embedding, seg2.embedding)
            
            # Check if difference exceeds threshold
            if distance > threshold:
                differences.append({
                    "start_sec": seg1.start_offset_sec,
                    "end_sec": seg1.end_offset_sec,
                    "distance": distance
                })
    
    return differences
```

**Distance Calculations**:
- **Cosine Distance**: `1 - (dot_product / (norm1 * norm2))`
- **Euclidean Distance**: `sqrt(sum((v1 - v2)²))`
- **Normalization**: Vectors normalized to unit length

## 🎨 **Frontend Architecture**

### **Component Structure**

#### **1. Main Page (`page.tsx`)**
- **Video Upload**: Drag & drop interface with thumbnail generation
- **Status Management**: Real-time progress tracking and status updates
- **Queue Management**: Sequential processing for multiple videos
- **Error Handling**: Non-blocking error display with recovery options

#### **2. Analysis Page (`analysis/page.tsx`)**
- **Video Players**: Synchronized side-by-side playback
- **Timeline Component**: Interactive timeline with difference markers
- **Threshold Controls**: Real-time sensitivity adjustment
- **Statistics Panel**: Comparison metrics and segment information

#### **3. API Client (`lib/api.ts`)**
- **Request Management**: Centralized API communication
- **Error Handling**: Consistent error handling across all endpoints
- **Type Safety**: TypeScript interfaces for all API responses
- **CORS Handling**: Automatic CORS configuration

### **State Management**

#### **Video Processing State**
```typescript
interface LocalVideo {
  id: string;
  file: File;
  thumbnail: string;
  video_id?: string;
  embedding_id?: string;
  status: 'uploading' | 'processing' | 'ready' | 'error' | 'cancelled' | 'uploaded' | 'queued';
  error?: string;
  duration?: number;
  progress?: string;
}
```

#### **Comparison State**
```typescript
interface ComparisonState {
  differences: Difference[];
  totalSegments: number;
  threshold: number;
  isPlaying: boolean;
  currentTime: number;
  error: string | null;
}
```

### **Video Synchronization**

#### **Player Coordination**
- **Shared State**: Both players share play/pause state
- **Time Synchronization**: Scrubbing updates both players simultaneously
- **Duration Handling**: Timeline uses longer video's duration
- **Seeking Constraints**: Seeking limited to shorter video's duration

#### **Timeline Integration**
- **Difference Markers**: Color-coded markers for different segments
- **Interactive Seeking**: Click markers to jump to specific times
- **Real-Time Updates**: Threshold changes update markers immediately
- **Visual Feedback**: Clear indication of current playback position

## 🔒 **Security & Performance**

### **Security Features**

#### **API Key Management**
- **Cryptographic Hashing**: API keys stored as SHA-256 hashes
- **Secure Storage**: SQLite database with proper access controls
- **Validation**: Keys validated against TwelveLabs API before use
- **Session Management**: Keys cached in memory during session

#### **File Upload Security**
- **Content Type Validation**: Only video files accepted
- **Size Limits**: Configurable maximum file sizes
- **S3 Security**: Presigned URLs with expiration for TwelveLabs access
- **Input Sanitization**: All user inputs validated and sanitized

### **Performance Optimizations**

#### **Memory Management**
- **Streaming Uploads**: 10MB chunks prevent memory exhaustion
- **In-Memory Storage**: Fast access to embeddings and metadata
- **Garbage Collection**: Automatic cleanup of completed tasks
- **Resource Limits**: Configurable timeouts and memory limits

#### **Processing Efficiency**
- **Asynchronous Operations**: Non-blocking AI processing
- **Queue Management**: Sequential processing prevents resource conflicts
- **Progress Tracking**: Real-time updates without blocking
- **Error Recovery**: Graceful handling of failures

## 🚀 **Deployment & Scaling**

### **Current Deployment**

#### **Backend**
- **Hosting**: Digital Ocean droplet (Ubuntu 22.04)
- **Process Management**: Systemd service with auto-restart
- **Logging**: Structured logging with rotation
- **Monitoring**: Health checks and uptime monitoring

#### **Frontend**
- **Hosting**: Vercel with automatic CI/CD
- **Build Process**: Bun-based build optimization
- **Performance**: Next.js optimization and caching
- **Domain**: Custom domain with SSL

### **Scaling Considerations**

#### **Horizontal Scaling**
- **Load Balancing**: Multiple backend instances behind load balancer
- **Session Management**: Redis for shared session state
- **Database Scaling**: PostgreSQL for persistent storage
- **File Storage**: S3 for scalable video storage

#### **Performance Monitoring**
- **Metrics Collection**: Success/failure rates, processing times
- **Resource Monitoring**: CPU, memory, and network usage
- **Error Tracking**: Comprehensive error logging and alerting
- **User Analytics**: Usage patterns and performance metrics
- **Video Duration Limits**: Monitor for videos approaching 20-minute limit

## 🔧 **Development & Testing**

### **Development Setup**

#### **Backend Development**
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run development server
python app.py

# Run tests
python -m pytest tests/
```

#### **Frontend Development**
```bash
# Install dependencies
bun install

# Run development server
bun dev

# Build for production
bun run build

# Run linting
bun run lint
```

### **Testing Strategy**

#### **Backend Testing**
- **Unit Tests**: Individual function testing
- **Integration Tests**: API endpoint testing
- **Performance Tests**: Large file handling
- **Error Handling**: Failure scenario testing

#### **Frontend Testing**
- **Component Tests**: Individual component testing
- **Integration Tests**: Page-level functionality
- **User Experience**: End-to-end workflow testing
- **Performance**: Bundle size and loading optimization

## 📚 **Additional Resources**

### **Documentation**
- [User Guide](USER_GUIDE.md) - Complete user documentation
- [Large Video Handling](LARGE_VIDEO_HANDLING.md) - Critical fixes for large videos
- [Upload Process](UPLOAD_PROCESS.md) - Detailed upload implementation
- [API Reference](USER_GUIDE.md#-api-reference) - Complete API documentation

### **External Resources**
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [TwelveLabs API](https://docs.twelvelabs.io/)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)

---

**SAGE Developer Guide** - Technical implementation details for developers and contributors.
