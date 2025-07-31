#!/usr/bin/env python3
"""
Sample Music Event Data Generator
Generates realistic sample music events for testing the pipeline.
"""

import json
import random
import argparse
from datetime import datetime, timedelta
from uuid import uuid4
from typing import List, Dict, Any

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from models.music_events import (
    MusicEvent,
    Artist,
    Track,
    Album,
    PlayEvent,
    StreamingEvent,
    UserInteraction,
    EventType,
    Platform,
    Genre
)


class MusicDataGenerator:
    """Generates realistic sample music event data."""
    
    def __init__(self):
        # Sample data pools
        self.artist_names = [
            "The Midnight Runners", "Cosmic Dreamers", "Electric Pulse", 
            "Soulful Echoes", "Neon Lights", "Gravity Falls", "Urban Waves",
            "Desert Storm", "Ocean Deep", "Mountain High", "City Lights",
            "Rainbow Bridge", "Thunder Road", "Silver Moon", "Golden Hour"
        ]
        
        self.track_names = [
            "Midnight Dance", "Cosmic Journey", "Electric Dreams", "Soul Fire",
            "Neon Nights", "Gravity Pull", "Urban Rhythm", "Desert Wind",
            "Ocean Waves", "Mountain Climb", "City Beats", "Rainbow Colors",
            "Thunder Strike", "Moonlight Serenade", "Golden Memories",
            "Starlight Express", "Velvet Touch", "Crystal Clear", "Fire Dance",
            "Ice Cold", "Smooth Operator", "Wild Heart", "Free Spirit"
        ]
        
        self.album_names = [
            "First Light", "Dark Matter", "Electric Symphony", "Soul Collection",
            "Neon Dreams", "Zero Gravity", "Urban Stories", "Desert Tales",
            "Deep Blue", "Peak Experience", "Metropolitan", "Spectrum",
            "Storm Front", "Lunar Cycle", "Golden Age"
        ]
        
        self.user_locations = ["US", "UK", "DE", "FR", "CA", "AU", "JP", "BR", "IN", "MX"]
        self.device_types = ["mobile", "desktop", "tablet", "smart_speaker", "car_system"]
        self.subscription_types = ["free", "premium", "family", "student"]
        self.age_groups = ["13-17", "18-24", "25-34", "35-44", "45-54", "55+"]
        self.stream_qualities = ["low", "medium", "high", "lossless"]
        
        # Cached data
        self.generated_artists: List[Artist] = []
        self.generated_tracks: List[Track] = []
        self.generated_albums: List[Album] = []
        self.generated_users: List[str] = []
    
    def generate_artists(self, count: int = 50) -> List[Artist]:
        """Generate sample artists."""
        artists = []
        
        for i in range(count):
            artist = Artist(
                id=f"artist-{i+1:03d}",
                name=random.choice(self.artist_names) + f" {i+1}",
                genres=random.sample(list(Genre), k=random.randint(1, 3)),
                followers=random.randint(1000, 5000000),
                verified=random.choice([True, False]),
                country=random.choice(self.user_locations)
            )
            artists.append(artist)
        
        self.generated_artists = artists
        return artists
    
    def generate_albums(self, artists: List[Artist], count: int = 100) -> List[Album]:
        """Generate sample albums."""
        albums = []
        
        for i in range(count):
            artist = random.choice(artists)
            album = Album(
                id=f"album-{i+1:03d}",
                name=random.choice(self.album_names) + f" {i+1}",
                artist_id=artist.id,
                release_date=datetime.now() - timedelta(days=random.randint(0, 3650)),
                track_count=random.randint(8, 20),
                genres=artist.genres[:random.randint(1, len(artist.genres))]
            )
            albums.append(album)
        
        self.generated_albums = albums
        return albums
    
    def generate_tracks(self, artists: List[Artist], albums: List[Album], count: int = 500) -> List[Track]:
        """Generate sample tracks."""
        tracks = []
        
        for i in range(count):
            artist = random.choice(artists)
            album = random.choice([a for a in albums if a.artist_id == artist.id]) if albums else None
            
            track = Track(
                id=f"track-{i+1:04d}",
                name=random.choice(self.track_names) + f" {i+1}",
                artist_id=artist.id,
                album_id=album.id if album else None,
                duration_ms=random.randint(120000, 420000),  # 2-7 minutes
                explicit=random.choice([True, False]),
                popularity=random.randint(0, 100),
                energy=round(random.uniform(0.0, 1.0), 3),
                valence=round(random.uniform(0.0, 1.0), 3),
                tempo=round(random.uniform(60.0, 200.0), 1),
                genres=artist.genres[:random.randint(1, len(artist.genres))]
            )
            tracks.append(track)
        
        self.generated_tracks = tracks
        return tracks
    
    def generate_users(self, count: int = 1000) -> List[str]:
        """Generate sample user IDs."""
        users = [f"user-{i+1:04d}" for i in range(count)]
        self.generated_users = users
        return users
    
    def generate_music_event(self) -> MusicEvent:
        """Generate a single realistic music event."""
        
        # Ensure we have sample data
        if not self.generated_artists:
            self.generate_artists()
        if not self.generated_tracks:
            self.generate_tracks(self.generated_artists, self.generated_albums)
        if not self.generated_albums:
            self.generate_albums(self.generated_artists)
        if not self.generated_users:
            self.generate_users()
        
        # Select random data
        track = random.choice(self.generated_tracks)
        artist = next((a for a in self.generated_artists if a.id == track.artist_id), self.generated_artists[0])
        album = next((a for a in self.generated_albums if a.id == track.album_id), None)
        user_id = random.choice(self.generated_users)
        
        # Generate event type with realistic distribution
        event_type = random.choices(
            [EventType.PLAY, EventType.SKIP, EventType.LIKE, EventType.SHARE, EventType.PLAYLIST_ADD],
            weights=[70, 20, 5, 3, 2]  # Play events are most common
        )[0]
        
        # User interaction
        user_interaction = UserInteraction(
            user_id=user_id,
            session_id=f"session-{random.randint(1, 10000):06d}",
            device_type=random.choice(self.device_types),
            location=random.choice(self.user_locations),
            subscription_type=random.choice(self.subscription_types),
            user_age_group=random.choice(self.age_groups)
        )
        
        # Streaming event
        streaming_event = StreamingEvent(
            platform=random.choice(list(Platform)),
            stream_quality=random.choice(self.stream_qualities),
            bandwidth_kbps=random.choice([128, 192, 256, 320]),
            buffer_events=random.randint(0, 3)
        )
        
        # Play event (if applicable)
        play_event = None
        if event_type == EventType.PLAY:
            # Realistic play duration based on track length
            max_duration = track.duration_ms if track.duration_ms else 180000
            completion_ratio = random.betavariate(2, 2)  # Bell curve around 0.5
            played_duration = int(max_duration * completion_ratio)
            
            play_event = PlayEvent(
                played_duration_ms=played_duration,
                skip_reason="user_action" if completion_ratio < 0.3 else None,
                playlist_id=f"playlist-{random.randint(1, 100):03d}" if random.random() < 0.7 else None,
                shuffle_mode=random.choice([True, False]),
                repeat_mode=random.choices(["off", "track", "context"], weights=[70, 20, 10])[0]
            )
        
        # Create the event
        event = MusicEvent(
            event_type=event_type,
            timestamp=datetime.now() - timedelta(seconds=random.randint(0, 3600)),  # Within last hour
            track=track,
            artist=artist,
            album=album,
            user_interaction=user_interaction,
            streaming_event=streaming_event,
            play_event=play_event
        )
        
        return event
    
    def generate_events(self, count: int = 100) -> List[MusicEvent]:
        """Generate multiple music events."""
        events = []
        
        for _ in range(count):
            try:
                event = self.generate_music_event()
                events.append(event)
            except Exception as e:
                print(f"Error generating event: {e}")
                continue
        
        return events
    
    def save_events_json(self, events: List[MusicEvent], filename: str) -> None:
        """Save events to JSON file."""
        event_dicts = [json.loads(event.json()) for event in events]
        
        with open(filename, 'w') as f:
            json.dump(event_dicts, f, indent=2, default=str)
        
        print(f"Saved {len(events)} events to {filename}")


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description="Generate sample music event data")
    parser.add_argument("--count", "-c", type=int, default=100, help="Number of events to generate")
    parser.add_argument("--output", "-o", type=str, default="sample_events.json", help="Output filename")
    parser.add_argument("--artists", type=int, default=50, help="Number of artists to generate")
    parser.add_argument("--tracks", type=int, default=500, help="Number of tracks to generate")
    parser.add_argument("--users", type=int, default=1000, help="Number of users to generate")
    
    args = parser.parse_args()
    
    print(f"Generating {args.count} sample music events...")
    
    generator = MusicDataGenerator()
    
    # Generate base data
    print(f"Creating {args.artists} artists...")
    artists = generator.generate_artists(args.artists)
    
    print(f"Creating {args.artists * 2} albums...")
    albums = generator.generate_albums(artists, args.artists * 2)
    
    print(f"Creating {args.tracks} tracks...")
    tracks = generator.generate_tracks(artists, albums, args.tracks)
    
    print(f"Creating {args.users} users...")
    users = generator.generate_users(args.users)
    
    # Generate events
    print(f"Generating {args.count} events...")
    events = generator.generate_events(args.count)
    
    # Save to file
    generator.save_events_json(events, args.output)
    
    print(f"Generated {len(events)} valid events")
    print(f"Sample event preview:")
    if events:
        sample_event = events[0]
        print(f"  Event Type: {sample_event.event_type.value}")
        print(f"  Track: {sample_event.track.name}")
        print(f"  Artist: {sample_event.artist.name}")
        print(f"  Platform: {sample_event.streaming_event.platform.value}")
        print(f"  User: {sample_event.user_interaction.user_id}")


if __name__ == "__main__":
    main() 