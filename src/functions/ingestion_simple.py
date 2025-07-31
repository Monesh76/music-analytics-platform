"""
Simplified Cloud Function for music event data ingestion.
Validates incoming events and publishes to Pub/Sub for stream processing.
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Any

import functions_framework
from google.cloud import pubsub_v1
from pydantic import BaseModel, Field, validator
from enum import Enum


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Pub/Sub publisher
publisher = pubsub_v1.PublisherClient()

# Get environment variables
GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT', 'mystage-claudellm')
RAW_EVENTS_TOPIC = os.getenv('RAW_EVENTS_TOPIC', 'raw-music-events-dev')
ENRICHMENT_TOPIC = os.getenv('ENRICHMENT_TOPIC', 'music-events-enrichment-dev')

# Pub/Sub topic paths
RAW_EVENTS_TOPIC_PATH = publisher.topic_path(GOOGLE_CLOUD_PROJECT, RAW_EVENTS_TOPIC)
ENRICHMENT_TOPIC_PATH = publisher.topic_path(GOOGLE_CLOUD_PROJECT, ENRICHMENT_TOPIC)


# Simplified data models
class EventType(str, Enum):
    PLAY = "play"
    PAUSE = "pause"
    SKIP = "skip"
    LIKE = "like"
    SHARE = "share"


class Platform(str, Enum):
    SPOTIFY = "spotify"
    APPLE_MUSIC = "apple_music"
    YOUTUBE_MUSIC = "youtube_music"
    SOUNDCLOUD = "soundcloud"


class Track(BaseModel):
    id: str = Field(..., description="Unique track identifier")
    title: str = Field(..., description="Track title")
    artist: str = Field(..., description="Artist name")
    album: str = Field(..., description="Album name")
    duration: int = Field(..., description="Track duration in seconds")
    genre: str = Field(..., description="Primary genre")
    release_year: int = Field(..., description="Release year")


class Artist(BaseModel):
    id: str = Field(..., description="Unique artist identifier")
    name: str = Field(..., description="Artist name")
    genre: str = Field(..., description="Primary genre")
    followers: int = Field(..., description="Number of followers")


class UserInteraction(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    session_id: str = Field(..., description="Session identifier")
    timestamp: datetime = Field(..., description="Interaction timestamp")
    location: str = Field(..., description="User location")


class StreamingEvent(BaseModel):
    platform: Platform = Field(..., description="Streaming platform")
    quality: str = Field(..., description="Audio quality")
    bitrate: int = Field(..., description="Audio bitrate")


class MusicEvent(BaseModel):
    event_id: str = Field(..., description="Unique event identifier")
    event_type: EventType = Field(..., description="Type of music event")
    track: Track = Field(..., description="Track information")
    artist: Artist = Field(..., description="Artist information")
    user_interaction: UserInteraction = Field(..., description="User interaction data")
    streaming_event: StreamingEvent = Field(..., description="Streaming platform data")
    timestamp: datetime = Field(..., description="Event timestamp")

    @validator('timestamp', pre=True)
    def parse_timestamp(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v


@functions_framework.http
def ingest_music_event(request) -> tuple[str, int]:
    """
    HTTP Cloud Function to ingest music events.
    
    Expected payload format:
    {
        "event_id": "evt_123",
        "event_type": "play",
        "track": {...},
        "artist": {...},
        "user_interaction": {...},
        "streaming_event": {...},
        "timestamp": "2024-01-15T10:30:00Z"
    }
    
    Returns:
        Tuple of (response_message, status_code)
    """
    
    # Enable CORS for web applications
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)
    
    headers = {'Access-Control-Allow-Origin': '*'}
    
    try:
        # Validate request method
        if request.method != 'POST':
            return ('Method not allowed', 405, headers)
        
        # Parse request data
        request_json = request.get_json(silent=True)
        if not request_json:
            logger.error("No JSON data provided in request")
            return ('Invalid JSON data', 400, headers)
        
        # Validate and create MusicEvent using Pydantic
        try:
            music_event = MusicEvent(**request_json)
            logger.info(f"Successfully validated event: {music_event.event_id}")
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return (f'Data validation failed: {str(e)}', 400, headers)
        
        # Convert to JSON for Pub/Sub
        event_data = music_event.json().encode('utf-8')
        
        # Publish to raw events topic for main pipeline
        future_raw = publisher.publish(
            RAW_EVENTS_TOPIC_PATH,
            event_data,
            event_type=music_event.event_type.value,
            platform=music_event.streaming_event.platform.value,
            timestamp=music_event.timestamp.isoformat()
        )
        
        # Publish to enrichment topic for Claude LLM processing
        future_enrichment = publisher.publish(
            ENRICHMENT_TOPIC_PATH,
            event_data,
            event_type=music_event.event_type.value,
            platform=music_event.streaming_event.platform.value,
            timestamp=music_event.timestamp.isoformat()
        )
        
        # Wait for publish to complete
        raw_message_id = future_raw.result()
        enrichment_message_id = future_enrichment.result()
        
        logger.info(f"Event {music_event.event_id} published successfully")
        logger.info(f"Raw topic message ID: {raw_message_id}")
        logger.info(f"Enrichment topic message ID: {enrichment_message_id}")
        
        return (json.dumps({
            "status": "success",
            "event_id": music_event.event_id,
            "message": "Event ingested successfully",
            "raw_message_id": raw_message_id,
            "enrichment_message_id": enrichment_message_id
        }), 200, headers)
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return (json.dumps({
            "status": "error",
            "message": f"Internal server error: {str(e)}"
        }), 500, headers)


@functions_framework.http  
def health_check(request) -> tuple[str, int]:
    """Health check endpoint for the Cloud Function."""
    headers = {'Access-Control-Allow-Origin': '*'}
    
    if request.method == 'OPTIONS':
        headers.update({
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        })
        return ('', 204, headers)
    
    return (json.dumps({
        "status": "healthy",
        "service": "music-event-ingestion",
        "timestamp": datetime.utcnow().isoformat()
    }), 200, headers) 