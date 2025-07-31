#!/bin/bash

echo "🎵 Starting Music Event Enrichment Frontend..."
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "frontend/server.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    echo "   Current directory: $(pwd)"
    echo "   Expected files: frontend/server.py"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found"
    echo "   Please run: python3 -m venv venv"
    echo "   Then: source venv/bin/activate"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if requests module is available
if ! python3 -c "import requests" &> /dev/null; then
    echo "⚠️  Installing required Python dependencies..."
    pip3 install requests
fi

# Check if gcloud is configured
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "⚠️  Warning: Google Cloud not authenticated"
    echo "   Run: gcloud auth login"
    echo "   Then: gcloud config set project mystage-claudellm"
fi

# Navigate to frontend directory and start server
cd frontend

echo "🚀 Starting server on http://localhost:8000"
echo "📱 Open your browser and navigate to the URL above"
echo "🔧 Press Ctrl+C to stop the server"
echo "=================================================="

python3 server.py 