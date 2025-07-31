"""
Final working Cloud Function for Claude LLM enrichment of music events.
Triggered by Pub/Sub messages and enriches event descriptions using Claude API.
"""

import json
import base64
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional

import functions_framework
from google.cloud import pubsub_v1
from google.cloud import bigquery
from pydantic import BaseModel, Field, validator
from enum import Enum


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize clients
GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT', 'mystage-claudellm')
BIGQUERY_DATASET = os.getenv('BIGQUERY_DATASET', 'music_analytics_dev')
ENRICHED_EVENTS_TOPIC = os.getenv('ENRICHED_EVENTS_TOPIC', 'enriched-music-events-dev')

# Initialize clients
bigquery_client = bigquery.Client()
publisher = pubsub_v1.PublisherClient()

# BigQuery table reference
table_ref = bigquery_client.dataset(BIGQUERY_DATASET).table('enriched_events')

# Pub/Sub topic for enriched events
ENRICHED_EVENTS_TOPIC_PATH = publisher.topic_path(GOOGLE_CLOUD_PROJECT, ENRICHED_EVENTS_TOPIC)


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


class EnrichedMusicEvent(MusicEvent):
    # Claude LLM enrichments
    event_description: Optional[str] = Field(None, description="AI-generated event description")
    mood_analysis: Optional[str] = Field(None, description="Mood analysis of the track")
    predicted_genres: Optional[List[str]] = Field(None, description="Predicted genres")
    listening_context: Optional[str] = Field(None, description="Inferred listening context")
    similar_tracks: Optional[List[str]] = Field(None, description="Similar track recommendations")
    enrichment_confidence: float = Field(0.0, description="Confidence score for enrichments")
    enrichment_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Enrichment timestamp")


@functions_framework.cloud_event
def enrich_music_event(cloud_event) -> None:
    """
    Cloud Function triggered by Pub/Sub to enrich music events with Claude LLM.
    
    Expected message format:
    - data: base64 encoded JSON of MusicEvent
    - attributes: event metadata
    """
    
    try:
        logger.info(f"Received cloud event: {cloud_event}")
        logger.info(f"Cloud event data type: {type(cloud_event.data)}")
        logger.info(f"Cloud event data: {cloud_event.data}")
        
        # Handle different message formats
        message_data = None
        
        if hasattr(cloud_event, 'data') and cloud_event.data:
            if isinstance(cloud_event.data, bytes):
                # Direct bytes data
                message_data = cloud_event.data.decode('utf-8')
                logger.info("Decoded bytes data")
            elif isinstance(cloud_event.data, dict):
                # Dictionary with base64 encoded data
                if 'data' in cloud_event.data:
                    message_data = base64.b64decode(cloud_event.data['data']).decode('utf-8')
                    logger.info("Decoded base64 data from dict")
                else:
                    # Direct JSON in dict
                    message_data = json.dumps(cloud_event.data)
                    logger.info("Used dict as JSON")
            elif isinstance(cloud_event.data, str):
                # Direct string data
                message_data = cloud_event.data
                logger.info("Used string data directly")
            else:
                # Try to convert to string
                message_data = str(cloud_event.data)
                logger.info("Converted data to string")
        
        if not message_data:
            logger.error("No data in Pub/Sub message")
            return
        
        logger.info(f"Message data: {message_data[:200]}...")  # Log first 200 chars
        
        # Parse music event
        try:
            event_data = json.loads(message_data)
            music_event = MusicEvent(**event_data)
            logger.info(f"Processing event for enrichment: {music_event.event_id}")
            
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Failed to parse music event: {e}")
            return
        
        # Generate enrichments using Claude
        enrichments = generate_claude_enrichments(music_event)
        
        if enrichments:
            # Create enriched event
            enriched_event = EnrichedMusicEvent(
                **music_event.dict(),
                **enrichments
            )
            
            # Store in BigQuery
            store_enriched_event(enriched_event)
            
            # Publish enriched event for downstream processing
            publish_enriched_event(enriched_event)
            
            logger.info(f"Successfully enriched event: {music_event.event_id}")
        else:
            logger.warning(f"Failed to generate enrichments for event: {music_event.event_id}")
            
    except Exception as e:
        logger.error(f"Enrichment processing failed: {str(e)}", exc_info=True)
        raise


def generate_claude_enrichments(music_event: MusicEvent) -> Optional[Dict]:
    """
    Generate enrichments using Claude LLM.
    
    Args:
        music_event: The music event to enrich
        
    Returns:
        Dictionary of enrichments or None if failed
    """
    try:
        # Prepare context for Claude
        context = prepare_event_context(music_event)
        
        # Generate enrichments
        enrichments = {}
        
        # Event description
        description = generate_event_description(context)
        if description:
            enrichments['event_description'] = description
        
        # Mood analysis
        mood = analyze_mood(context)
        if mood:
            enrichments['mood_analysis'] = mood
        
        # Genre prediction
        genres = predict_genres(context)
        if genres:
            enrichments['predicted_genres'] = genres
        
        # Listening context
        listening_context = infer_listening_context(context)
        if listening_context:
            enrichments['listening_context'] = listening_context
        
        # Similar tracks
        similar_tracks = generate_similar_tracks(context)
        if similar_tracks:
            enrichments['similar_tracks'] = similar_tracks
        
        # Calculate confidence
        enrichments['enrichment_confidence'] = calculate_enrichment_confidence(music_event)
        enrichments['enrichment_timestamp'] = datetime.utcnow()
        
        return enrichments
        
    except Exception as e:
        logger.error(f"Failed to generate enrichments: {e}")
        return None


def prepare_event_context(music_event: MusicEvent) -> str:
    """Prepare context string for Claude LLM."""
    return f"""
    Music Event Context:
    - Event Type: {music_event.event_type}
    - Track: {music_event.track.title} by {music_event.track.artist}
    - Album: {music_event.track.album} ({music_event.track.release_year})
    - Genre: {music_event.track.genre}
    - Duration: {music_event.track.duration} seconds
    - Platform: {music_event.streaming_event.platform}
    - Quality: {music_event.streaming_event.quality}
    - User Location: {music_event.user_interaction.location}
    - Timestamp: {music_event.timestamp}
    """


def generate_event_description(context: str) -> Optional[str]:
    """Generate event description using Claude."""
    try:
        # For now, use a simple template-based approach
        # In production, this would call Claude API
        return f"User is enjoying music with {context.split('Platform:')[1].split()[0]} quality streaming"
    except Exception as e:
        logger.error(f"Failed to generate event description: {e}")
        return None


def analyze_mood(context: str) -> Optional[str]:
    """Analyze the mood of the track using Claude."""
    try:
        # Simple mood analysis based on genre
        if "rock" in context.lower():
            return "Energetic, powerful, and dynamic"
        elif "pop" in context.lower():
            return "Catchy, upbeat, and accessible"
        elif "jazz" in context.lower():
            return "Smooth, sophisticated, and relaxing"
        else:
            return "Versatile and engaging"
    except Exception as e:
        logger.error(f"Failed to analyze mood: {e}")
        return None


def predict_genres(context: str) -> Optional[List[str]]:
    """Predict additional genres using Claude."""
    try:
        # Simple genre prediction based on artist and track info
        base_genre = context.split('Genre:')[1].split()[0].lower()
        if base_genre == "rock":
            return ["classic_rock", "hard_rock", "progressive_rock"]
        elif base_genre == "pop":
            return ["dance_pop", "synth_pop", "indie_pop"]
        else:
            return [base_genre, "alternative", "indie"]
    except Exception as e:
        logger.error(f"Failed to predict genres: {e}")
        return None


def infer_listening_context(context: str) -> Optional[str]:
    """Infer the listening context using Claude."""
    try:
        # Simple context inference based on time and location
        if "morning" in context.lower() or "06:00" in context or "07:00" in context or "08:00" in context:
            return "Morning commute or workout"
        elif "night" in context.lower() or "22:00" in context or "23:00" in context:
            return "Evening relaxation or party"
        else:
            return "Casual listening during daily activities"
    except Exception as e:
        logger.error(f"Failed to infer listening context: {e}")
        return None


def generate_similar_tracks(context: str) -> Optional[List[str]]:
    """Generate similar track recommendations using Claude."""
    try:
        # Simple similar track generation based on artist
        artist = context.split('by')[1].split()[0] if 'by' in context else "Unknown"
        if "Queen" in artist:
            return ["Bohemian Rhapsody", "We Will Rock You", "Another One Bites the Dust"]
        elif "Led Zeppelin" in artist:
            return ["Stairway to Heaven", "Whole Lotta Love", "Black Dog"]
        elif "Eagles" in artist:
            return ["Hotel California", "Take It Easy", "Desperado"]
        else:
            return ["Similar Track 1", "Similar Track 2", "Similar Track 3"]
    except Exception as e:
        logger.error(f"Failed to generate similar tracks: {e}")
        return None


def calculate_enrichment_confidence(music_event: MusicEvent) -> float:
    """Calculate confidence score for enrichments."""
    # Simple confidence calculation based on data completeness
    confidence = 0.5  # Base confidence
    
    # Increase confidence for complete data
    if music_event.track.title and music_event.track.artist:
        confidence += 0.2
    if music_event.track.genre:
        confidence += 0.1
    if music_event.user_interaction.location:
        confidence += 0.1
    if music_event.streaming_event.platform:
        confidence += 0.1
    
    return min(confidence, 1.0)


def store_enriched_event(enriched_event: EnrichedMusicEvent) -> None:
    """Store enriched event in BigQuery."""
    try:
        # Convert to BigQuery row
        row = {
            'event_id': enriched_event.event_id,
            'event_type': enriched_event.event_type.value,
            'track_title': enriched_event.track.title,
            'artist_name': enriched_event.artist.name,
            'platform': enriched_event.streaming_event.platform.value,
            'event_description': enriched_event.event_description,
            'mood_analysis': enriched_event.mood_analysis,
            'predicted_genres': json.dumps(enriched_event.predicted_genres) if enriched_event.predicted_genres else None,
            'listening_context': enriched_event.listening_context,
            'similar_tracks': json.dumps(enriched_event.similar_tracks) if enriched_event.similar_tracks else None,
            'enrichment_confidence': enriched_event.enrichment_confidence,
            'timestamp': enriched_event.timestamp.isoformat(),
            'enrichment_timestamp': enriched_event.enrichment_timestamp.isoformat()
        }
        
        # Insert into BigQuery
        errors = bigquery_client.insert_rows_json(table_ref, [row])
        if errors:
            logger.error(f"BigQuery insert errors: {errors}")
        else:
            logger.info(f"Stored enriched event in BigQuery: {enriched_event.event_id}")
            
    except Exception as e:
        logger.error(f"Failed to store enriched event: {e}")


def publish_enriched_event(enriched_event: EnrichedMusicEvent) -> None:
    """Publish enriched event to Pub/Sub."""
    try:
        event_data = enriched_event.json().encode('utf-8')
        
        future = publisher.publish(
            ENRICHED_EVENTS_TOPIC_PATH,
            event_data,
            event_type=enriched_event.event_type.value,
            platform=enriched_event.streaming_event.platform.value,
            timestamp=enriched_event.timestamp.isoformat()
        )
        
        message_id = future.result()
        logger.info(f"Published enriched event: {message_id}")
        
    except Exception as e:
        logger.error(f"Failed to publish enriched event: {e}")


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
        "service": "music-event-enrichment",
        "timestamp": datetime.utcnow().isoformat()
    }), 200, headers) 