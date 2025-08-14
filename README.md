# SAGE - Video Comparison with AI Embeddings

SAGE is a video comparison application that uses TwelveLabs AI embeddings to analyze and compare video content. Videos are uploaded to S3 storage and processed asynchronously for optimal performance.

## Features

- **S3 Integration**: Videos are uploaded directly to AWS S3 for scalable storage
- **Async Processing**: Embedding generation happens in the background without blocking the user
- **Real-time Status**: Polling system to track video processing progress
- **AI-powered Comparison**: Uses TwelveLabs Marengo-retrieval-2.7 model for video analysis
- **Modern UI**: Clean, responsive interface built with Next.js and Tailwind CSS

## Architecture

### Backend (FastAPI)
- **Upload Flow**: Videos uploaded to S3 → Embedding generation started asynchronously
- **Storage**: S3 for video files, in-memory for embeddings and metadata
- **API Endpoints**:
  - `POST /upload-and-generate-embeddings` - Upload video and start processing
  - `GET /video-status/{video_id}` - Check video processing status
  - `GET /embedding-status/{embedding_id}` - Check embedding generation status
  - `GET /serve-video/{video_id}` - Get presigned S3 URL for video playback
  - `POST /compare-local-videos` - Compare two processed videos

### Frontend (Next.js)
- **Async Workflow**: Upload → Processing → Ready for comparison
- **Status Polling**: Automatic checking of video processing status
- **Progress Tracking**: Real-time updates on video processing stages

## Setup

### Prerequisites
- Python 3.8+
- Node.js 18+
- AWS S3 bucket
- TwelveLabs API key

### Backend Setup
1. Navigate to `backend/` directory
2. Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   S3_BUCKET_NAME=tl-sage-bucket
   S3_REGION=us-east-1
   S3_ACCESS_KEY=your_aws_access_key
   S3_SECRET_KEY=your_aws_secret_key
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the backend:
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000
   ```

### Frontend Setup
1. Navigate to `frontend/` directory
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```

## Usage

1. **Configure API Key**: Enter your TwelveLabs API key in the frontend
2. **Upload Videos**: Upload two videos (MP4 format recommended)
3. **Start Processing**: Click "Upload & Start Processing" to begin
4. **Monitor Progress**: Watch real-time status updates
5. **Compare Videos**: Once processing is complete, videos are ready for comparison
6. **Analysis**: Navigate to the analysis page to compare video content

## Workflow

1. **Upload**: Video files are uploaded to S3 bucket
2. **Processing**: Embedding generation starts asynchronously using S3 URLs
3. **Status Updates**: Frontend polls backend for processing status
4. **Completion**: Once both videos are processed, comparison is enabled
5. **Analysis**: AI-powered comparison of video segments

## API Reference

### Upload Video
```http
POST /upload-and-generate-embeddings
Content-Type: multipart/form-data
X-API-Key: your_twelvelabs_api_key

Response:
{
  "message": "Video uploaded successfully. Embedding generation in progress.",
  "filename": "video.mp4",
  "video_id": "video_uuid",
  "embedding_id": "embed_uuid",
  "status": "processing"
}
```

### Check Video Status
```http
GET /video-status/{video_id}
X-API-Key: your_twelvelabs_api_key

Response:
{
  "video_id": "video_uuid",
  "filename": "video.mp4",
  "status": "ready",
  "embedding_status": "completed",
  "duration": 120.5,
  "upload_timestamp": "2024-01-01T12:00:00"
}
```

### Get Video URL
```http
GET /serve-video/{video_id}
X-API-Key: your_twelvelabs_api_key

Response:
{
  "video_url": "https://presigned-s3-url..."
}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `S3_BUCKET_NAME` | S3 bucket for video storage | `tl-sage-bucket` |
| `S3_REGION` | AWS region for S3 | `us-east-1` |
| `S3_ACCESS_KEY` | AWS access key ID | Required |
| `S3_SECRET_KEY` | AWS secret access key | Required |

## Security

- API keys are validated against TwelveLabs
- S3 presigned URLs expire after 1 hour
- CORS configured for specific origins
- Input validation and sanitization

## Troubleshooting

### Common Issues
1. **S3 Upload Failed**: Check AWS credentials and bucket permissions
2. **Embedding Generation Failed**: Verify TwelveLabs API key and quota
3. **Video Not Playing**: Check if presigned URL has expired

### Logs
Backend logs are available in the console and include:
- Request/response logging
- S3 operation status
- Embedding generation progress
- Error details with stack traces

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.