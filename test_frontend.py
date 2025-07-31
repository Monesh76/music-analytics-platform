#!/usr/bin/env python3
"""
Test script to verify the frontend is working correctly.
"""

import requests
import json
import time

def test_frontend():
    """Test the frontend server and API."""
    print("🧪 Testing Music Event Enrichment Frontend")
    print("=" * 50)
    
    # Test 1: Check if server is running
    print("📋 1. Checking server status...")
    try:
        response = requests.get("http://localhost:8000", timeout=5)
        if response.status_code == 200:
            print("   ✅ Server is running")
        else:
            print(f"   ❌ Server returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Server not accessible: {e}")
        return False
    
    # Test 2: Check if API endpoint is working
    print("\n📋 2. Testing API endpoint...")
    try:
        test_data = {
            "event_id": "test_event_001",
            "event_type": "play",
            "track": {
                "id": "track_test",
                "title": "Test Song",
                "artist": "Test Artist",
                "album": "Test Album",
                "duration": 180,
                "genre": "pop",
                "release_year": 2024
            },
            "artist": {
                "id": "artist_test",
                "name": "Test Artist",
                "genre": "pop",
                "followers": 1000000
            },
            "user_interaction": {
                "user_id": "user_test",
                "session_id": "session_test",
                "timestamp": "2024-01-16T12:00:00Z",
                "location": "Test City"
            },
            "streaming_event": {
                "platform": "spotify",
                "quality": "high",
                "bitrate": 320
            },
            "timestamp": "2024-01-16T12:00:00Z"
        }
        
        response = requests.post(
            "http://localhost:8000/api/enrich",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ API endpoint working")
            print(f"   📊 Response: {result.get('status', 'unknown')}")
            if 'enrichments' in result:
                print(f"   🧠 Enrichments generated: {len(result['enrichments'])}")
        else:
            print(f"   ❌ API returned status {response.status_code}")
            print(f"   📄 Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"   ❌ API test failed: {e}")
        return False
    
    # Test 3: Check if static files are served
    print("\n📋 3. Testing static file serving...")
    try:
        response = requests.get("http://localhost:8000/script.js", timeout=5)
        if response.status_code == 200:
            print("   ✅ Static files are being served")
        else:
            print(f"   ❌ Static files returned status {response.status_code}")
    except Exception as e:
        print(f"   ❌ Static file test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Frontend tests completed successfully!")
    print("🌐 Open your browser to: http://localhost:8000")
    print("🎵 Start testing your music enrichment pipeline!")
    
    return True

if __name__ == "__main__":
    test_frontend() 