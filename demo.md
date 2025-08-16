# SAGE Demo Guide

This guide will help you test the SAGE video comparison system.

## 🚀 Quick Start

1. **Set your TwelveLabs API key:**
   ```bash
   export TWELVELABS_API_KEY="your_actual_api_key_here"
   ```

2. **Run the startup script:**
   ```bash
   ./start.sh
   ```

3. **Open your browser and go to:** `http://localhost:3000`

## 🎬 Testing the System

### Step 1: API Key Configuration
- Enter your TwelveLabs API key
- Click "Validate & Continue"
- The system will validate your key and store it securely

### Step 2: Video Upload
- Upload two video files (MP4 format recommended)
- Watch the progress indicators:
  - **Uploading**: File is being uploaded to the backend
  - **Processing**: AI is generating embeddings
  - **Ready**: Video is ready for comparison

### Step 3: Start Comparison
- Once both videos are ready, click "Start Comparison"
- You'll be redirected to the analysis page

### Step 4: Analysis Interface
The analysis page features:

#### **Video Players (Left Side)**
- Side-by-side synchronized video players
- Both videos play/pause together
- Current time display

#### **Timeline Controls (Center)**
- **Difference Visualization Bar**: Color-coded markers showing where differences occur
- **Main Playback Track**: Interactive timeline with progress indicator
- **Time Labels**: 0:00, midpoint, and end time

#### **Threshold Settings (Top Right)**
- Click the "Threshold Settings" button
- Adjust sensitivity slider (0.01 - 0.5)
- Lower values = more sensitive (detect subtle differences)
- Higher values = less sensitive (only major differences)

#### **Differences Panel (Right Side)**
- List of all detected differences with timestamps
- Click any difference to jump to that time
- Color-coded badges showing difference severity
- Summary statistics at the bottom

## 🎨 Understanding the Interface

### Color Coding
- **Red**: Major differences (distance > 0.4)
- **Orange**: Significant differences (distance > 0.3)
- **Amber**: Moderate differences (distance > 0.2)
- **Yellow**: Minor differences (distance > 0.1)
- **Lime**: Very minor differences (distance > 0.05)
- **Cyan**: Minimal differences (distance ≤ 0.05)
- **Grey**: Overall comparison markers

### Timeline Navigation
- **Click on timeline**: Jump to specific time
- **Click on difference markers**: Jump to difference start time
- **Drag timeline**: Seek through video
- **Hover effects**: See time information

### Video Synchronization
- **Play/Pause**: Controls both videos simultaneously
- **Time scrubbing**: Both videos seek together
- **Current time**: Always shows synchronized time

## 🔧 Testing Different Scenarios

### Test Case 1: Identical Videos
- Upload the same video twice
- Expected result: No differences detected
- Similarity: 100%

### Test Case 2: Slightly Different Videos
- Upload videos with minor edits
- Adjust threshold to 0.05 for sensitivity
- Expected result: Few differences detected

### Test Case 3: Very Different Videos
- Upload completely different videos
- Adjust threshold to 0.3 for less sensitivity
- Expected result: Many differences detected

### Test Case 4: Threshold Adjustment
- Start with threshold 0.1
- Gradually increase to 0.3
- Watch how fewer differences are detected
- Gradually decrease to 0.01
- Watch how more subtle differences appear

## 🐛 Troubleshooting

### Common Issues

1. **"No video data found" error**
   - Go back to upload page
   - Upload videos again
   - Ensure both videos show "Ready" status

2. **Videos not playing**
   - Check browser console for errors
   - Ensure backend is running on port 8000
   - Check video format compatibility

3. **No differences detected**
   - Try lowering the threshold
   - Check if videos are actually different
   - Verify API key has sufficient quota

4. **Slow performance**
   - Check network connectivity
   - Monitor browser console for errors
   - Ensure sufficient system resources

## 📊 Understanding Results

### Similarity Percentage
- **100%**: Videos are identical
- **90-99%**: Very similar videos
- **70-89%**: Moderately similar videos
- **50-69%**: Somewhat different videos
- **Below 50%**: Very different videos

### Distance Values
- **0.0**: Identical segments
- **0.1**: Very similar segments
- **0.3**: Moderately different segments
- **0.5**: Very different segments
- **Infinity**: Missing segments (one video longer than the other)

### Segment Information
- **Total segments**: Number of time segments analyzed
- **Different segments**: Number of segments exceeding threshold
- **Threshold used**: Current sensitivity setting

## 🎯 Advanced Testing

### Performance Testing
- Upload larger video files
- Test with different video formats
- Monitor processing times

### Edge Cases
- Videos of different lengths
- Videos with different frame rates
- Videos with different resolutions
- Very short videos (< 10 seconds)
- Very long videos (> 10 minutes)

### Browser Compatibility
- Test on different browsers
- Test on mobile devices
- Test with different screen sizes

## 🔮 Next Steps

After testing the basic functionality:

1. **Explore the API**: Visit `http://localhost:8000/docs`
2. **Check health**: Visit `http://localhost:8000/health`
3. **Monitor logs**: Watch backend console output
4. **Customize thresholds**: Experiment with different sensitivity levels

## 📝 Notes

- The current implementation uses mock embedding data for demonstration
- In production, actual TwelveLabs API calls would generate real embeddings
- Video storage is in-memory and will be lost on server restart
- The system is designed for development and testing purposes

---

**Happy testing! 🎉**
