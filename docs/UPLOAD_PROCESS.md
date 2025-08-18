# SAGE Upload Process Documentation

## Overview

The SAGE upload process is designed to handle large video files efficiently using streaming multipart uploads to AWS S3. This document details the complete upload flow, chunking strategy, and error handling mechanisms.

## Upload Flow Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Frontend  │    │   Backend   │    │     S3      │    │ TwelveLabs  │
│             │    │             │    │             │    │             │
│ File Select │───►│ Validate    │───►│ Multipart   │───►│ Embedding   │
│             │    │ & Upload    │    │ Upload      │    │ Generation  │
│ Status Poll │◄───│ Status      │◄───│ Complete    │◄───│ Complete    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

## Why Video Chunking is Necessary

### Overview

The video file is chunked into **10MB pieces** during S3 upload for several critical technical reasons. This chunking is **only for upload transport** and does not modify the original video file.

### Technical Reasons for Chunking

#### **1. Memory Exhaustion Prevention**
- **Problem**: Large videos (1GB+ files) would consume the entire server's RAM if loaded at once
- **Impact**: Server would crash with "Killed" messages when processing large files
- **Solution**: Streaming upload processes the file in small chunks, keeping memory usage low
- **Result**: Server stays stable even with massive video files

#### **2. S3 Multipart Upload Requirements**
- **S3 Limit**: Files larger than 5GB **require** multipart upload
- **Best Practice**: Multipart upload is recommended for files > 100MB
- **Reliability**: Better error handling and retry mechanisms
- **Resumability**: Failed uploads can be resumed from the last successful part

#### **3. Network Performance Optimization**
- **Connection Stability**: Smaller chunks are more reliable over network connections
- **Timeout Prevention**: Reduces risk of connection timeouts on large files
- **Progress Tracking**: Can track upload progress per chunk
- **Error Recovery**: Individual chunk failures don't require restarting entire upload

### Chunking Process Details

#### **Chunk Size Selection**
```python
chunk_size = 10 * 1024 * 1024  # 10MB chunks
```
- **Rationale**: Optimal balance between memory usage and upload efficiency
- **S3 Limit**: Maximum 10,000 parts per multipart upload
- **File Size Support**: Up to 5TB (10,000 × 10MB chunks)

#### **Chunking Implementation**
```python
while True:
    chunk = await file.read(chunk_size)  # Read 10MB at a time
    if not chunk:
        break
    
    # Upload this 10MB chunk to S3
    part_response = s3_client.upload_part(
        Bucket=S3_BUCKET_NAME,
        Key=file_key,
        PartNumber=part_number,
        UploadId=upload_id,
        Body=chunk
    )
```

### What You See in Logs

```
Uploading part 1 for video.mp4 (10485760 bytes)  # 10MB
Uploading part 2 for video.mp4 (10485760 bytes)  # 10MB
...
Uploading part 108 for video.mp4 (3526991 bytes) # Final chunk (smaller)
```

### Important: File Integrity Preserved

- **Chunking is ONLY for upload transport**
- **S3 reassembles the chunks into the original file**
- **TwelveLabs receives the complete, unmodified video**
- **No quality loss or file corruption**
- **Original file structure and content remain intact**

### Alternative Approaches

#### **1. Larger Chunk Sizes**
```python
chunk_size = 50 * 1024 * 1024  # 50MB chunks
```
- **Pros**: Faster upload, fewer API calls
- **Cons**: Higher memory usage, less reliable on slow connections

#### **2. Dynamic Chunk Sizing**
```python
# Smaller chunks for large files, larger chunks for small files
if file_size > 1_000_000_000:  # 1GB
    chunk_size = 10 * 1024 * 1024  # 10MB
else:
    chunk_size = 50 * 1024 * 1024  # 50MB
```

#### **3. Parallel Chunk Uploads**
```python
# Upload multiple chunks simultaneously
async def upload_chunk_parallel(chunk, part_number):
    return await s3_client.upload_part(...)

# Upload chunks in parallel
tasks = [upload_chunk_parallel(chunk, i) for i, chunk in enumerate(chunks)]
results = await asyncio.gather(*tasks)
```

### Performance Impact

#### **Memory Usage**
- **Without Chunking**: Entire file in memory (1GB+ for large videos)
- **With Chunking**: Only 10MB in memory at any time
- **Memory Reduction**: 99%+ reduction in peak memory usage

#### **Upload Reliability**
- **Network Errors**: Only current chunk needs retry
- **Server Crashes**: Upload can resume from last successful part
- **Timeout Handling**: Individual chunk timeouts don't fail entire upload

#### **Upload Speed**
- **Sequential**: Current implementation (reliable, predictable)
- **Parallel**: Future enhancement (faster, more complex)
- **Bandwidth**: Full bandwidth utilization with proper chunk sizing

### Troubleshooting Chunking Issues

#### **Common Problems**

**1. Too Many Parts Error**
```
Error: Multipart upload failed - too many parts
```
- **Cause**: File too large for 10MB chunks
- **Solution**: Increase chunk size to 50MB or 100MB

**2. Memory Issues**
```
Error: Out of memory during upload
```
- **Cause**: Chunk size too large
- **Solution**: Decrease chunk size to 5MB

**3. Network Timeouts**
```
Error: Connection timeout during upload
```
- **Cause**: Chunk size too large for network conditions
- **Solution**: Decrease chunk size or implement retry logic

#### **Monitoring Chunking Performance**

```python
# Log chunking metrics
logger.info(f"Chunking {file.filename}: {total_chunks} chunks, {chunk_size} bytes each")
logger.info(f"Upload progress: {completed_chunks}/{total_chunks} chunks")
logger.info(f"Memory usage: {memory_usage}MB")
```

## Detailed Upload Process

### Phase 1: Frontend File Selection

**File Input Handling**:
```typescript
const handleVideoUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
  const file = event.target.files[0];
  
  // Validation
  if (!file.content_type?.startsWith('video/')) {
    throw new Error('File must be a video');
  }
  
  // Thumbnail generation
  const thumbnail = await generateThumbnail(file);
  
  // Create local video object
  const newVideo: LocalVideo = {
    id: `video-${Date.now()}`,
    file,
    thumbnail,
    status: 'uploading',
    progress: 'Uploading to S3...'
  };
};
```

**Thumbnail Generation**:
```typescript
const generateThumbnail = (file: File): Promise<string> => {
  return new Promise((resolve) => {
    const video = document.createElement('video');
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d')!;
    
    video.onloadedmetadata = () => {
      video.currentTime = 1; // Seek to 1 second
    };
    
    video.onseeked = () => {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      resolve(canvas.toDataURL());
    };
    
    video.src = URL.createObjectURL(file);
  });
};
```

### Phase 2: Backend File Validation

**Content Type Validation**:
```python
if not file.content_type or not file.content_type.startswith('video/'):
    logger.error(f"Invalid content type: {file.content_type}")
    raise HTTPException(status_code=400, detail="File must be a video")
```

**API Key Validation**:
```python
def get_stored_api_key() -> str:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute('SELECT api_key FROM api_keys ORDER BY created_at DESC LIMIT 1')
    stored_api_key = cursor.fetchone()
    conn.close()
    
    if not stored_api_key or not stored_api_key[0]:
        raise HTTPException(status_code=400, detail="No API key found")
    
    return stored_api_key[0]
```

### Phase 3: S3 Multipart Upload

#### **Chunking Strategy**

**Chunk Size**: 10MB (10,485,760 bytes)
- **Rationale**: Optimal balance between memory usage and upload efficiency
- **S3 Limit**: Maximum 10,000 parts per multipart upload
- **File Size Support**: Up to 5TB (10,000 × 10MB chunks)

**Chunking Process**:
```python
chunk_size = 10 * 1024 * 1024  # 10MB chunks
parts = []
part_number = 1

while True:
    chunk = await file.read(chunk_size)  # Async file reading
    if not chunk:
        break
    
    logger.info(f"Uploading part {part_number} for {file.filename} ({len(chunk)} bytes)")
    
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

#### **Multipart Upload Steps**

**Step 1: Initialize Upload**
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

**Step 2: Upload Parts**
```python
for part_number in range(1, total_parts + 1):
    chunk = await file.read(chunk_size)
    
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
```

**Step 3: Complete Upload**
```python
s3_client.complete_multipart_upload(
    Bucket=S3_BUCKET_NAME,
    Key=file_key,
    UploadId=upload_id,
    MultipartUpload={'Parts': parts}
)
```

#### **Error Handling**

**Abort on Failure**:
```python
try:
    # Upload process
    pass
except Exception as e:
    # Abort multipart upload on error
    try:
        s3_client.abort_multipart_upload(
            Bucket=S3_BUCKET_NAME,
            Key=file_key,
            UploadId=upload_id
        )
    except:
        pass
    raise e
```

**Retry Logic**:
- **Network Errors**: Automatic retry with exponential backoff
- **S3 Errors**: Specific error handling for different S3 error codes
- **Timeout Handling**: Graceful timeout with cleanup

### Phase 4: Storage Initialization

**Video Metadata Storage**:
```python
video_id = f"video_{uuid.uuid4()}"
embedding_id = f"embed_{uuid.uuid4()}"

# Store video metadata (in-memory only)
video_storage[video_id] = {
    "filename": file.filename,
    "s3_url": s3_url,
    "status": "uploaded",
    "upload_timestamp": datetime.now().isoformat(),
    "embedding_id": embedding_id
}

# Initialize embedding storage (in-memory only)
embedding_storage[embedding_id] = {
    "filename": file.filename,
    "status": "pending",
    "video_id": video_id,
    "s3_url": s3_url
}
```

### Phase 5: Embedding Generation

**Presigned URL Generation**:
```python
def get_s3_presigned_url(s3_url: str, expiration: int = 3600) -> str:
    if s3_url.startswith("s3://"):
        parts = s3_url[5:].split("/", 1)
        bucket = parts[0]
        key = parts[1] if len(parts) > 1 else ""
    
    presigned_url = s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket, 'Key': key},
        ExpiresIn=expiration
    )
    return presigned_url
```

**TwelveLabs Task Creation**:
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
```

## Performance Metrics

### Upload Performance

**Chunking Benefits**:
- **Memory Efficiency**: Only 10MB in memory at any time
- **Resumability**: Can resume failed uploads (future enhancement)
- **Parallel Upload**: Can upload multiple chunks simultaneously (future enhancement)
- **Progress Tracking**: Real-time progress for each chunk

**Typical Upload Times**:
- **1GB Video**: ~2-3 minutes (depending on network)
- **5GB Video**: ~10-15 minutes
- **10GB Video**: ~20-30 minutes

### Memory Usage

**Backend Memory**:
- **Per Upload**: ~10MB (chunk size)
- **Storage**: In-memory only, no persistence
- **Peak Usage**: ~50MB for 5 concurrent uploads

**Frontend Memory**:
- **Thumbnail**: ~100KB per video
- **File Object**: Minimal (file reference only)
- **State**: ~1KB per video

## Error Scenarios

### Common Errors

**1. Network Timeout**:
```python
# S3 client timeout configuration
s3_client = session.client('s3', config=Config(
    connect_timeout=60,
    read_timeout=300,
    retries={'max_attempts': 3}
))
```

**2. Invalid File Type**:
```python
if not file.content_type.startswith('video/'):
    raise HTTPException(status_code=400, detail="File must be a video")
```

**3. API Key Issues**:
```python
try:
    client = TwelveLabs(api_key=api_key)
    client.task.list()  # Test API call
except Exception as e:
    raise HTTPException(status_code=401, detail="Invalid API key")
```

**4. S3 Upload Failure**:
```python
except ClientError as e:
    logger.error(f"Failed to upload file to S3: {e}")
    raise Exception(f"S3 upload failed: {str(e)}")
```

### Recovery Mechanisms

**1. Automatic Retry**:
- Network errors: 3 retries with exponential backoff
- S3 errors: Specific handling for different error codes

**2. Cleanup on Failure**:
- Abort multipart upload
- Remove from active tasks
- Update status to 'error'

**3. User Feedback**:
- Detailed error messages
- Progress indicators
- Retry options

## Monitoring and Logging

### Upload Logging

**Progress Logging**:
```python
logger.info(f"Starting streaming S3 upload for {file.filename}")
logger.info(f"Uploading part {part_number} for {file.filename} ({len(chunk)} bytes)")
logger.info(f"File uploaded to S3: {s3_url}")
```

**Error Logging**:
```python
logger.error(f"Failed to upload file to S3: {e}")
logger.error(f"Exception type: {type(e).__name__}")
logger.error(f"Traceback: {traceback.format_exc()}")
```

### Metrics Collection

**Upload Metrics**:
- File size
- Upload duration
- Chunk count
- Success/failure rate
- Network performance

**Performance Metrics**:
- Memory usage
- CPU utilization
- Network bandwidth
- S3 response times

## Future Enhancements

### Planned Improvements

**1. Resumable Uploads**:
- Store upload state
- Resume from last successful chunk
- Handle network interruptions

**2. Parallel Chunk Upload**:
- Upload multiple chunks simultaneously
- Improve upload speed
- Better resource utilization

**3. Progress Callbacks**:
- Real-time progress updates
- WebSocket integration
- Better user experience

**4. Compression**:
- Video compression before upload
- Reduce bandwidth usage
- Faster upload times

**5. CDN Integration**:
- CloudFront distribution
- Global content delivery
- Better streaming performance
