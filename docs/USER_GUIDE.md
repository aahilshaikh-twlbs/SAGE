# SAGE User Guide - Complete User Documentation

## 🎯 **Project Overview**

SAGE is a sophisticated video comparison application that leverages TwelveLabs AI embeddings to analyze and compare video content at the segment level. It provides real-time video processing, AI-powered similarity analysis, and an intuitive interface for identifying differences between video files.

## 🚀 **Quick Start**

### **Backend Setup**
```bash
cd SAGE/backend
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### **Frontend Setup**
```bash
cd SAGE/frontend
bun install  # or npm install
bun dev      # or npm run dev
```

### **Configuration**
1. **Get TwelveLabs API Key**: Sign up at [twelvelabs.io](https://twelvelabs.io/)
2. **Set Environment Variable**: `export TWELVELABS_API_KEY="your_key"`
3. **Start Backend**: Run `python app.py` in the backend directory
4. **Start Frontend**: Run `bun dev` in the frontend directory
5. **Configure API Key**: Enter your API key in the SAGE interface

## ⚠️ **CRITICAL: Large Video Handling**

**IMPORTANT**: For videos longer than 10 minutes, please read the [Large Video Handling Guide](LARGE_VIDEO_HANDLING.md) before use. These fixes are essential for reliable operation with longer videos.

- **Videos 1-10 minutes**: Work out of the box
- **Videos 10+ minutes**: Require the implemented fixes for proper operation
- **Videos 15+ minutes**: Critical fixes prevent silent failures and incorrect results
- **Maximum supported duration: 20 minutes** (TwelveLabs API limitation)

## 🎯 **Key Features**

### **Core Functionality**
- **AI-Powered Video Analysis** - Uses TwelveLabs Marengo-retrieval-2.7 model for semantic video understanding
- **Real-Time Video Processing** - Asynchronous embedding generation with progress tracking
- **Segment-Level Comparison** - Identifies differences at precise timestamps with configurable similarity thresholds
- **Synchronized Video Playback** - Side-by-side video comparison with timeline markers
- **Drag & Drop Interface** - Modern upload experience with video thumbnails

### **Advanced Analytics**
- **Cosine & Euclidean Distance Metrics** - Multiple similarity calculation methods
- **Configurable Thresholds** - Adjustable sensitivity for difference detection (0.01 - 0.5)
- **Visual Timeline** - Color-coded difference markers on synchronized video timeline
- **Difference Statistics** - Total segments, differing segments, and distance metrics
- **Real-Time Threshold Adjustment** - Instant comparison updates with new settings

### **User Experience**
- **Progress Tracking** - Real-time status updates during video processing
- **Error Handling** - Non-blocking error display with automatic recovery
- **Responsive Design** - Works across desktop and mobile devices
- **Accessibility** - Screen reader friendly components

## 📱 **Usage Guide**

### **1. Upload Videos**
- Navigate to the main page
- Upload up to 2 video files (MP4 recommended)
- Wait for AI processing to complete
- Monitor progress with real-time status updates

### **2. Start Comparison**
- Click "Start Comparison" when both videos are ready
- Navigate to the analysis page
- System will automatically load comparison data

### **3. Analyze Differences**
- Use synchronized video players for side-by-side comparison
- Adjust similarity threshold for different sensitivity levels
- Click on timeline markers to jump to specific differences
- View detailed difference statistics in the right panel

## 🎨 **UI Components**

### **Main Interface**
- **ApiKeyConfig**: API key input and validation
- **Video Upload**: Drag & drop interface with thumbnails
- **Video List**: Status tracking and management
- **Comparison Button**: Start analysis when ready

### **Analysis Interface**
- **Side-by-side video players** with synchronized controls
- **Visual timeline** with color-coded difference markers
- **Real-time threshold adjustment** for comparison sensitivity
- **Difference list** with clickable segments
- **Statistics panel** showing comparison metrics

### **Video Synchronization**
- Play/pause controls synchronized between both players
- Timeline scrubbing updates both videos simultaneously
- Current time display and progress tracking
- Difference markers overlay on timeline

## 🔧 **API Reference**

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

**Request:** Multipart form data with video file

**Response:**
```json
{
  "message": "Video uploaded successfully. Embedding generation in progress.",
  "filename": "video.mp4",
  "video_id": "video_uuid",
  "embedding_id": "embed_uuid",
  "status": "processing"
}
```

#### `POST /compare-local-videos`
Compares two videos using their embedding IDs.

**Request:**
```
GET /compare-local-videos?embedding_id1=id1&embedding_id2=id2&threshold=0.05&distance_metric=cosine
```

**Response:**
```json
{
  "filename1": "video1.mp4",
  "filename2": "video2.mp4",
  "differences": [
    {
      "start_sec": 10.0,
      "end_sec": 12.0,
      "distance": 0.85
    }
  ],
  "total_segments": 300,
  "differing_segments": 45,
  "threshold_used": 0.05
}
```

#### `GET /video-status/{video_id}`
Gets current processing status of a video.

**Response:**
```json
{
  "video_id": "video_uuid",
  "filename": "video.mp4",
  "status": "ready",
  "embedding_status": "completed",
  "duration": 120.5,
  "upload_timestamp": "2024-08-19T15:00:00"
}
```

#### `GET /serve-video/{video_id}`
Gets streaming URL for video playback.

**Response:**
```json
{
  "video_url": "https://s3.amazonaws.com/bucket/video.mp4"
}
```

#### `GET /health`
Server health check and system status.

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "uptime_seconds": 3600,
  "uptime": "1:00:00",
  "timestamp": "2024-08-19T15:00:00",
  "database_status": "connected",
  "python_version": "3.12.0"
}
```

## 🔑 **Configuration**

### **Environment Variables**

**Backend:**
```bash
S3_BUCKET_NAME=sage-video-bucket
S3_REGION=us-east-2
S3_PROFILE=dev
TWELVELABS_API_KEY=your_api_key
```

**Frontend:**
```bash
NEXT_PUBLIC_API_URL=https://your-backend-url.com
```

### **AWS Setup**
```bash
# Configure SSO
aws configure sso

# Test S3 access
aws s3 ls s3://your-bucket --profile dev
```

## 📊 **Upload Process**

### **Chunking Strategy**
- **Chunk Size**: 10MB (10,485,760 bytes)
- **Max File Size**: 5TB (10,000 chunks)
- **Memory Usage**: ~10MB per upload

### **Upload Flow**
1. **Frontend**: File selection & thumbnail generation
2. **Backend**: Content type validation & API key check
3. **S3**: Multipart upload with 10MB chunks
4. **TwelveLabs**: Embedding generation via presigned URL
5. **Storage**: In-memory metadata storage

## 🎯 **Video Comparison**

### **Algorithm**
- **Interval**: 2-second segments
- **Distance Metric**: Cosine distance (default) or Euclidean
- **Threshold**: User-configurable (0.01-0.5)
- **Output**: Differing segments with timestamps

### **Timeline Handling**
- **Duration**: Uses longer video's duration
- **Seeking**: Constrained to shorter video's duration
- **Synchronization**: Both videos play/pause together

## 🐛 **Troubleshooting**

### **Common Issues**

1. **API Key Validation Fails**
   - Verify TwelveLabs API key is valid
   - Check API key has sufficient quota
   - Ensure network connectivity

2. **Video Upload Fails**
   - Check file format (MP4 recommended)
   - Verify file size limits
   - Ensure backend is running

3. **Comparison Results Empty**
   - Adjust similarity threshold
   - Check video quality and duration
   - Verify embedding generation completed

4. **Large Video Issues (>10 minutes)**
   - **CRITICAL**: Read [Large Video Handling Guide](LARGE_VIDEO_HANDLING.md)
   - Check backend logs for embedding generation errors
   - Verify video format compatibility
   - Monitor processing time (can take 15-30 minutes for very long videos)

### **For Large Videos (10+ minutes)**
If you're experiencing issues with videos longer than 10 minutes:

1. **Check the logs** for detailed error messages
2. **Verify embedding generation** completed successfully
3. **Check segment count** vs expected count
4. **Review the [Large Video Handling Guide](LARGE_VIDEO_HANDLING.md)** for detailed troubleshooting

**Note**: The system now provides clear error messages instead of silent failures. If a large video fails, you'll get a specific error explaining what went wrong.

### **Debug Commands**

```bash
# Check backend logs
tail -f backend/app.log

# Test video upload
curl -X POST http://localhost:8000/upload-and-generate-embeddings \
  -F "file=@test_video.mp4"

# Check video status
curl "http://localhost:8000/video-status/{video_id}"
```

## 🚧 **Current Limitations**

- In-memory storage (videos lost on server restart)
- Single server deployment
- 2-video comparison limit
- Sequential video processing (one at a time)
- **Maximum video duration: 20 minutes** (TwelveLabs API limitation)

## 🔮 **Future Enhancements**

- Persistent storage with PostgreSQL
- User management and authentication
- Export features for comparison reports
- Batch processing for multiple videos
- S3 integration for scalable storage
- Redis caching for performance optimization
- Parallel video processing

## 📄 **License**

This project is licensed under the MIT License.

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

**SAGE** - Making AI-powered video comparison accessible and intuitive.
