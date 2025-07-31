"""Pydantic models for music data aggregation pipeline."""

from .music_events import (
    MusicEvent,
    Artist,
    Track,
    Album,
    PlayEvent,
    StreamingEvent,
    UserInteraction,
    EnrichedMusicEvent,
)

__all__ = [
    "MusicEvent",
    "Artist",
    "Track",
    "Album", 
    "PlayEvent",
    "StreamingEvent",
    "UserInteraction",
    "EnrichedMusicEvent",
] 