# SAGE - Video Comparison with AI Embeddings

A modern, AI-powered video comparison application that leverages TwelveLabs AI embeddings to analyze and compare video content at the segment level.

## 🚀 Features

- **AI-Powered Video Analysis** - Uses TwelveLabs Marengo-retrieval-2.7 model
- **Real-Time Video Processing** - Asynchronous embedding generation with progress tracking
- **Segment-Level Comparison** - Identifies differences at precise timestamps
- **Synchronized Video Playback** - Side-by-side video comparison with timeline markers
- **Drag & Drop Interface** - Modern upload experience with video thumbnails
- **Configurable Thresholds** - Adjustable sensitivity for difference detection
- **Visual Timeline** - Color-coded difference markers on synchronized video timeline

## 🏗️ Architecture

- **Frontend**: Next.js 15 with React 19, TypeScript, and Tailwind CSS
- **Backend**: FastAPI with Python 3.12+
- **AI Service**: TwelveLabs API integration
- **Database**: SQLite for API key storage
- **Storage**: In-memory for videos and embeddings

## 📦 Installation

### Prerequisites

- Python 3.12+
- Node.js 18+
- TwelveLabs API key
- Git

### Backend Setup

```bash
cd SAGE_new/backend

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export TWELVELABS_API_KEY="your_api_key"

# Run backend
python app.py
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

```bash
cd SAGE_new/frontend

# Install dependencies
npm install

# Set environment variables (optional)
export NEXT_PUBLIC_API_URL="http://localhost:8000"

# Run development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

## 🔑 Configuration

1. **Get TwelveLabs API Key**: Sign up at [twelvelabs.io](https://twelvelabs.io/)
2. **Set Environment Variable**: `export TWELVELABS_API_KEY="your_key"`
3. **Start Backend**: Run `python app.py` in the backend directory
4. **Start Frontend**: Run `npm run dev` in the frontend directory
5. **Configure API Key**: Enter your API key in the SAGE interface

## 📱 Usage

### 1. Upload Videos
- Navigate to the main page
- Upload up to 2 video files (MP4 recommended)
- Wait for AI processing to complete

### 2. Start Comparison
- Click "Start Comparison" when both videos are ready
- Navigate to the analysis page

### 3. Analyze Differences
- Use synchronized video players for side-by-side comparison
- Adjust similarity threshold for different sensitivity levels
- Click on timeline markers to jump to specific differences
- View detailed difference statistics in the right panel

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
