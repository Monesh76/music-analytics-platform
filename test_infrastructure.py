#!/usr/bin/env python3
"""
Simple infrastructure test script
"""

import json
import requests
from datetime import datetime

def test_ingestion_function():
    """Test the ingestion function with a sample event."""
    
    # Sample event data
    event_data = {
        "event_id": "evt_test_002",
        "event_type": "play",
        "track": {
            "id": "track_002",
            "title": "Hotel California",
            "artist": "Eagles",
            "album": "Hotel California",
            "duration": 391,
            "genre": "rock",
            "release_year": 1976
        },
        "artist": {
            "id": "artist_002",
            "name": "Eagles",
            "genre": "rock",
            "followers": 45000000
        },
        "user_interaction": {
            "user_id": "user_002",
            "session_id": "session_002",
            "timestamp": "2024-01-15T11:30:00Z",
            "location": "Los Angeles, CA"
        },
        "streaming_event": {
            "platform": "spotify",
            "quality": "high",
            "bitrate": 320
        },
        "timestamp": "2024-01-15T11:30:00Z"
    }
    
    # Function URL
    function_url = "https://music-event-ingestion-dev-y42dokfiga-uc.a.run.app/ingest_music_event"
    
    try:
        # Get authentication token
        import subprocess
        token = subprocess.check_output(["gcloud", "auth", "print-identity-token"], text=True).strip()
        
        # Make request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.post(function_url, json=event_data, headers=headers)
        
        print(f"✅ Ingestion Function Test:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            print("   ✅ SUCCESS: Event ingested successfully!")
        else:
            print("   ❌ FAILED: Event ingestion failed!")
            
    except Exception as e:
        print(f"❌ Error testing ingestion function: {e}")

def test_pubsub_topics():
    """Test Pub/Sub topics."""
    try:
        import subprocess
        
        # List topics
        result = subprocess.run([
            "gcloud", "pubsub", "topics", "list", 
            "--project=mystage-claudellm"
        ], capture_output=True, text=True)
        
        print(f"✅ Pub/Sub Topics Test:")
        print(f"   {result.stdout}")
        
        if "raw-music-events-dev" in result.stdout:
            print("   ✅ SUCCESS: Pub/Sub topics are working!")
        else:
            print("   ❌ FAILED: Pub/Sub topics not found!")
            
    except Exception as e:
        print(f"❌ Error testing Pub/Sub: {e}")

def test_bigquery():
    """Test BigQuery dataset."""
    try:
        import subprocess
        
        # List datasets
        result = subprocess.run([
            "bq", "ls", "--project_id=mystage-claudellm"
        ], capture_output=True, text=True)
        
        print(f"✅ BigQuery Test:")
        print(f"   {result.stdout}")
        
        if "music_analytics_dev" in result.stdout:
            print("   ✅ SUCCESS: BigQuery dataset is working!")
        else:
            print("   ❌ FAILED: BigQuery dataset not found!")
            
    except Exception as e:
        print(f"❌ Error testing BigQuery: {e}")

def test_storage():
    """Test Cloud Storage bucket."""
    try:
        import subprocess
        
        # List bucket contents
        result = subprocess.run([
            "gsutil", "ls", "gs://mystage-claudellm-music-pipeline-dev/"
        ], capture_output=True, text=True)
        
        print(f"✅ Cloud Storage Test:")
        print(f"   {result.stdout}")
        
        if "gs://mystage-claudellm-music-pipeline-dev/" in result.stdout:
            print("   ✅ SUCCESS: Cloud Storage bucket is working!")
        else:
            print("   ❌ FAILED: Cloud Storage bucket not found!")
            
    except Exception as e:
        print(f"❌ Error testing Cloud Storage: {e}")

def main():
    """Run all infrastructure tests."""
    print("🧪 Testing Real-Time Music Data Pipeline Infrastructure")
    print("=" * 60)
    
    test_pubsub_topics()
    print()
    
    test_bigquery()
    print()
    
    test_storage()
    print()
    
    test_ingestion_function()
    print()
    
    print("🎉 Infrastructure Test Complete!")

if __name__ == "__main__":
    main() 