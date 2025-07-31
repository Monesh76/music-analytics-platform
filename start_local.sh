#!/bin/bash

echo "🎵 Starting Music Event Enrichment Frontend (LOCAL MODE)"
echo "========================================================"

# Check if we're in the right directory
if [ ! -f "frontend/server_local.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    echo "   Current directory: $(pwd)"
    echo "   Expected files: frontend/server_local.py"
    exit 1
fi

# Navigate to frontend directory and start local server
cd frontend

echo "🚀 Starting LOCAL server on http://localhost:8000"
echo "📱 Open your browser and navigate to the URL above"
echo "🔧 Press Ctrl+C to stop the server"
echo "💰 No GCP resources needed - running locally!"
echo "========================================================"

python3 server_local.py 