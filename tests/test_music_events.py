"""
Unit tests for music event models and pipeline components.
"""

import pytest
from datetime import datetime
from uuid import uuid4

from src.models.music_events import (
    MusicEvent,
    EnrichedMusicEvent,
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


class TestMusicEventModels:
    """Test cases for Pydantic music event models."""
    
    @pytest.fixture
    def sample_artist(self):
        """Sample artist data."""
        return Artist(
            id="artist-001",
            name="Test Artist",
            genres=[Genre.POP, Genre.ROCK],
            followers=100000,
            verified=True,
            country="US"
        )
    
    @pytest.fixture
    def sample_track(self):
        """Sample track data."""
        return Track(
            id="track-001",
            name="Test Song",
            artist_id="artist-001",
            duration_ms=210000,
            explicit=False,
            popularity=75,
            energy=0.8,
            valence=0.6,
            tempo=120.0,
            genres=[Genre.POP]
        )
    
    @pytest.fixture
    def sample_album(self):
        """Sample album data."""
        return Album(
            id="album-001",
            name="Test Album",
            artist_id="artist-001",
            release_date=datetime(2023, 1, 15),
            track_count=12,
            genres=[Genre.POP]
        )
    
    @pytest.fixture
    def sample_user_interaction(self):
        """Sample user interaction data."""
        return UserInteraction(
            user_id="user-001",
            session_id="session-001",
            device_type="mobile",
            location="US",
            subscription_type="premium",
            user_age_group="25-34"
        )
    
    @pytest.fixture
    def sample_streaming_event(self):
        """Sample streaming event data."""
        return StreamingEvent(
            platform=Platform.SPOTIFY,
            stream_quality="high",
            bandwidth_kbps=320,
            buffer_events=0
        )
    
    @pytest.fixture
    def sample_play_event(self):
        """Sample play event data."""
        return PlayEvent(
            played_duration_ms=180000,
            skip_reason=None,
            playlist_id="playlist-001",
            shuffle_mode=False,
            repeat_mode="off"
        )
    
    def test_artist_creation(self, sample_artist):
        """Test artist model creation and validation."""
        assert sample_artist.id == "artist-001"
        assert sample_artist.name == "Test Artist"
        assert Genre.POP in sample_artist.genres
        assert sample_artist.verified is True
    
    def test_artist_name_validation(self):
        """Test artist name validation."""
        # Valid name
        artist = Artist(id="test", name="Valid Name")
        assert artist.name == "Valid Name"
        
        # Name with extra whitespace
        artist = Artist(id="test", name="  Trimmed Name  ")
        assert artist.name == "Trimmed Name"
        
        # Empty name should raise error
        with pytest.raises(ValueError):
            Artist(id="test", name="")
    
    def test_track_creation(self, sample_track):
        """Test track model creation."""
        assert sample_track.id == "track-001"
        assert sample_track.duration_ms == 210000
        assert sample_track.energy == 0.8
        assert sample_track.valence == 0.6
    
    def test_track_validation(self):
        """Test track validation rules."""
        # Valid track
        track = Track(id="test", name="Test Song", artist_id="artist-1")
        assert track.name == "Test Song"
        
        # Invalid popularity range
        with pytest.raises(ValueError):
            Track(id="test", name="Test", artist_id="artist-1", popularity=150)
    
    def test_music_event_creation(
        self,
        sample_artist,
        sample_track,
        sample_user_interaction,
        sample_streaming_event,
        sample_play_event
    ):
        """Test music event creation with all components."""
        event = MusicEvent(
            event_type=EventType.PLAY,
            track=sample_track,
            artist=sample_artist,
            user_interaction=sample_user_interaction,
            streaming_event=sample_streaming_event,
            play_event=sample_play_event
        )
        
        assert event.event_type == EventType.PLAY
        assert event.track.name == "Test Song"
        assert event.artist.name == "Test Artist"
        assert event.event_id is not None  # Auto-generated UUID
    
    def test_music_event_validation(
        self,
        sample_artist,
        sample_track,
        sample_user_interaction,
        sample_streaming_event
    ):
        """Test music event validation rules."""
        # Play event without play_event data should fail
        with pytest.raises(ValueError, match="Play events must include play_event data"):
            MusicEvent(
                event_type=EventType.PLAY,
                track=sample_track,
                artist=sample_artist,
                user_interaction=sample_user_interaction,
                streaming_event=sample_streaming_event
                # Missing play_event
            )
    
    def test_artist_track_consistency(
        self,
        sample_artist,
        sample_user_interaction,
        sample_streaming_event
    ):
        """Test artist-track ID consistency validation."""
        # Mismatched artist-track IDs should fail
        track = Track(id="track-001", name="Test", artist_id="different-artist")
        
        with pytest.raises(ValueError, match="Track artist_id must match artist id"):
            MusicEvent(
                event_type=EventType.LIKE,
                track=track,
                artist=sample_artist,  # artist.id = "artist-001"
                user_interaction=sample_user_interaction,
                streaming_event=sample_streaming_event
            )
    
    def test_enriched_music_event(
        self,
        sample_artist,
        sample_track,
        sample_user_interaction,
        sample_streaming_event,
        sample_play_event
    ):
        """Test enriched music event creation."""
        base_event = MusicEvent(
            event_type=EventType.PLAY,
            track=sample_track,
            artist=sample_artist,
            user_interaction=sample_user_interaction,
            streaming_event=sample_streaming_event,
            play_event=sample_play_event
        )
        
        enriched_event = EnrichedMusicEvent(
            **base_event.dict(),
            enhanced_description="Energetic pop track with high engagement",
            mood_analysis="upbeat",
            genre_prediction=[Genre.ELECTRONIC, Genre.DANCE],
            similar_tracks=["Artist2 - Similar Song", "Artist3 - Another Track"],
            listening_context="workout",
            enrichment_confidence=0.85
        )
        
        assert enriched_event.enhanced_description is not None
        assert enriched_event.mood_analysis == "upbeat"
        assert Genre.ELECTRONIC in enriched_event.genre_prediction
        assert enriched_event.enrichment_confidence == 0.85
    
    def test_enhanced_description_length_validation(
        self,
        sample_artist,
        sample_track,
        sample_user_interaction,
        sample_streaming_event
    ):
        """Test enhanced description length validation."""
        base_event = MusicEvent(
            event_type=EventType.LIKE,
            track=sample_track,
            artist=sample_artist,
            user_interaction=sample_user_interaction,
            streaming_event=sample_streaming_event
        )
        
        # Description too long should fail
        long_description = "x" * 1001
        
        with pytest.raises(ValueError, match="Enhanced description must be under 1000 characters"):
            EnrichedMusicEvent(
                **base_event.dict(),
                enhanced_description=long_description
            )
    
    def test_play_event_repeat_mode_validation(self):
        """Test play event repeat mode validation."""
        # Valid repeat modes
        for mode in ["off", "track", "context"]:
            play_event = PlayEvent(played_duration_ms=1000, repeat_mode=mode)
            assert play_event.repeat_mode == mode
        
        # Invalid repeat mode
        with pytest.raises(ValueError):
            PlayEvent(played_duration_ms=1000, repeat_mode="invalid")
    
    def test_json_serialization(
        self,
        sample_artist,
        sample_track,
        sample_user_interaction,
        sample_streaming_event,
        sample_play_event
    ):
        """Test JSON serialization of music events."""
        event = MusicEvent(
            event_type=EventType.PLAY,
            track=sample_track,
            artist=sample_artist,
            user_interaction=sample_user_interaction,
            streaming_event=sample_streaming_event,
            play_event=sample_play_event
        )
        
        # Should serialize to JSON without errors
        json_data = event.json()
        assert isinstance(json_data, str)
        assert "event_type" in json_data
        assert "play" in json_data
    
    def test_enum_values(self):
        """Test enum value usage."""
        # EventType enum
        assert EventType.PLAY.value == "play"
        assert EventType.SKIP.value == "skip"
        
        # Platform enum
        assert Platform.SPOTIFY.value == "spotify"
        assert Platform.APPLE_MUSIC.value == "apple_music"
        
        # Genre enum
        assert Genre.POP.value == "pop"
        assert Genre.HIP_HOP.value == "hip_hop"


class TestBigQuerySchema:
    """Test BigQuery schema generation."""
    
    def test_bigquery_schema_generation(self):
        """Test BigQuery schema generation function."""
        from src.models.music_events import get_bigquery_schema
        
        schema = get_bigquery_schema()
        
        assert "fields" in schema
        assert len(schema["fields"]) > 0
        
        # Check for required fields
        field_names = [field["name"] for field in schema["fields"]]
        required_fields = [
            "event_id",
            "event_type", 
            "timestamp",
            "track_id",
            "artist_id",
            "platform",
            "user_id"
        ]
        
        for field in required_fields:
            assert field in field_names, f"Required field {field} not found in schema"


if __name__ == "__main__":
    pytest.main([__file__]) 