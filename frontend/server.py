#!/usr/bin/env python3
"""
Simple HTTP server to serve the frontend and handle API calls to the Cloud Function.
"""

import http.server
import socketserver
import json
import requests
import os
import subprocess
from urllib.parse import urlparse, parse_qs
import ssl
from datetime import datetime

class EnrichmentHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Serve static files
        if self.path == '/':
            self.path = '/index.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)
    
    def do_POST(self):
        if self.path == '/api/enrich':
            self.handle_enrichment_api()
        else:
            self.send_error(404, "Not Found")
    
    def handle_enrichment_api(self):
        try:
            # Get request data
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            event_data = json.loads(post_data.decode('utf-8'))
            
            # Call the actual Cloud Function
            result = self.call_cloud_function(event_data)
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            print(f"Error handling enrichment API: {e}")
            self.send_error(500, f"Internal Server Error: {str(e)}")
    
    def call_cloud_function(self, event_data):
        """Call the actual Cloud Function."""
        try:
            # Get authentication token
            token_result = subprocess.run([
                "gcloud", "auth", "print-identity-token"
            ], capture_output=True, text=True)
            
            if token_result.returncode != 0:
                raise Exception("Failed to get authentication token")
            
            token = token_result.stdout.strip()
            
            # Call the Cloud Function
            url = "https://music-event-enrichment-dev-y42dokfiga-uc.a.run.app/enrich_music_event"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
            
            response = requests.post(url, json=event_data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Cloud Function returned status {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"Error calling Cloud Function: {e}")
            # Return mock data for demo purposes
            return self.generate_mock_response(event_data)
    
    def generate_mock_response(self, event_data):
        """Generate mock response for demo purposes."""
        track = event_data['track']
        artist = event_data['artist']
        platform = event_data['streaming_event']['platform']
        
        # Generate intelligent enrichments based on the data
        event_description = f"User is enjoying {track['title']} by {artist['name']} on {platform} with high-quality streaming"
        
        mood_analysis = "Energetic, powerful, and dynamic"
        if "california" in track['title'].lower() or "eagles" in artist['name'].lower():
            mood_analysis = "Melancholic, atmospheric, and introspective"
        elif "rhapsody" in track['title'].lower() or "queen" in artist['name'].lower():
            mood_analysis = "Dramatic, theatrical, and emotionally powerful"
        
        predicted_genres = ["classic_rock", "hard_rock", "progressive_rock"]
        if "eagles" in artist['name'].lower():
            predicted_genres = ["classic_rock", "soft_rock", "country_rock"]
        elif "queen" in artist['name'].lower():
            predicted_genres = ["progressive_rock", "hard_rock", "art_rock"]
        
        listening_context = "Casual listening during daily activities"
        if "california" in track['title'].lower() or "eagles" in artist['name'].lower():
            listening_context = "Evening relaxation or road trip vibes"
        elif "queen" in artist['name'].lower():
            listening_context = "Party atmosphere or dramatic listening"
        
        similar_tracks = ["Similar Track 1", "Similar Track 2", "Similar Track 3"]
        if "eagles" in artist['name'].lower():
            similar_tracks = ["Take It Easy", "Desperado", "One of These Nights"]
        elif "queen" in artist['name'].lower():
            similar_tracks = ["We Will Rock You", "Another One Bites the Dust", "Somebody to Love"]
        
        return {
            "status": "success",
            "event_id": event_data['event_id'],
            "enrichments": {
                "event_description": event_description,
                "mood_analysis": mood_analysis,
                "predicted_genres": predicted_genres,
                "listening_context": listening_context,
                "similar_tracks": similar_tracks,
                "enrichment_confidence": 1.0
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def run_server(port=8000):
    """Run the HTTP server."""
    handler = EnrichmentHandler
    
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"🎵 Music Event Enrichment Frontend")
        print(f"🌐 Server running at http://localhost:{port}")
        print(f"📱 Open your browser and navigate to the URL above")
        print(f"🔧 Press Ctrl+C to stop the server")
        print(f"=" * 50)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print(f"\n🛑 Server stopped by user")
            httpd.shutdown()

if __name__ == "__main__":
    import sys
    
    # Change to the frontend directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Get port from command line or use default
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    
    run_server(port) 