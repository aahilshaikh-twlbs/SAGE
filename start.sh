#!/bin/bash

echo "🚀 Starting SAGE - Video Comparison with AI Embeddings"
echo "=================================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.12+ first."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

# Check if TWELVELABS_API_KEY is set
if [ -z "$TWELVELABS_API_KEY" ]; then
    echo "⚠️  TWELVELABS_API_KEY environment variable is not set."
    echo "   Please set it with: export TWELVELABS_API_KEY='your_api_key'"
    echo "   Or add it to your .env file"
fi

echo ""
echo "📦 Installing backend dependencies..."
cd backend
if [ ! -d ".venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install -r requirements.txt

echo ""
echo "📦 Installing frontend dependencies..."
cd ../frontend
npm install

echo ""
echo "🔧 Starting services..."
echo "   Backend will run on http://localhost:8000"
echo "   Frontend will run on http://localhost:3000"
echo ""

# Start backend in background
cd ../backend
source .venv/bin/activate
python app.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo "✅ Services started successfully!"
echo "   Backend PID: $BACKEND_PID"
echo "   Frontend PID: $FRONTEND_PID"
echo ""
echo "🌐 Open http://localhost:3000 in your browser"
echo ""
echo "🛑 To stop services, press Ctrl+C or run:"
echo "   kill $BACKEND_PID $FRONTEND_PID"

# Wait for user to stop
trap "echo ''; echo '🛑 Stopping services...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT

# Keep script running
wait
