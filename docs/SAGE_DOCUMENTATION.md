# SAGE - Video Comparison with AI Embeddings

## 🎯 **Project Summary**

SAGE is a sophisticated video comparison application that leverages TwelveLabs AI embeddings to analyze and compare video content at the segment level. It provides real-time video processing, AI-powered similarity analysis, and an intuitive interface for identifying differences between video files.

## 🚀 **Key Features**

### **Core Functionality**
- **AI-Powered Video Analysis** - Uses TwelveLabs Marengo-retrieval-2.7 model for semantic video understanding
- **Real-Time Video Processing** - Asynchronous embedding generation with progress tracking
- **Segment-Level Comparison** - Identifies differences at precise timestamps with configurable similarity thresholds
- **Synchronized Video Playback** - Side-by-side video comparison with timeline markers
- **Drag & Drop Interface** - Modern upload experience with video thumbnails

### **Advanced Analytics**
- **Cosine & Euclidean Distance Metrics** - Multiple similarity calculation methods
- **Configurable Thresholds** - Adjustable sensitivity for difference detection
- **Visual Timeline** - Color-coded difference markers on synchronized video timeline
- **Difference Statistics** - Total segments, differing segments, and distance metrics
- **Real-Time Threshold Adjustment** - Instant comparison updates with new settings

### **User Experience**
- **Progress Tracking** - Real-time status updates during video processing
- **Error Handling** - Non-blocking error display with automatic recovery
- **Responsive Design** - Works across desktop and mobile devices
- **Dark/Light Theme** - TwelveLabs brand colors with theme support
- **Accessibility** - Screen reader friendly components

## 🏗️ **Architecture Overview**

### **System Architecture**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   External      │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (TwelveLabs)  │
│                 │    │                 │    │                 │
│ • Video Upload  │    │ • API Gateway   │    │ • AI Embeddings │
│ • UI/UX         │    │ • Processing    │    │ • Video Analysis│
│ • Comparison    │    │ • Storage       │    │ • ML Models     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Data Flow**
1. **API Key Setup** - User configures TwelveLabs API key
2. **Video Upload** - Files uploaded to backend for processing
3. **Embedding Generation** - TwelveLabs AI creates video embeddings
4. **Comparison Analysis** - Backend calculates segment similarities
5. **Visualization** - Frontend displays synchronized comparison results

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
├── Boto3 1.34.0 - AWS S3 integration (for future scaling)
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

## 📊 **API Reference**

### **Core Endpoints**

#### `POST /validate-key`
Validates TwelveLabs API key and stores hash securely.

**Request:**
```json
{
  "key": "your_twelvelabs_api_key"
}
```

**Response:**
```json
{
  "key": "your_twelvelabs_api_key",
  "isValid": true
}
```

#### `POST /upload-and-generate-embeddings`
Uploads video file and starts AI embedding generation.

**Request:** `multipart/form-data`
- `file`: Video file (MP4 recommended)

**Response:**
```json
{
  "embeddings": {...},
  "filename": "video.mp4",
  "duration": 120.5,
  "embedding_id": "embed_uuid",
  "video_id": "video_uuid"
}
```

#### `POST /compare-local-videos`
Compares two videos using their embedding IDs.

**Query Parameters:**
- `embedding_id1`: First video embedding ID
- `embedding_id2`: Second video embedding ID
- `threshold`: Similarity threshold (default: 0.1)
- `distance_metric`: "cosine" or "euclidean" (default: "cosine")

**Response:**
```json
{
  "filename1": "video1.mp4",
  "filename2": "video2.mp4",
  "differences": [
    {
      "start_sec": 10.5,
      "end_sec": 12.0,
      "distance": 0.85
    }
  ],
  "total_segments": 60,
  "differing_segments": 5,
  "threshold_used": 0.1
}
```

#### `GET /serve-video/{video_id}`
Streams video content from backend memory.

**Response:** `video/mp4` stream

### **Utility Endpoints**

#### `GET /health`
Server health check with detailed status information.

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "uptime_seconds": 3600,
  "uptime": "1:00:00",
  "timestamp": "2024-01-01T12:00:00Z",
  "database_status": "healthy",
  "python_version": "3.12.0"
}
```

#### `GET /`
API information endpoint for bots and scanners.

**Response:**
```json
{
  "message": "SAGE API",
  "docs": "/docs"
}
```

## 🎨 **User Interface**

### **Pages**

#### Landing Page (`/`)
- **API Key Configuration** - TwelveLabs API key input with validation
- **Video Upload Interface** - Drag & drop with thumbnail generation
- **Progress Tracking** - Real-time status updates during processing
- **Error Handling** - Non-blocking error display with recovery

#### Analysis Page (`/analysis`)
- **Synchronized Video Players** - Side-by-side video comparison
- **Visual Timeline** - Color-coded difference markers
- **Difference List** - Detailed segment-by-segment analysis
- **Threshold Controls** - Real-time similarity adjustment
- **Statistics Panel** - Comparison metrics and summary

### **Components**

#### ApiKeyConfig
- API key input with validation
- Secure storage in localStorage
- Error handling for invalid keys

#### Video Upload
- Drag & drop interface
- File type validation (video only)
- Thumbnail generation
- Progress indicators

#### Video Player
- Synchronized dual video playback
- Timeline scrubbing
- Difference marker overlay
- Playback controls

#### Settings Panel
- Threshold adjustment slider
- Distance metric selection
- Real-time comparison updates

## 🔒 **Security Features**

### **API Key Management**
- **SHA-256 Hashing** - API keys hashed before storage
- **Secure Storage** - Keys stored in SQLite database
- **Validation** - Real-time validation against TwelveLabs API
- **Session Persistence** - Keys cached in localStorage

### **CORS Protection**
```python
allow_origins=[
    "http://localhost:3000",
    "https://tl-sage.vercel.app"
]
```

### **Input Validation**
- **Pydantic Models** - Request/response validation
- **File Type Checking** - Video file validation
- **Size Limits** - Upload size restrictions
- **Sanitization** - Input data cleaning

### **Bot Traffic Management**
- **Root Endpoint** - Returns API info instead of 404
- **Robots.txt** - Disallows all crawlers
- **Favicon Handler** - Prevents log spam
- **Health Monitoring** - Request logging and analysis

## 📈 **Performance Optimizations**

### **Frontend Optimizations**
- **Client-Side Thumbnails** - Browser-generated video previews
- **Lazy Loading** - Components loaded on demand
- **Efficient State Management** - React hooks for minimal re-renders
- **Bundle Optimization** - Tree shaking and code splitting

### **Backend Optimizations**
- **Efficient Vector Operations** - NumPy-optimized similarity calculations
- **Memory Management** - Temporary file cleanup
- **Streaming Responses** - Direct video serving
- **Connection Pooling** - Database connection optimization

### **Network Optimizations**
- **API Proxy** - Next.js rewrites avoid CORS issues
- **Compression** - Gzip compression for responses
- **Caching** - Browser caching for static assets
- **CDN** - Vercel edge network for global performance

## 🔄 **Workflow**

### **1. Setup Phase**
```
User enters TwelveLabs API key
    ↓
Frontend validates with backend
    ↓
Key hash stored in SQLite
    ↓
Key persisted in localStorage
```

### **2. Upload Phase**
```
User selects 2 video files
    ↓
Videos uploaded to backend
    ↓
Backend creates TwelveLabs tasks
    ↓
Embeddings generated asynchronously
    ↓
Results stored in memory
```

### **3. Processing Phase**
```
TwelveLabs processes videos
    ↓
Backend polls for completion
    ↓
Frontend shows progress updates
    ↓
Embeddings stored with metadata
```

### **4. Analysis Phase**
```
Frontend requests comparison
    ↓
Backend calculates segment distances
    ↓
Results filtered by threshold
    ↓
Differences returned with timestamps
```

### **5. Visualization Phase**
```
Videos served from backend
    ↓
Synchronized playback controls
    ↓
Timeline shows difference segments
    ↓
Real-time threshold adjustment
```

## 🚧 **Current Limitations**

### **Technical Limitations**
- **In-Memory Storage** - Videos/embeddings lost on server restart
- **Single Server** - No horizontal scaling capability
- **2-Video Limit** - UI designed for pairwise comparison only
- **No Persistence** - Comparison results not saved between sessions

### **Feature Limitations**
- **No User Management** - Single API key for all users
- **No Batch Processing** - Limited to 2 videos at a time
- **No Export Features** - Results cannot be downloaded
- **No Collaboration** - No sharing of comparison results

### **Infrastructure Limitations**
- **No Load Balancing** - Single point of failure
- **No Database** - Limited data persistence
- **No Caching** - No Redis or CDN caching
- **No Monitoring** - Limited observability

## 🔮 **Future Enhancements**

### **Short Term (1-3 months)**
- **Persistent Storage** - PostgreSQL database for videos and results
- **User Management** - Multi-user support with authentication
- **Export Features** - PDF/CSV comparison reports
- **Batch Comparison** - Support for multiple video analysis

### **Medium Term (3-6 months)**
- **S3 Integration** - Scalable video storage
- **Redis Caching** - Embedding performance optimization
- **Advanced Analytics** - Aggregate statistics and trends
- **API Rate Limiting** - Protection against abuse

### **Long Term (6+ months)**
- **Microservices Architecture** - Scalable backend services
- **Machine Learning Pipeline** - Custom model training
- **Collaboration Features** - Share and comment on comparisons
- **Mobile Application** - Native iOS/Android apps

## 🎯 **Use Cases**

### **Content Verification**
- Compare video versions for differences
- Quality control in media production
- Version control for video content

### **Research & Analysis**
- Academic video comparison studies
- Forensic video analysis
- Content similarity research

### **Media Production**
- Before/after comparison of edits
- Quality assurance testing
- Content validation workflows

### **Security & Compliance**
- Video tampering detection
- Content authenticity verification
- Regulatory compliance checking

## 📋 **Installation & Setup**

### **Prerequisites**
- Python 3.12+
- Node.js 18+
- TwelveLabs API key
- Git

### **Backend Setup**
```bash
# Clone repository
git clone <repository-url>
cd SAGE/backend

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export TWELVELABS_API_KEY="your_api_key"

# Run backend
python app.py
```

### **Frontend Setup**
```bash
# Navigate to frontend
cd SAGE/frontend

# Install dependencies
bun install

# Set environment variables
export NEXT_PUBLIC_API_URL="http://localhost:8000"

# Run development server
bun run dev
```

### **Production Deployment**
```bash
# Backend (Digital Ocean)
sudo systemctl start sage-backend

# Frontend (Vercel)
vercel --prod
```

## 🐛 **Troubleshooting**

### **Common Issues**

#### API Key Validation Fails
- Verify TwelveLabs API key is valid
- Check API key has sufficient quota
- Ensure network connectivity to TwelveLabs

#### Video Upload Fails
- Check file format (MP4 recommended)
- Verify file size limits
- Ensure backend is running and accessible

#### Comparison Results Empty
- Adjust similarity threshold
- Check video quality and duration
- Verify embedding generation completed

#### Performance Issues
- Monitor server resources
- Check network connectivity
- Review API rate limits

### **Debug Information**
- Backend logs available in console
- Frontend errors in browser console
- Network requests in browser dev tools
- Health endpoint: `GET /health`

## 📄 **License**

This project is licensed under the MIT License. See LICENSE file for details.

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 **Support**

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review troubleshooting guide
- Contact the development team

---

**SAGE** - Making AI-powered video comparison accessible and intuitive.


using 1 remanent of @SAGE_old/  (the analysis tab content and layout; i want you to recreate SAGE based on the documents in @SAGE/ 