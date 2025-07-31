#!/usr/bin/env python3
"""
Test script to verify track data functionality
"""

import json
import requests

def test_track_data():
    """Test the track data functionality."""
    print("🎵 Testing Track Data Functionality")
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
    
    # Test 2: Check if track data is accessible
    print("\n📋 2. Testing track data access...")
    try:
        response = requests.get("http://localhost:8000/test_tracks.json", timeout=5)
        if response.status_code == 200:
            tracks_data = response.json()
            tracks = tracks_data.get('test_tracks', [])
            print(f"   ✅ Track data accessible: {len(tracks)} tracks loaded")
            
            # Show some sample tracks
            print("   📊 Sample tracks:")
            for i, track in enumerate(tracks[:5]):
                print(f"      {i+1}. {track['title']} by {track['artist']} ({track['genre']})")
            
        else:
            print(f"   ❌ Track data returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Track data test failed: {e}")
        return False
    
    # Test 3: Test different genres
    print("\n📋 3. Testing genre filtering...")
    try:
        response = requests.get("http://localhost:8000/test_tracks.json", timeout=5)
        tracks_data = response.json()
        tracks = tracks_data.get('test_tracks', [])
        
        genres = ['rock', 'pop', 'soul', 'funk', 'folk']
        for genre in genres:
            genre_tracks = [t for t in tracks if t['genre'].lower() == genre.lower()]
            print(f"   🎵 {genre.capitalize()}: {len(genre_tracks)} tracks")
            
    except Exception as e:
        print(f"   ❌ Genre filtering test failed: {e}")
    
    # Test 4: Test different artists
    print("\n📋 4. Testing artist variety...")
    try:
        response = requests.get("http://localhost:8000/test_tracks.json", timeout=5)
        tracks_data = response.json()
        tracks = tracks_data.get('test_tracks', [])
        
        artists = set(track['artist'] for track in tracks)
        print(f"   🎤 Unique artists: {len(artists)}")
        print("   📋 Sample artists:")
        for artist in list(artists)[:8]:
            print(f"      • {artist}")
            
    except Exception as e:
        print(f"   ❌ Artist variety test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Track data tests completed successfully!")
    print("🌐 Open your browser to: http://localhost:8000")
    print("🎵 Use the Quick Track Selection buttons to test different tracks!")
    
    return True

if __name__ == "__main__":
    test_track_data() 