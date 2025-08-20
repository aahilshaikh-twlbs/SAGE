# SAGE - Video Comparison with AI Embeddings

A modern, AI-powered video comparison application that leverages TwelveLabs AI embeddings to analyze and compare video content at the segment level.

## ⚠️ CRITICAL: Large Video Handling

**IMPORTANT**: For videos longer than 10 minutes, please read the [Large Video Handling Guide](docs/LARGE_VIDEO_HANDLING.md) before use. These fixes are essential for reliable operation with longer videos.

- **Videos 1-10 minutes**: Work out of the box
- **Videos 10+ minutes**: Require the implemented fixes for proper operation
- **Videos 15+ minutes**: Critical fixes prevent silent failures and incorrect results

## 📚 **Documentation**

- **[User Guide](docs/USER_GUIDE.md)** - Complete user documentation, setup, and usage
- **[Developer Guide](docs/DEVELOPER_GUIDE.md)** - Technical implementation and architecture
- **[Large Video Handling](docs/LARGE_VIDEO_HANDLING.md)** - Critical fixes for videos >10 minutes
- **[Upload Process](docs/UPLOAD_PROCESS.md)** - Detailed upload implementation details

## 🚀 **Features**

- **AI-Powered Video Analysis** - TwelveLabs Marengo-retrieval-2.7 model
- **Real-Time Processing** - Asynchronous embedding generation with progress tracking
- **Segment-Level Comparison** - Identifies differences at precise timestamps
- **Synchronized Playback** - Side-by-side video comparison with timeline markers
- **Drag & Drop Interface** - Modern upload experience with video thumbnails
- **Configurable Thresholds** - Adjustable sensitivity for difference detection
- **Visual Timeline** - Color-coded difference markers on synchronized timeline

*For detailed feature information, see the [User Guide](docs/USER_GUIDE.md).*

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.12+
- Node.js 18+ or Bun
- TwelveLabs API key
- Git

### **Basic Setup**
```bash
# Backend
cd SAGE/backend
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export TWELVELABS_API_KEY="your_key"
python app.py

# Frontend (new terminal)
cd SAGE/frontend
bun install  # or npm install
bun dev      # or npm run dev
```

*For complete setup instructions, see the [User Guide](docs/USER_GUIDE.md).*

## 🎨 UI Components

- **ApiKeyConfig**: API key input and validation
- **Video Upload**: Drag & drop interface with thumbnails
- **Video Player**: Synchronized dual video playback
- **Timeline**: Interactive timeline with difference markers
- **Settings Panel**: Threshold adjustment and configuration

## 🔧 API Endpoints

- `POST /validate-key` - Validate TwelveLabs API key
- `POST /upload-and-generate-embeddings` - Upload and process video
- `POST /compare-local-videos` - Compare two videos
- `GET /serve-video/{video_id}` - Stream video content
- `GET /health` - Server health check

## 🎯 Key Features

### Analysis Tab Layout
The analysis page features:
- **Side-by-side video players** with synchronized controls
- **Visual timeline** with color-coded difference markers
- **Real-time threshold adjustment** for comparison sensitivity
- **Difference list** with clickable segments
- **Statistics panel** showing comparison metrics

### Video Synchronization
- Play/pause controls synchronized between both players
- Timeline scrubbing updates both videos simultaneously
- Current time display and progress tracking
- Difference markers overlay on timeline

### Threshold Controls
- Adjustable similarity threshold (0.01 - 0.5)
- Real-time comparison updates
- Visual feedback on difference sensitivity
- Preset threshold options

## 🚧 Current Limitations

- In-memory storage (videos lost on server restart)
- Single server deployment
- 2-video comparison limit
- Mock embedding data for demonstration

## 🔧 Recent Critical Fixes

### Large Video Handling (August 2024)
**CRITICAL FIXES** have been implemented to handle videos longer than 10 minutes reliably:

- **Fixed embedding generation failures** for videos >15 minutes
- **Eliminated silent failures** that produced incorrect comparison results
- **Added comprehensive validation** for segment generation and coverage
- **Implemented proper error handling** with clear failure messages
- **Fixed Python scoping issues** that prevented upload completion

**📖 For complete details, see: [Large Video Handling Guide](docs/LARGE_VIDEO_HANDLING.md)**

### What Was Fixed
- Videos 18-19 minutes: Previously failing, now working correctly
- Videos 26-29 minutes: Previously failing, now working correctly  
- Videos 8 minutes: Continue working as before
- All video lengths: Now provide clear success/failure feedback

### Impact
- **Before**: Silent failures, incorrect results, confusing behavior
- **After**: Reliable operation or clear error messages
- **Coverage**: Videos up to 2 hours (TwelveLabs limit) now supported

## 🔮 Future Enhancements

- Persistent storage with PostgreSQL
- User management and authentication
- Export features for comparison reports
- Batch processing for multiple videos
- S3 integration for scalable storage
- Redis caching for performance optimization

## 🐛 Troubleshooting

### Common Issues

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
   - **CRITICAL**: Read [Large Video Handling Guide](docs/LARGE_VIDEO_HANDLING.md)
   - Check backend logs for embedding generation errors
   - Verify video format compatibility
   - Monitor processing time (can take 15-30 minutes for very long videos)

### For Large Videos (10+ minutes)
If you're experiencing issues with videos longer than 10 minutes:

1. **Check the logs** for detailed error messages
2. **Verify embedding generation** completed successfully
3. **Check segment count** vs expected count
4. **Review the [Large Video Handling Guide](docs/LARGE_VIDEO_HANDLING.md)** for detailed troubleshooting

**Note**: The system now provides clear error messages instead of silent failures. If a large video fails, you'll get a specific error explaining what went wrong.

### **For Complete Troubleshooting**
See the [User Guide](docs/USER_GUIDE.md#-troubleshooting) for comprehensive troubleshooting information and the [Developer Guide](docs/DEVELOPER_GUIDE.md) for technical debugging.

## 📚 **Documentation Structure**

The SAGE documentation has been consolidated for better organization:

- **[User Guide](docs/USER_GUIDE.md)** - Complete user documentation (consolidated from QUICK_REFERENCE + SAGE_DOCUMENTATION)
- **[Developer Guide](docs/DEVELOPER_GUIDE.md)** - Technical implementation (consolidated from ARCHITECTURE + TECHNICAL_SPECIFICATION)
- **[Large Video Handling](docs/LARGE_VIDEO_HANDLING.md)** - Critical fixes for large videos (specialized)
- **[Upload Process](docs/UPLOAD_PROCESS.md)** - Detailed upload implementation (specialized)

*This consolidation eliminates redundancy while preserving all essential information.*

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

**SAGE** - Making AI-powered video comparison accessible and intuitive.
