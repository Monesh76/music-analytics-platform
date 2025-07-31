#!/usr/bin/env python3
"""
Local HTTP server for testing the frontend without GCP dependencies.
"""

import http.server
import socketserver
import json
from datetime import datetime, timezone

class LocalEnrichmentHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Serve static files
        if self.path == '/':
            self.path = '/index.html'
        elif self.path == '/test_tracks.json':
            # Serve the test tracks JSON file
            self.path = '/test_tracks.json'
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
            
            # Generate local enrichments (no GCP needed)
            result = self.generate_local_enrichments(event_data)
            
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
    
    def generate_local_enrichments(self, event_data):
        """Generate enrichments locally without GCP."""
        track = event_data['track']
        artist = event_data['artist']
        platform = event_data['streaming_event']['platform']
        
        # Generate intelligent enrichments based on the data
        event_description = f"User is enjoying {track['title']} by {artist['name']} on {platform} with high-quality streaming"
        
        # Enhanced mood analysis based on track and artist
        mood_analysis = self.get_mood_analysis(track['title'], artist['name'], track['genre'])
        
        # Enhanced genre prediction
        predicted_genres = self.get_predicted_genres(track['title'], artist['name'], track['genre'])
        
        # Enhanced listening context
        listening_context = self.get_listening_context(track['title'], artist['name'], track['genre'])
        
        # Enhanced similar tracks based on actual artist and track
        similar_tracks = self.get_similar_tracks(track['title'], artist['name'], track['genre'])
        
        # Calculate realistic confidence based on data completeness
        confidence = self.calculate_confidence(track, artist, platform)
        
        return {
            "status": "success",
            "event_id": event_data['event_id'],
            "enrichments": {
                "event_description": event_description,
                "mood_analysis": mood_analysis,
                "predicted_genres": predicted_genres,
                "listening_context": listening_context,
                "similar_tracks": similar_tracks,
                "enrichment_confidence": confidence
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def get_mood_analysis(self, track_title, artist_name, genre):
        """Get accurate mood analysis based on track and artist."""
        track_lower = track_title.lower()
        artist_lower = artist_name.lower()
        genre_lower = genre.lower()
        
        # Specific track-based moods
        if "hotel california" in track_lower or "eagles" in artist_lower:
            return "Melancholic, atmospheric, and introspective"
        elif "bohemian rhapsody" in track_lower or "queen" in artist_lower:
            return "Dramatic, theatrical, and emotionally powerful"
        elif "stairway to heaven" in track_lower or "led zeppelin" in artist_lower:
            return "Epic, mystical, and transcendent"
        elif "sweet child" in track_lower or "guns" in artist_lower:
            return "Energetic, passionate, and anthemic"
        elif "billie jean" in track_lower or "michael jackson" in artist_lower:
            return "Groovy, infectious, and danceable"
        elif "imagine" in track_lower or "john lennon" in artist_lower:
            return "Peaceful, idealistic, and inspiring"
        elif "smells like teen spirit" in track_lower or "nirvana" in artist_lower:
            return "Raw, rebellious, and angst-filled"
        elif "superstition" in track_lower or "stevie wonder" in artist_lower:
            return "Funky, soulful, and groove-heavy"
        elif "respect" in track_lower or "aretha franklin" in artist_lower:
            return "Empowering, soulful, and confident"
        elif "purple haze" in track_lower or "jimi hendrix" in artist_lower:
            return "Psychedelic, experimental, and mind-bending"
        elif "good vibrations" in track_lower or "beach boys" in artist_lower:
            return "Harmonious, sunny, and feel-good"
        elif "what's going on" in track_lower or "marvin gaye" in artist_lower:
            return "Smooth, socially conscious, and soulful"
        elif "johnny b. goode" in track_lower or "chuck berry" in artist_lower:
            return "Energetic, pioneering, and rock 'n' roll"
        elif "i want to hold your hand" in track_lower or "beatles" in artist_lower:
            return "Infectious, youthful, and romantic"
        elif "like a rolling stone" in track_lower or "bob dylan" in artist_lower:
            return "Poetic, rebellious, and thought-provoking"
        
        # Genre-based fallback
        if "rock" in genre_lower:
            return "Energetic, powerful, and dynamic"
        elif "pop" in genre_lower:
            return "Catchy, upbeat, and accessible"
        elif "soul" in genre_lower or "funk" in genre_lower:
            return "Smooth, soulful, and groove-heavy"
        elif "folk" in genre_lower:
            return "Poetic, introspective, and authentic"
        else:
            return "Versatile and engaging"
    
    def get_predicted_genres(self, track_title, artist_name, genre):
        """Get accurate genre predictions based on track and artist."""
        track_lower = track_title.lower()
        artist_lower = artist_name.lower()
        genre_lower = genre.lower()
        
        # Specific artist-based genres
        if "eagles" in artist_lower:
            return ["classic_rock", "soft_rock", "country_rock"]
        elif "queen" in artist_lower:
            return ["progressive_rock", "hard_rock", "art_rock"]
        elif "led zeppelin" in artist_lower:
            return ["hard_rock", "progressive_rock", "blues_rock"]
        elif "guns" in artist_lower:
            return ["hard_rock", "glam_metal", "classic_rock"]
        elif "michael jackson" in artist_lower:
            return ["pop", "dance_pop", "funk"]
        elif "bob dylan" in artist_lower:
            return ["folk_rock", "blues_rock", "protest_song"]
        elif "john lennon" in artist_lower:
            return ["pop", "soft_rock", "protest_song"]
        elif "nirvana" in artist_lower:
            return ["grunge", "alternative_rock", "punk_rock"]
        elif "stevie wonder" in artist_lower:
            return ["funk", "soul", "r&b"]
        elif "aretha franklin" in artist_lower:
            return ["soul", "r&b", "gospel"]
        elif "jimi hendrix" in artist_lower:
            return ["psychedelic_rock", "hard_rock", "blues_rock"]
        elif "beach boys" in artist_lower:
            return ["pop", "surf_rock", "baroque_pop"]
        elif "marvin gaye" in artist_lower:
            return ["soul", "r&b", "protest_song"]
        elif "chuck berry" in artist_lower:
            return ["rock_n_roll", "blues_rock", "classic_rock"]
        elif "beatles" in artist_lower:
            return ["pop", "british_invasion", "rock_n_roll"]
        
        # Genre-based fallback
        if "rock" in genre_lower:
            return ["classic_rock", "hard_rock", "progressive_rock"]
        elif "pop" in genre_lower:
            return ["dance_pop", "synth_pop", "indie_pop"]
        elif "soul" in genre_lower or "funk" in genre_lower:
            return ["soul", "r&b", "funk"]
        elif "folk" in genre_lower:
            return ["folk_rock", "blues_rock", "protest_song"]
        else:
            return [genre_lower, "alternative", "indie"]
    
    def get_listening_context(self, track_title, artist_name, genre):
        """Get accurate listening context based on track and artist."""
        track_lower = track_title.lower()
        artist_lower = artist_name.lower()
        genre_lower = genre.lower()
        
        # Specific track-based contexts
        if "hotel california" in track_lower or "eagles" in artist_lower:
            return "Evening relaxation or road trip vibes"
        elif "bohemian rhapsody" in track_lower or "queen" in artist_lower:
            return "Party atmosphere or dramatic listening"
        elif "stairway to heaven" in track_lower or "led zeppelin" in artist_lower:
            return "Deep listening or spiritual experience"
        elif "sweet child" in track_lower or "guns" in artist_lower:
            return "High-energy activities or driving"
        elif "billie jean" in track_lower or "michael jackson" in artist_lower:
            return "Dancing or party atmosphere"
        elif "imagine" in track_lower or "john lennon" in artist_lower:
            return "Meditation or peaceful reflection"
        elif "smells like teen spirit" in track_lower or "nirvana" in artist_lower:
            return "High-energy activities or teenage rebellion"
        elif "superstition" in track_lower or "stevie wonder" in artist_lower:
            return "Dancing or funky vibes"
        elif "respect" in track_lower or "aretha franklin" in artist_lower:
            return "Empowerment or confidence boost"
        elif "purple haze" in track_lower or "jimi hendrix" in artist_lower:
            return "Psychedelic experience or experimental listening"
        elif "good vibrations" in track_lower or "beach boys" in artist_lower:
            return "Summer vibes or feel-good moments"
        elif "what's going on" in track_lower or "marvin gaye" in artist_lower:
            return "Reflective listening or social awareness"
        elif "johnny b. goode" in track_lower or "chuck berry" in artist_lower:
            return "Dancing or rock 'n' roll celebration"
        elif "i want to hold your hand" in track_lower or "beatles" in artist_lower:
            return "Romantic moments or nostalgic listening"
        elif "like a rolling stone" in track_lower or "bob dylan" in artist_lower:
            return "Reflective listening or cultural appreciation"
        
        # Genre-based fallback
        if "rock" in genre_lower:
            return "High-energy activities or driving"
        elif "pop" in genre_lower:
            return "Casual listening or party atmosphere"
        elif "soul" in genre_lower or "funk" in genre_lower:
            return "Dancing or soulful vibes"
        elif "folk" in genre_lower:
            return "Reflective listening or cultural appreciation"
        else:
            return "Casual listening during daily activities"
    
    def get_similar_tracks(self, track_title, artist_name, genre):
        """Get accurate similar tracks based on actual artist and track."""
        track_lower = track_title.lower()
        artist_lower = artist_name.lower()
        genre_lower = genre.lower()
        
        # Specific artist-based recommendations
        if "eagles" in artist_lower:
            return ["Take It Easy", "Desperado", "One of These Nights", "Lyin' Eyes", "New Kid in Town"]
        elif "queen" in artist_lower:
            return ["We Will Rock You", "Another One Bites the Dust", "Somebody to Love", "Killer Queen", "Don't Stop Me Now"]
        elif "led zeppelin" in artist_lower:
            return ["Whole Lotta Love", "Black Dog", "Kashmir", "Rock and Roll", "Immigrant Song"]
        elif "guns" in artist_lower:
            return ["November Rain", "Paradise City", "Welcome to the Jungle", "Patience", "Estranged"]
        elif "michael jackson" in artist_lower:
            return ["Beat It", "Thriller", "Smooth Criminal", "Man in the Mirror", "Billie Jean"]
        elif "bob dylan" in artist_lower:
            return ["Blowin' in the Wind", "The Times They Are A-Changin'", "Mr. Tambourine Man", "Like a Rolling Stone", "Knockin' on Heaven's Door"]
        elif "john lennon" in artist_lower:
            return ["Give Peace a Chance", "Working Class Hero", "Instant Karma", "Imagine", "Jealous Guy"]
        elif "nirvana" in artist_lower:
            return ["Come As You Are", "Lithium", "In Bloom", "About a Girl", "All Apologies"]
        elif "stevie wonder" in artist_lower:
            return ["Higher Ground", "Living for the City", "Sir Duke", "Superstition", "Isn't She Lovely"]
        elif "aretha franklin" in artist_lower:
            return ["Think", "Natural Woman", "Chain of Fools", "Respect", "I Say a Little Prayer"]
        elif "jimi hendrix" in artist_lower:
            return ["All Along the Watchtower", "Voodoo Child", "Foxy Lady", "Purple Haze", "Hey Joe"]
        elif "beach boys" in artist_lower:
            return ["God Only Knows", "Wouldn't It Be Nice", "California Girls", "Good Vibrations", "Surfin' USA"]
        elif "marvin gaye" in artist_lower:
            return ["Mercy Mercy Me", "Inner City Blues", "Let's Get It On", "What's Going On", "Sexual Healing"]
        elif "chuck berry" in artist_lower:
            return ["Maybellene", "Roll Over Beethoven", "Rock and Roll Music", "Johnny B. Goode", "Sweet Little Sixteen"]
        elif "beatles" in artist_lower:
            return ["She Loves You", "A Hard Day's Night", "Help!", "I Want to Hold Your Hand", "Yesterday"]
        
        # Genre-based fallback
        if "rock" in genre_lower:
            return ["Classic Rock Track 1", "Classic Rock Track 2", "Classic Rock Track 3"]
        elif "pop" in genre_lower:
            return ["Pop Hit 1", "Pop Hit 2", "Pop Hit 3"]
        elif "soul" in genre_lower or "funk" in genre_lower:
            return ["Soul Track 1", "Soul Track 2", "Soul Track 3"]
        elif "folk" in genre_lower:
            return ["Folk Song 1", "Folk Song 2", "Folk Song 3"]
        else:
            return ["Similar Track 1", "Similar Track 2", "Similar Track 3"]
    
    def calculate_confidence(self, track, artist, platform):
        """Calculate realistic confidence based on data completeness."""
        confidence = 0.5  # Base confidence
        
        # Increase confidence for complete data
        if track.get('title') and track.get('artist'):
            confidence += 0.15
        if track.get('genre'):
            confidence += 0.1
        if artist.get('name'):
            confidence += 0.1
        if platform:
            confidence += 0.05
        
        # Bonus for well-known artists (higher confidence for famous artists)
        artist_name = artist.get('name', '').lower()
        famous_artists = [
            'eagles', 'queen', 'led zeppelin', 'guns n roses', 'michael jackson',
            'bob dylan', 'john lennon', 'nirvana', 'stevie wonder', 'aretha franklin',
            'jimi hendrix', 'beach boys', 'marvin gaye', 'chuck berry', 'beatles'
        ]
        
        if any(famous in artist_name for famous in famous_artists):
            confidence += 0.1
        
        # Bonus for complete track information
        if track.get('album') and track.get('release_year'):
            confidence += 0.05
        
        # Cap at 0.95 (never 100% to be realistic)
        return min(confidence, 0.95)
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def run_local_server(port=8000):
    """Run the local HTTP server."""
    handler = LocalEnrichmentHandler
    
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"🎵 Music Event Enrichment Frontend (LOCAL MODE)")
        print(f"🌐 Server running at http://localhost:{port}")
        print(f"📱 Open your browser and navigate to the URL above")
        print(f"🔧 Press Ctrl+C to stop the server")
        print(f"💰 No GCP resources needed - running locally!")
        print(f"=" * 50)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print(f"\n🛑 Server stopped by user")
            httpd.shutdown()

if __name__ == "__main__":
    import sys
    
    # Change to the frontend directory
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Get port from command line or use default
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    
    run_local_server(port) 