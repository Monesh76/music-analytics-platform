// Track Data Loader for Music Analytics Platform
class TrackDataLoader {
    constructor() {
        this.tracks = [];
        this.currentTrackIndex = 0;
        this.currentPlatform = null; // Track current platform
        this.platformTracks = {}; // Cache tracks by platform
        this.loadTracks();
    }
    
    async loadTracks() {
        try {
            const response = await fetch('/test_tracks.json');
            const data = await response.json();
            this.tracks = data.test_tracks;
            
            // Group tracks by platform
            this.platformTracks = {
                'spotify': this.tracks.filter(track => track.platform === 'spotify'),
                'apple_music': this.tracks.filter(track => track.platform === 'apple_music'),
                'youtube_music': this.tracks.filter(track => track.platform === 'youtube_music')
            };
            
            console.log(`Loaded ${this.tracks.length} test tracks`);
            console.log(`Spotify: ${this.platformTracks.spotify.length} tracks`);
            console.log(`Apple Music: ${this.platformTracks.apple_music.length} tracks`);
            console.log(`YouTube Music: ${this.platformTracks.youtube_music.length} tracks`);
        } catch (error) {
            console.error('Failed to load test tracks:', error);
            // Fallback to default tracks
            this.tracks = this.getDefaultTracks();
        }
    }
    
    getDefaultTracks() {
        return [
            {
                id: "track_001",
                title: "Hotel California",
                artist: "Eagles",
                album: "Hotel California",
                genre: "rock",
                duration: 391,
                release_year: 1976,
                platform: "spotify",
                expected_mood: "Melancholic, atmospheric, and introspective",
                expected_genres: ["classic_rock", "soft_rock", "country_rock"],
                expected_context: "Evening relaxation or road trip vibes",
                similar_tracks: ["Take It Easy", "Desperado", "One of These Nights"]
            },
            {
                id: "track_002",
                title: "Bohemian Rhapsody",
                artist: "Queen",
                album: "A Night at the Opera",
                genre: "rock",
                duration: 354,
                release_year: 1975,
                platform: "apple_music",
                expected_mood: "Dramatic, theatrical, and emotionally powerful",
                expected_genres: ["progressive_rock", "hard_rock", "art_rock"],
                expected_context: "Party atmosphere or dramatic listening",
                similar_tracks: ["We Will Rock You", "Another One Bites the Dust", "Somebody to Love"]
            }
        ];
    }
    
    getRandomTrack() {
        if (this.tracks.length === 0) return null;
        const randomIndex = Math.floor(Math.random() * this.tracks.length);
        const track = this.tracks[randomIndex];
        this.currentPlatform = track.platform; // Update current platform
        return track;
    }
    
    getNextTrack() {
        // If we have a current platform, get next track from that platform
        if (this.currentPlatform && this.platformTracks[this.currentPlatform]) {
            const platformTracks = this.platformTracks[this.currentPlatform];
            if (platformTracks.length > 0) {
                // Find current track in platform tracks
                const currentTrack = this.tracks[this.currentTrackIndex];
                let currentPlatformIndex = platformTracks.findIndex(t => t.id === currentTrack.id);
                
                // If current track is not in platform tracks, start from beginning
                if (currentPlatformIndex === -1) {
                    currentPlatformIndex = -1;
                }
                
                // Get next track from same platform
                const nextIndex = (currentPlatformIndex + 1) % platformTracks.length;
                const nextTrack = platformTracks[nextIndex];
                
                // Update main track index
                this.currentTrackIndex = this.tracks.findIndex(t => t.id === nextTrack.id);
                return nextTrack;
            }
        }
        
        // Fallback to cycling through all tracks
        if (this.tracks.length === 0) return null;
        const track = this.tracks[this.currentTrackIndex];
        this.currentTrackIndex = (this.currentTrackIndex + 1) % this.tracks.length;
        this.currentPlatform = track.platform; // Update current platform
        return track;
    }
    
    getTrackByGenre(genre) {
        return this.tracks.filter(track => 
            track.genre.toLowerCase().includes(genre.toLowerCase()) ||
            track.expected_genres.some(g => g.toLowerCase().includes(genre.toLowerCase()))
        );
    }
    
    getTrackByArtist(artist) {
        return this.tracks.filter(track => 
            track.artist.toLowerCase().includes(artist.toLowerCase())
        );
    }
    
    getTrackByMood(mood) {
        return this.tracks.filter(track => 
            track.expected_mood.toLowerCase().includes(mood.toLowerCase())
        );
    }
    
    getTrackByPlatform(platform) {
        return this.tracks.filter(track => 
            track.platform === platform
        );
    }
    
    fillFormWithTrack(track) {
        if (!track) return;
        
        console.log(`Filling form with track: ${track.title} by ${track.artist} on ${track.platform}`);
        
        // Update current platform
        this.currentPlatform = track.platform;
        
        // Fill form fields
        const fields = {
            'eventId': `evt_${track.platform}_${Date.now()}`,
            'trackTitle': track.title,
            'artist': track.artist,
            'album': track.album,
            'genre': track.genre,
            'duration': track.duration.toString(),
            'releaseYear': track.release_year.toString(),
            'userId': `user_${track.platform}_${Math.floor(Math.random() * 1000)}`,
            'location': this.getRandomLocation(),
            'bitrate': '320'
        };
        
        // Fill each field
        Object.keys(fields).forEach(key => {
            const element = document.getElementById(key.charAt(0).toLowerCase() + key.slice(1));
            if (element) {
                element.value = fields[key];
            }
        });
        
        // Set platform radio button with better error handling
        console.log(`Setting platform to: ${track.platform}`);
        const platformRadio = document.querySelector(`input[name="platform"][value="${track.platform}"]`);
        if (platformRadio) {
            platformRadio.checked = true;
            console.log(`✅ Successfully set platform to ${track.platform}`);
        } else {
            console.error(`❌ Could not find radio button for platform: ${track.platform}`);
            console.log('Available platform options:', Array.from(document.querySelectorAll('input[name="platform"]')).map(r => r.value));
        }
        
        console.log(`Filled form with: ${track.title} by ${track.artist} on ${track.platform}`);
    }
    
    getRandomLocation() {
        const locations = [
            "San Francisco, CA",
            "New York, NY",
            "Los Angeles, CA",
            "Chicago, IL",
            "Miami, FL",
            "Seattle, WA",
            "Austin, TX",
            "Nashville, TN",
            "Portland, OR",
            "Denver, CO"
        ];
        return locations[Math.floor(Math.random() * locations.length)];
    }
    
    createTrackSelector() {
        const container = document.createElement('div');
        container.className = 'bg-gray-50 rounded-lg p-4 mb-6';
        container.innerHTML = `
            <h3 class="text-lg font-semibold text-gray-800 mb-4">
                <i class="fas fa-music mr-2 text-blue-600"></i>
                Quick Track Selection
            </h3>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Load Random Track</label>
                    <button id="loadRandomBtn" class="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors">
                        <i class="fas fa-random mr-2"></i>Random Track
                    </button>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Load Next Track</label>
                    <button id="loadNextBtn" class="w-full bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition-colors">
                        <i class="fas fa-forward mr-2"></i>Next Track
                    </button>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Spotify Tracks</label>
                    <button id="loadSpotifyBtn" class="w-full bg-green-500 text-white px-4 py-2 rounded-md hover:bg-green-600 transition-colors">
                        <i class="fab fa-spotify mr-2"></i>Spotify
                    </button>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Apple Music Tracks</label>
                    <button id="loadAppleMusicBtn" class="w-full bg-red-500 text-white px-4 py-2 rounded-md hover:bg-red-600 transition-colors">
                        <i class="fab fa-apple mr-2"></i>Apple Music
                    </button>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">YouTube Music Tracks</label>
                    <button id="loadYouTubeMusicBtn" class="w-full bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 transition-colors">
                        <i class="fab fa-youtube mr-2"></i>YouTube Music
                    </button>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Classic Rock</label>
                    <button id="loadClassicRockBtn" class="w-full bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700 transition-colors">
                        <i class="fas fa-guitar mr-2"></i>Classic Rock
                    </button>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Pop Hits</label>
                    <button id="loadPopBtn" class="w-full bg-pink-600 text-white px-4 py-2 rounded-md hover:bg-pink-700 transition-colors">
                        <i class="fas fa-star mr-2"></i>Pop Hits
                    </button>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Soul & Funk</label>
                    <button id="loadSoulBtn" class="w-full bg-orange-600 text-white px-4 py-2 rounded-md hover:bg-orange-700 transition-colors">
                        <i class="fas fa-heart mr-2"></i>Soul & Funk
                    </button>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Clear Form</label>
                    <button id="clearFormBtn" class="w-full bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 transition-colors">
                        <i class="fas fa-eraser mr-2"></i>Clear Form
                    </button>
                </div>
            </div>
        `;
        
        // Add event listeners
        container.querySelector('#loadRandomBtn').addEventListener('click', () => {
            const track = this.getRandomTrack();
            this.fillFormWithTrack(track);
        });
        
        container.querySelector('#loadNextBtn').addEventListener('click', () => {
            const track = this.getNextTrack();
            this.fillFormWithTrack(track);
        });
        
        container.querySelector('#loadSpotifyBtn').addEventListener('click', () => {
            const tracks = this.getTrackByPlatform('spotify');
            if (tracks.length > 0) {
                const randomTrack = tracks[Math.floor(Math.random() * tracks.length)];
                this.fillFormWithTrack(randomTrack);
            }
        });
        
        container.querySelector('#loadAppleMusicBtn').addEventListener('click', () => {
            const tracks = this.getTrackByPlatform('apple_music');
            if (tracks.length > 0) {
                const randomTrack = tracks[Math.floor(Math.random() * tracks.length)];
                this.fillFormWithTrack(randomTrack);
            }
        });
        
        container.querySelector('#loadYouTubeMusicBtn').addEventListener('click', () => {
            const tracks = this.getTrackByPlatform('youtube_music');
            if (tracks.length > 0) {
                const randomTrack = tracks[Math.floor(Math.random() * tracks.length)];
                this.fillFormWithTrack(randomTrack);
            }
        });
        
        container.querySelector('#loadClassicRockBtn').addEventListener('click', () => {
            const tracks = this.getTrackByGenre('rock');
            if (tracks.length > 0) {
                const randomTrack = tracks[Math.floor(Math.random() * tracks.length)];
                this.fillFormWithTrack(randomTrack);
            }
        });
        
        container.querySelector('#loadPopBtn').addEventListener('click', () => {
            const tracks = this.getTrackByGenre('pop');
            if (tracks.length > 0) {
                const randomTrack = tracks[Math.floor(Math.random() * tracks.length)];
                this.fillFormWithTrack(randomTrack);
            }
        });
        
        container.querySelector('#loadSoulBtn').addEventListener('click', () => {
            const tracks = this.getTrackByGenre('soul');
            if (tracks.length > 0) {
                const randomTrack = tracks[Math.floor(Math.random() * tracks.length)];
                this.fillFormWithTrack(randomTrack);
            }
        });
        
        container.querySelector('#clearFormBtn').addEventListener('click', () => {
            document.getElementById('enrichmentForm').reset();
            this.currentPlatform = null; // Reset platform when clearing form
        });
        
        return container;
    }
}

// Initialize track loader when page loads
let trackLoader;
document.addEventListener('DOMContentLoaded', () => {
    trackLoader = new TrackDataLoader();
    
    // Add track selector to the form
    const form = document.getElementById('enrichmentForm');
    if (form) {
        const trackSelector = trackLoader.createTrackSelector();
        form.insertBefore(trackSelector, form.firstChild);
    }
}); 