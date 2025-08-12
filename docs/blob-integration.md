# Vercel Blob Integration Guide

## Overview

This document describes the integration of Vercel Blob storage for handling large video uploads in the SAGE application. The system now uses Vercel Blob for direct client-side uploads, bypassing Vercel Function size limits.

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
   - Go to Vercel Dashboard → Storage → Create Blob Store
   - Copy the read-write token

2. **Configure Environment Variables**
   - Add variables in Vercel project settings
   - Create local `.env.local` file

3. **Deploy**
   - Push changes to trigger Vercel deployment
   - Ensure backend is accessible from Vercel servers

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

## Future Improvements

- Add progress callbacks for better UX
- Implement blob cleanup for old videos
- Add video compression before upload
- Support resume for interrupted uploads
