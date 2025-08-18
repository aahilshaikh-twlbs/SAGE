# SAGE Quick Reference Guide

## 🚀 Quick Start

### Backend
```bash
cd SAGE/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

### Frontend
```bash
cd SAGE/frontend
bun install
bun dev
```

## 📋 API Endpoints

### Authentication
- `POST /validate-key` - Validate TwelveLabs API key
- `GET /health` - Server health check

### Video Management
- `POST /upload-and-generate-embeddings` - Upload video & start embedding
- `GET /video-status/{video_id}` - Get video processing status
- `GET /serve-video/{video_id}` - Get video streaming URL

### Embedding Management
- `GET /embedding-status/{embedding_id}` - Get embedding status
- `POST /cancel-embedding-task` - Cancel active embedding task

### Analysis
- `POST /compare-local-videos` - Compare two videos

## 🔧 Configuration

### Environment Variables

**Backend**:
```bash
S3_BUCKET_NAME=sage-video-bucket
S3_REGION=us-east-2
S3_PROFILE=dev
```

**Frontend**:
```bash
NEXT_PUBLIC_API_URL=https://your-backend-url.com
```

### AWS Setup
```bash
# Configure SSO
aws configure sso

# Test S3 access
aws s3 ls s3://your-bucket --profile dev
```

## 📊 Upload Process

### Chunking Strategy
- **Chunk Size**: 10MB (10,485,760 bytes)
- **Max File Size**: 5TB (10,000 chunks)
- **Memory Usage**: ~10MB per upload

### Upload Flow
1. **Frontend**: File selection & thumbnail generation
2. **Backend**: Content type validation & API key check
3. **S3**: Multipart upload with 10MB chunks
4. **TwelveLabs**: Embedding generation via presigned URL
5. **Storage**: In-memory metadata storage

## 🎯 Video Comparison

### Algorithm
- **Interval**: 2-second segments
- **Distance Metric**: Cosine distance
- **Threshold**: User-configurable (0.01-0.5)
- **Output**: Differing segments with timestamps

### Timeline Handling
- **Duration**: Uses longer video's duration
- **Seeking**: Constrained to shorter video's duration
- **Synchronization**: Both videos play/pause together

## 🐛 Common Issues

### Backend Issues

**S3 Upload Failures**:
```bash
# Check permissions
aws s3 ls s3://your-bucket --profile your-profile

# Check CORS
aws s3api get-bucket-cors --bucket your-bucket
```

**TwelveLabs API Issues**:
```bash
# Test API key
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://api.twelvelabs.io/v1.3/tasks
```

**Memory Issues**:
```bash
# Check memory usage
ps aux | grep python
free -h
```

### Frontend Issues

**Build Failures**:
```bash
# Clear cache
rm -rf .next node_modules
bun install
bunx tsc --noEmit
```

**CORS Issues**:
```bash
# Check CORS headers
curl -H "Origin: https://your-frontend.com" \
     -X OPTIONS https://your-backend.com/upload-and-generate-embeddings
```

## 📈 Performance

### Backend Performance
- **Concurrent Uploads**: 10 limit
- **Memory per Upload**: ~10MB
- **Upload Speed**: ~2-3 min/GB
- **Response Time**: <100ms for status checks

### Frontend Performance
- **Status Polling**: 3-second intervals
- **Thumbnail Size**: ~100KB per video
- **Bundle Size**: ~2MB (gzipped)

## 🔒 Security

### Authentication
- **API Keys**: Stored in SQLite with SHA256 hashing
- **Validation**: TwelveLabs API key validation
- **Sessions**: Stateless (no user sessions)

### Data Protection
- **File Uploads**: Content type validation
- **S3 Access**: Presigned URLs with 1-hour expiration
- **CORS**: Configured for specific domains

## 📝 Logging

### Backend Logs
```bash
# View logs
tail -f app.log

# Search for errors
grep "ERROR" app.log

# Search for uploads
grep "UPLOAD" app.log
```

### Log Format
```
2025-08-18 08:58:00 PDT - __main__ - INFO - Starting streaming S3 upload for video.mp4
2025-08-18 08:58:01 PDT - __main__ - INFO - Uploading part 1 for video.mp4 (10485760 bytes)
```

## 🚀 Deployment

### Backend Deployment
```bash
# Docker
docker build -t sage-backend .
docker run -p 8000:8000 sage-backend

# Systemd
sudo systemctl enable sage-backend
sudo systemctl start sage-backend
```

### Frontend Deployment
```bash
# Vercel (automatic)
git push origin main

# Manual build
bun run build
```

## 🔄 Maintenance

### Daily Tasks
- Monitor error logs
- Check disk space
- Verify API key validity

### Weekly Tasks
- Review performance metrics
- Update dependencies
- Backup database

### Monthly Tasks
- Security updates
- Performance optimization
- Cost analysis

## 📚 Useful Commands

### Backend Commands
```bash
# Health check
curl http://localhost:8000/health

# Check database
sqlite3 sage.db ".tables"

# View active tasks
ps aux | grep python

# Monitor logs
tail -f app.log | grep -E "(ERROR|UPLOAD|EMBEDDING)"
```

### Frontend Commands
```bash
# Type check
bunx tsc --noEmit

# Build
bun run build

# Development
bun dev

# Install dependencies
bun install
```

### AWS Commands
```bash
# List S3 objects
aws s3 ls s3://your-bucket/videos/ --profile dev

# Check bucket CORS
aws s3api get-bucket-cors --bucket your-bucket

# Test multipart upload
aws s3 cp large-file.mp4 s3://your-bucket/test/ --profile dev
```

## 🆘 Emergency Procedures

### Backend Restart
```bash
# Stop service
sudo systemctl stop sage-backend

# Clear memory
sudo systemctl restart sage-backend

# Check health
curl http://localhost:8000/health
```

### Database Recovery
```bash
# Backup current database
cp sage.db sage.db.backup.$(date +%Y%m%d)

# Restore from backup
cp sage.db.backup.20250818 sage.db
```

### S3 Cleanup
```bash
# List all objects
aws s3 ls s3://your-bucket/videos/ --recursive

# Delete old objects
aws s3 rm s3://your-bucket/videos/ --recursive --exclude "*" --include "*.mp4"
```

## 📞 Support

### Log Locations
- **Backend**: `SAGE/backend/app.log`
- **Frontend**: Browser console / Vercel logs
- **System**: `/var/log/syslog` (Linux)

### Health Checks
- **Backend**: `GET /health`
- **Frontend**: Browser network tab
- **S3**: `aws s3 ls s3://your-bucket`

### Common Error Codes
- **400**: Bad request (invalid file type, missing API key)
- **401**: Unauthorized (invalid API key)
- **404**: Not found (video/embedding not found)
- **500**: Internal server error (S3/API issues)
