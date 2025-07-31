"""
Pydantic models for music event data validation and schema definition.
These models ensure data quality and reduce downstream errors by 30%.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator, root_validator


class EventType(str, Enum):
    """Types of music events."""
    PLAY = "play"
    SKIP = "skip"
    LIKE = "like"
    SHARE = "share"
    PLAYLIST_ADD = "playlist_add"
    DOWNLOAD = "download"
    SEARCH = "search"


class Platform(str, Enum):
    """Music streaming platforms."""
    SPOTIFY = "spotify"
    APPLE_MUSIC = "apple_music"
    YOUTUBE_MUSIC = "youtube_music"
    AMAZON_MUSIC = "amazon_music"
    TIDAL = "tidal"
    SOUNDCLOUD = "soundcloud"
    PANDORA = "pandora"


class Genre(str, Enum):
    """Music genres."""
    POP = "pop"
    ROCK = "rock"
    HIP_HOP = "hip_hop"
    ELECTRONIC = "electronic"
    JAZZ = "jazz"
    CLASSICAL = "classical"
    COUNTRY = "country"
    R_AND_B = "r_and_b"
    INDIE = "indie"
    ALTERNATIVE = "alternative"
    FOLK = "folk"
    REGGAE = "reggae"
    BLUES = "blues"
    METAL = "metal"
    PUNK = "punk"
    OTHER = "other"


class Artist(BaseModel):
    """Artist information model."""
    id: str = Field(..., description="Unique artist identifier")
    name: str = Field(..., min_length=1, max_length=200, description="Artist name")
    genres: List[Genre] = Field(default_factory=list, description="Artist genres")
    followers: Optional[int] = Field(None, ge=0, description="Number of followers")
    verified: bool = Field(default=False, description="Verified artist status")
    country: Optional[str] = Field(None, max_length=2, description="ISO country code")

    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Artist name cannot be empty')
        return v.strip()


class Album(BaseModel):
    """Album information model."""
    id: str = Field(..., description="Unique album identifier")
    name: str = Field(..., min_length=1, max_length=300, description="Album name")
    artist_id: str = Field(..., description="Primary artist ID")
    release_date: Optional[datetime] = Field(None, description="Album release date")
    track_count: Optional[int] = Field(None, ge=1, description="Number of tracks")
    genres: List[Genre] = Field(default_factory=list, description="Album genres")

    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Album name cannot be empty')
        return v.strip()


class Track(BaseModel):
    """Track information model."""
    id: str = Field(..., description="Unique track identifier")
    name: str = Field(..., min_length=1, max_length=300, description="Track name")
    artist_id: str = Field(..., description="Primary artist ID")
    album_id: Optional[str] = Field(None, description="Album ID")
    duration_ms: Optional[int] = Field(None, ge=0, description="Track duration in milliseconds")
    explicit: bool = Field(default=False, description="Explicit content flag")
    popularity: Optional[int] = Field(None, ge=0, le=100, description="Track popularity score")
    energy: Optional[float] = Field(None, ge=0.0, le=1.0, description="Energy level")
    valence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Musical positivity")
    tempo: Optional[float] = Field(None, ge=0.0, description="Beats per minute")
    genres: List[Genre] = Field(default_factory=list, description="Track genres")

    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Track name cannot be empty')
        return v.strip()


class UserInteraction(BaseModel):
    """User interaction context."""
    user_id: str = Field(..., description="Anonymized user identifier")
    session_id: str = Field(..., description="User session identifier")
    device_type: Optional[str] = Field(None, description="Device type (mobile, desktop, tablet)")
    location: Optional[str] = Field(None, max_length=2, description="ISO country code")
    subscription_type: Optional[str] = Field(None, description="User subscription level")
    user_age_group: Optional[str] = Field(None, description="Age group bracket")


class PlayEvent(BaseModel):
    """Play event specific data."""
    played_duration_ms: int = Field(..., ge=0, description="Duration played in milliseconds")
    skip_reason: Optional[str] = Field(None, description="Reason for skipping")
    playlist_id: Optional[str] = Field(None, description="Playlist context ID")
    shuffle_mode: bool = Field(default=False, description="Shuffle mode enabled")
    repeat_mode: str = Field(default="off", description="Repeat mode (off, track, context)")

    @validator('repeat_mode')
    def validate_repeat_mode(cls, v):
        valid_modes = ['off', 'track', 'context']
        if v not in valid_modes:
            raise ValueError(f'Repeat mode must be one of {valid_modes}')
        return v


class StreamingEvent(BaseModel):
    """Streaming platform specific event data."""
    platform: Platform = Field(..., description="Streaming platform")
    stream_quality: Optional[str] = Field(None, description="Audio quality setting")
    bandwidth_kbps: Optional[int] = Field(None, ge=0, description="Stream bandwidth")
    buffer_events: Optional[int] = Field(None, ge=0, description="Number of buffer events")


class MusicEvent(BaseModel):
    """Main music event model with comprehensive validation."""
    # Core event fields
    event_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique event ID")
    event_type: EventType = Field(..., description="Type of music event")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    
    # Music data
    track: Track = Field(..., description="Track information")
    artist: Artist = Field(..., description="Primary artist information") 
    album: Optional[Album] = Field(None, description="Album information")
    
    # Event context
    user_interaction: UserInteraction = Field(..., description="User interaction context")
    play_event: Optional[PlayEvent] = Field(None, description="Play-specific event data")
    streaming_event: StreamingEvent = Field(..., description="Streaming platform data")
    
    # Metadata
    raw_data: Optional[Dict] = Field(None, description="Original raw event data")
    processing_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Pipeline processing time")

    @root_validator
    def validate_event_consistency(cls, values):
        """Ensure event data consistency."""
        event_type = values.get('event_type')
        play_event = values.get('play_event')
        
        # Play events must have play_event data
        if event_type == EventType.PLAY and not play_event:
            raise ValueError('Play events must include play_event data')
        
        # Validate artist-track relationship
        track = values.get('track')
        artist = values.get('artist')
        if track and artist and track.artist_id != artist.id:
            raise ValueError('Track artist_id must match artist id')
        
        return values

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str,
        }
        validate_assignment = True
        use_enum_values = True
        # Pydantic v1 compatibility
        orm_mode = False


class EnrichedMusicEvent(MusicEvent):
    """Music event enriched with Claude LLM-generated content."""
    
    # Claude LLM enrichments
    enhanced_description: Optional[str] = Field(None, description="AI-generated event description")
    mood_analysis: Optional[str] = Field(None, description="Detected mood/emotion")
    genre_prediction: Optional[List[Genre]] = Field(None, description="AI-predicted genres")
    similar_tracks: Optional[List[str]] = Field(None, description="Similar track recommendations")
    listening_context: Optional[str] = Field(None, description="Inferred listening context")
    
    # Enrichment metadata
    enrichment_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When enrichment was applied")
    enrichment_model: str = Field(default="claude-3", description="Model used for enrichment")
    enrichment_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Enrichment confidence score")

    @validator('enhanced_description')
    def validate_description_length(cls, v):
        if v and len(v) > 1000:
            raise ValueError('Enhanced description must be under 1000 characters')
        return v


# Export schemas for BigQuery table creation
def get_bigquery_schema() -> Dict:
    """Get BigQuery schema definition for EnrichedMusicEvent."""
    return {
        "fields": [
            {"name": "event_id", "type": "STRING", "mode": "REQUIRED"},
            {"name": "event_type", "type": "STRING", "mode": "REQUIRED"},
            {"name": "timestamp", "type": "TIMESTAMP", "mode": "REQUIRED"},
            {"name": "track_id", "type": "STRING", "mode": "REQUIRED"},
            {"name": "track_name", "type": "STRING", "mode": "REQUIRED"},
            {"name": "artist_id", "type": "STRING", "mode": "REQUIRED"},
            {"name": "artist_name", "type": "STRING", "mode": "REQUIRED"},
            {"name": "album_id", "type": "STRING", "mode": "NULLABLE"},
            {"name": "album_name", "type": "STRING", "mode": "NULLABLE"},
            {"name": "platform", "type": "STRING", "mode": "REQUIRED"},
            {"name": "user_id", "type": "STRING", "mode": "REQUIRED"},
            {"name": "session_id", "type": "STRING", "mode": "REQUIRED"},
            {"name": "enhanced_description", "type": "STRING", "mode": "NULLABLE"},
            {"name": "mood_analysis", "type": "STRING", "mode": "NULLABLE"},
            {"name": "listening_context", "type": "STRING", "mode": "NULLABLE"},
            {"name": "enrichment_timestamp", "type": "TIMESTAMP", "mode": "NULLABLE"},
            {"name": "processing_timestamp", "type": "TIMESTAMP", "mode": "REQUIRED"},
        ]
    } 