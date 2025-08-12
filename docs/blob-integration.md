# Vercel Blob Integration Guide

## Overview

This document describes the integration of Vercel Blob storage for handling large video uploads in the SAGE application. The system now uses Vercel Blob for direct client-side uploads, bypassing Vercel Function size limits.

## Recent Updates (December 2024)

### Logging Improvements
- **PST Timestamps**: All backend logs now use Pacific Standard Time for consistency
- **Detailed Progress Tracking**: Enhanced logging throughout the upload and processing pipeline
- **TwelveLabs Cache Detection**: Added checks to detect if TwelveLabs caches embeddings
- **Error Diagnostics**: Improved error reporting with detailed failure reasons

## Architecture Changes

### Previous Architecture
- Frontend sent video files directly to backend through Vercel Functions
- Hit 4.5MB payload limit on Vercel Functions
- Attempted custom chunking solution (removed due to complexity)

### Current Architecture
1. **Client-side Upload**: Browser uploads video directly to Vercel Blob
2. **Blob URL Generation**: Vercel Blob returns a public URL
3. **Backend Processing**: Frontend sends blob URL to backend
4. **Video Processing**: Backend downloads from blob URL and processes with TwelveLabs

## Implementation Details

### Frontend Changes

#### 1. API Client (`frontend/src/lib/api.ts`)
```typescript
// Uses @vercel/blob/client for direct uploads
const { url } = await upload(`videos/${file.name}`, file, {
  access: 'public',
  addRandomSuffix: true,
  multipart: true,
  handleUploadUrl: `${API_BASE_URL}/blob/upload`,
});

// Sends blob URL to backend
const ingest = await fetch(`${API_BASE_URL}/ingest-blob`, {
  method: 'POST',
  body: JSON.stringify({ blob_url: url, filename: file.name }),
});
```

#### 2. API Routes (`frontend/src/app/api/[...path]/route.ts`)
- Catch-all route handles both proxy requests and blob token generation
- Special handling for `/blob/upload` endpoint
- Proxies other requests to backend with proper headers

### Backend Changes

#### 1. New Ingest Endpoint (`backend/app.py`)
```python
@app.post("/ingest-blob")
async def ingest_blob(request: BlobIngestRequest, tl: TwelveLabs = Depends(get_twelve_labs_client)):
    # Downloads video from blob URL
    # Processes with ffprobe/ffmpeg if needed
    # Generates embeddings via TwelveLabs
    # Returns results
```

#### 2. Removed Endpoints
- Removed: `/upload-chunk`, `/upload/start`, `/upload/chunk`, `/upload/finalize`
- Removed: Custom chunking logic and temporary file management

## Environment Variables

### Required for Vercel Deployment
```bash
BLOB_READ_WRITE_TOKEN=vercel_blob_rw_[your-token]  # From Vercel Blob store
BACKEND_URL=http://209.38.142.207:8000             # Backend server URL
```

### Local Development
Create `frontend/.env.local`:
```bash
BLOB_READ_WRITE_TOKEN=vercel_blob_rw_[your-token]
BACKEND_URL=http://209.38.142.207:8000
NEXT_PUBLIC_BACKEND_URL=http://209.38.142.207:8000
```

## Setup Instructions

1. **Create Vercel Blob Store**
   - Go to Vercel Dashboard → Project → Storage tab
   - Click "Connect Database" → Create New → Blob
   - Name your store (e.g., "video-storage")
   - Select environments (Production, Preview, Development)
   - Click "Create"
   - Copy the `BLOB_READ_WRITE_TOKEN` from the store settings

2. **Configure Environment Variables in Vercel**
   - Go to Project Settings → Environment Variables
   - Add these variables:
     ```
     BLOB_READ_WRITE_TOKEN = vercel_blob_rw_[your-token-here]
     BACKEND_URL = http://209.38.142.207:8000
     ```
   - Make sure they're set for all environments you need

3. **Configure Local Development**
   - Create `frontend/.env.local`:
     ```bash
     BLOB_READ_WRITE_TOKEN=vercel_blob_rw_[your-token-here]
     BACKEND_URL=http://209.38.142.207:8000
     NEXT_PUBLIC_BACKEND_URL=http://209.38.142.207:8000
     ```

4. **Deploy**
   - Push changes to trigger Vercel deployment
   - Wait for deployment to complete
   - Verify environment variables are loaded

## Data Flow

1. User selects video files
2. Frontend uploads to Vercel Blob (multipart for large files)
3. Blob returns public URL
4. Frontend sends blob URL to backend via `/api/ingest-blob`
5. Backend downloads video from blob URL
6. Backend processes video (splits if >2GB or >7200s)
7. Backend generates embeddings via TwelveLabs
8. Backend returns embeddings and video metadata
9. Frontend stores results in session storage
10. Analysis page uses blob URLs directly for video playback

## Benefits

- **No size limits**: Supports videos up to 5GB
- **Better performance**: Direct uploads bypass Vercel Functions
- **Simplified code**: No custom chunking logic needed
- **Cost effective**: 3x cheaper than Fast Data Transfer
- **Global CDN**: Videos served from Vercel's edge network

## Troubleshooting

### 404 Not Found on /api/blob/upload
- Ensure `BLOB_READ_WRITE_TOKEN` is set in Vercel environment variables
- Check that the token starts with `vercel_blob_rw_`
- Redeploy after adding environment variables

### 502 Bad Gateway
- Ensure `BACKEND_URL` is set correctly in Vercel
- Check backend is accessible from external IPs
- Verify backend is running on all interfaces (0.0.0.0:8000)

### Mixed Content Errors
- All requests go through Vercel proxy to maintain HTTPS
- Backend can remain HTTP-only

### Upload Failures
- Check `BLOB_READ_WRITE_TOKEN` is valid
- Verify file size is under 5GB limit
- Ensure video MIME types are allowed

## Security Considerations

- Blob URLs are public but unguessable (random suffix)
- Backend requires API key authentication
- Upload tokens are generated server-side only
- No anonymous uploads allowed

## Logging Implementation Details

### Frontend Logging

#### Browser Console Logs
The frontend now provides detailed logging for debugging:

```javascript
// Blob Upload Progress (shown in your console)
[Blob Upload] Starting upload for video.mp4 (704.32 MB)
[Blob Upload] Progress: 0%
[Blob Upload] Progress: 10%
...
[Blob Upload] Progress: 100%
[Blob Upload] Completed. URL: https://fuq9yiiurpveek3t.public.blob.vercel-storage.com/...

// Polling Status
[Polling] Starting to poll task task_605a8a6623bd51f1
Task task_605a8a6623bd51f1 status: downloading
Task task_605a8a6623bd51f1 status: processing 0/1 parts processed
Task task_605a8a6623bd51f1 status: processing 0/1 parts processed (est. 25m 30s remaining)
Task task_605a8a6623bd51f1 status: completed
```

#### Error Handling
- Network errors during polling are caught and retried
- Per-request timeouts (10s) prevent hanging
- Detailed error messages for debugging

### Backend Logging

#### PST Timestamps
All backend logs now use PST timezone for consistency:
```python
2025-08-12 11:50:40 PST - __main__ - INFO - [Task task_56d68e11c406c1ad] Starting download from Vercel Blob
```

#### Download Progress
Detailed download tracking with speed metrics:
```
[Task task_id] Starting download from Vercel Blob: video.mp4
[Task task_id] Blob URL: https://fuq9yiiurpveek3t.public.blob...
[Task task_id] Downloading 1073.36 MB
[Task task_id] Download progress: 43.5% (467.0 MB)
[Task task_id] Download completed: 1073.36 MB in 11.4s (94.5 MB/s)
```

#### Video Processing
```
[Task task_id] Checking if video needs splitting...
[Task task_id] Video split into 1 part(s)
[Task task_id] Creating TwelveLabs embedding task for part 1/1
```

#### TwelveLabs Cache Detection
The system now checks if TwelveLabs returns embeddings immediately:
```
[Task task_id] TwelveLabs task created: 689b87b53e195789d4685ba3
[Task task_id] Initial status: processing - no immediate cache hit
# OR if cached:
[Task task_id] WOW! TwelveLabs returned embeddings IMMEDIATELY for task 689b87b53e195789d4685ba3 - they must be caching!
```

#### Status Updates
```
[Task task_id] TwelveLabs task 689b87b53e195789d4685ba3 (part 1) status: processing
[Task task_id] Part 1 completed. Progress: 1/1
[Task task_id] Progress: 1/1 parts processed
```

#### Error Reporting
Enhanced error details when TwelveLabs tasks fail:
```
[Task task_id] TwelveLabs task failed with details: {
  "task_id": "689b87b53e195789d4685ba3",
  "status": "failed",
  "error": "Invalid video format",
  "error_message": "The video codec is not supported"
}
```

### Asynchronous Processing

The backend now processes videos asynchronously to avoid Vercel timeouts:

1. **Immediate Response**: `/ingest-blob` returns a task ID immediately
2. **Background Processing**: Video download and embedding happens in a background thread
3. **Status Polling**: Frontend polls `/ingest-blob/status/{task_id}` for updates
4. **Progress Tracking**: Shows "X/Y parts processed" with time estimates

### API Response Examples

#### Task Status Response
```json
{
  "task_id": "task_605a8a6623bd51f1",
  "status": "processing",
  "created_at": "2025-08-12T17:46:25.872706+00:00",
  "progress": "0/1 parts processed",
  "estimated_remaining_seconds": 1530,
  "elapsed_seconds": 120
}
```

#### Completed Task Response
```json
{
  "task_id": "task_605a8a6623bd51f1",
  "status": "completed",
  "embeddings": { "segments": [...] },
  "filename": "video.mp4",
  "duration": 3360.5,
  "embedding_id": "embed_abc123",
  "video_url": "https://fuq9yiiurpveek3t.public.blob.vercel-storage.com/..."
}
```

#### Failed Task Response
```json
{
  "task_id": "task_605a8a6623bd51f1",
  "status": "failed",
  "error": "TwelveLabs task 689b87b53e195789d4685ba3 failed: Invalid video format"
}
```

## Implementation Changes Summary

### Frontend (`src/lib/api.ts`)
- Added `[Blob Upload]` prefixed logs for upload progress
- Added `[Polling]` prefixed logs for status checks
- Implemented retry logic for network errors
- Added per-request timeout (10s) with AbortSignal
- Display estimated remaining time in progress updates
- Only use multipart upload for files > 300MB

### Backend (`app.py`)
- Implemented PST timezone formatter for all logs
- Added `[Task {id}]` prefix to all task-related logs
- Enhanced download progress logging with speed calculations
- Added immediate cache detection after TwelveLabs task creation
- Improved error reporting with all available error fields
- Added progress tracking with time estimates

### Key Benefits
1. **Better Debugging**: Detailed logs at every step
2. **Performance Insights**: Download/upload speeds visible
3. **Cache Detection**: Can verify if TwelveLabs caches videos
4. **Error Clarity**: Specific failure reasons logged
5. **Progress Visibility**: Time estimates for long operations

## Future Improvements

- Add progress callbacks for better UX
- Implement blob cleanup for old videos
- Add video compression before upload
- Support resume for interrupted uploads
- Implement local caching to avoid re-processing identical videos
