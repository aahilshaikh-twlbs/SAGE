# SAGE Architecture Revamp

## Goals
- More modularized frontend
- Better code pipelines for debugging

## Upload Pipeline

### Default Configuration
- Pro plan Vercel: 1GB upload limit

### Fat Checker
- Checks how fat a given file is (filesize) - will be used in multiple places
- First check input file sizes for both videos

### Sub-Upload Pipeline: Frontend to Backend
1. Upload modal takes incoming bytestream and saves to byte file
2. Save until content reaches 1GB, then save as `video_A/B_chunk_X`
3. Immediately send chunk to backend to save locally in a folder, then delete chunk from frontend
4. Next set of incoming bytes (should start saving after deletion of chunkA since Vercel browser/localstore is limited)
5. Save to video_chunk file, repeat until whole video chunked into bytestream objects

### Backend Processing
- Concatenate all byte chunks into single bytefile via Python file concat with `wb+`
- Rename file to MP4
- If video >7200s or >2GB: chunk into acceptable segments
- Call embed API multiple times
- Concatenate all embeds from one video into single dict object

## Embed Pipeline
- Call embed API `x_chunks` times
- Concatenate all embeds from one video into single dict object
- Pass to comparison logic

## Comparison Pipeline
- Wait for complete dict/JSON objects from both videos
- Run comparison
- Save to RAM/cache for threshold adjustment s and reruns