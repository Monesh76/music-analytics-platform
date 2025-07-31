"""
Music Event Enrichment Function
Enriches music events with AI-powered insights using Claude LLM
"""

import os
import json
import logging
import functions_framework
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

# Google Cloud imports
from google.cloud import bigquery, pubsub_v1
from google.cloud import secretmanager

# Pydantic imports
from pydantic import BaseModel, Field, validator

# Anthropic imports
from anthropic import Anthropic

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize clients
GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT', 'mystage-claudellm')
BIGQUERY_DATASET = os.getenv('BIGQUERY_DATASET', 'music_analytics_dev')
ENRICHED_EVENTS_TOPIC = os.getenv('ENRICHED_EVENTS_TOPIC', 'enriched-music-events-dev')
CLAUDE_API_KEY_SECRET = os.getenv('CLAUDE_API_KEY_SECRET', 'claude-api-key-dev')

# Initialize clients
claude_api_key = os.getenv('CLAUDE_API_KEY', 'your-claude-api-key-here')
anthropic_client = Anthropic(api_key=claude_api_key)
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


class Genre(str, Enum):
    POP = "pop"
    ROCK = "rock"
    HIP_HOP = "hip_hop"
    ELECTRONIC = "electronic"
    JAZZ = "jazz"
    CLASSICAL = "classical"
    COUNTRY = "country"
    R_B = "r_b"
    FOLK = "folk"
    METAL = "metal"


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
    Cloud Function to enrich music events with AI-powered insights
    """
    try:
        # Parse the cloud event data
        if hasattr(cloud_event, 'data'):
            # Handle base64 encoded data
            import base64
            data = base64.b64decode(cloud_event.data).decode('utf-8')
            event_data = json.loads(data)
        else:
            # Handle direct JSON data
            event_data = cloud_event.get_json()
        
        logger.info(f"Processing music event: {event_data.get('event_id', 'unknown')}")
        
        # Parse the music event
        music_event = MusicEvent(**event_data)
        
        # Generate AI enrichments
        enrichments = generate_claude_enrichments(music_event)
        
        if enrichments:
            # Create enriched event
            enriched_event = EnrichedMusicEvent(
                **music_event.dict(),
                **enrichments
            )
            
            # Store in BigQuery
            store_enriched_event(enriched_event)
            
            # Publish to Pub/Sub
            publish_enriched_event(enriched_event)
            
            logger.info(f"Successfully enriched event: {music_event.event_id}")
        else:
            logger.warning(f"Failed to generate enrichments for event: {music_event.event_id}")
            
    except Exception as e:
        logger.error(f"Error processing music event: {str(e)}")
        raise


def generate_claude_enrichments(music_event: MusicEvent) -> Optional[Dict]:
    """
    Generate AI-powered enrichments using Claude LLM
    """
    try:
        # Prepare context for Claude
        context = prepare_event_context(music_event)
        
        # Generate enrichments
        event_description = generate_event_description(context)
        mood_analysis = analyze_mood(context)
        predicted_genres = predict_genres(context)
        listening_context = infer_listening_context(context)
        similar_tracks = generate_similar_tracks(context)
        confidence = calculate_enrichment_confidence(music_event)
        
        return {
            "event_description": event_description,
            "mood_analysis": mood_analysis,
            "predicted_genres": predicted_genres,
            "listening_context": listening_context,
            "similar_tracks": similar_tracks,
            "enrichment_confidence": confidence
        }
        
    except Exception as e:
        logger.error(f"Error generating enrichments: {str(e)}")
        return None


def prepare_event_context(music_event: MusicEvent) -> str:
    """
    Prepare context string for Claude LLM
    """
    track = music_event.track
    artist = music_event.artist
    event_type = music_event.event_type
    platform = music_event.streaming_event.platform
    
    context = f"""
    Track: {track.title} by {track.artist}
    Album: {track.album}
    Duration: {track.duration} seconds
    Genre: {track.genre}
    Release Year: {track.release_year}
    Artist: {artist.name}
    Artist Genre: {artist.genre}
    Artist Followers: {artist.followers}
    Event Type: {event_type}
    Platform: {platform}
    User Location: {music_event.user_interaction.location}
    """
    
    return context.strip()


def generate_event_description(context: str) -> Optional[str]:
    """
    Generate intelligent event description
    """
    try:
        prompt = f"""
        Based on this music event context, generate a brief, intelligent description of what's happening:
        
        {context}
        
        Provide a natural, engaging description of this music listening event.
        """
        
        response = anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text.strip()
        
    except Exception as e:
        logger.error(f"Error generating event description: {str(e)}")
        return "User listening to music"


def analyze_mood(context: str) -> Optional[str]:
    """
    Analyze the mood of the track
    """
    try:
        prompt = f"""
        Analyze the mood and emotional characteristics of this track:
        
        {context}
        
        Provide a brief mood analysis (e.g., "energetic and upbeat", "melancholic and introspective").
        """
        
        response = anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=50,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text.strip()
        
    except Exception as e:
        logger.error(f"Error analyzing mood: {str(e)}")
        return "neutral"


def predict_genres(context: str) -> Optional[List[str]]:
    """
    Predict genres for the track
    """
    try:
        prompt = f"""
        Based on this track information, predict the primary and secondary genres:
        
        {context}
        
        Return a list of 3-5 relevant genres (e.g., ["rock", "classic_rock", "soft_rock"]).
        """
        
        response = anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=50,
            messages=[{"role": "user", "content": prompt}]
        )
        
        genres_text = response.content[0].text.strip()
        # Parse genres from response
        genres = [g.strip().lower() for g in genres_text.replace('[', '').replace(']', '').split(',')]
        return genres[:5]  # Limit to 5 genres
        
    except Exception as e:
        logger.error(f"Error predicting genres: {str(e)}")
        return ["unknown"]


def infer_listening_context(context: str) -> Optional[str]:
    """
    Infer the listening context/environment
    """
    try:
        prompt = f"""
        Based on this music event, infer the likely listening context:
        
        {context}
        
        Provide a brief context (e.g., "evening relaxation", "workout session", "party atmosphere").
        """
        
        response = anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=50,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text.strip()
        
    except Exception as e:
        logger.error(f"Error inferring context: {str(e)}")
        return "casual listening"


def generate_similar_tracks(context: str) -> Optional[List[str]]:
    """
    Generate similar track recommendations
    """
    try:
        prompt = f"""
        Based on this track, suggest 5 similar tracks by the same artist:
        
        {context}
        
        Return a list of 5 track titles by the same artist.
        """
        
        response = anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}]
        )
        
        tracks_text = response.content[0].text.strip()
        # Parse track titles from response
        tracks = [t.strip() for t in tracks_text.split('\n') if t.strip()]
        return tracks[:5]  # Limit to 5 tracks
        
    except Exception as e:
        logger.error(f"Error generating similar tracks: {str(e)}")
        return ["Similar Track 1", "Similar Track 2", "Similar Track 3"]


def calculate_enrichment_confidence(music_event: MusicEvent) -> float:
    """
    Calculate confidence score for enrichments
    """
    confidence = 0.5  # Base confidence
    
    # Add confidence based on data completeness
    if music_event.track.title and music_event.track.artist:
        confidence += 0.2
    
    if music_event.artist.name:
        confidence += 0.1
    
    if music_event.streaming_event.platform:
        confidence += 0.1
    
    # Bonus for famous artists
    famous_artists = ["Eagles", "Queen", "Led Zeppelin", "Michael Jackson", "Bob Dylan"]
    if music_event.artist.name in famous_artists:
        confidence += 0.1
    
    # Bonus for complete metadata
    if music_event.track.album and music_event.track.release_year:
        confidence += 0.1
    
    return min(confidence, 0.95)  # Cap at 95%


def store_enriched_event(enriched_event: EnrichedMusicEvent) -> None:
    """
    Store enriched event in BigQuery
    """
    try:
        # Convert to BigQuery format
        row = {
            'event_id': enriched_event.event_id,
            'event_type': enriched_event.event_type,
            'track_title': enriched_event.track.title,
            'artist_name': enriched_event.artist.name,
            'platform': enriched_event.streaming_event.platform,
            'event_description': enriched_event.event_description,
            'mood_analysis': enriched_event.mood_analysis,
            'predicted_genres': json.dumps(enriched_event.predicted_genres),
            'listening_context': enriched_event.listening_context,
            'similar_tracks': json.dumps(enriched_event.similar_tracks),
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
        logger.error(f"Error storing enriched event: {str(e)}")


def publish_enriched_event(enriched_event: EnrichedMusicEvent) -> None:
    """
    Publish enriched event to Pub/Sub
    """
    try:
        # Convert to JSON
        event_data = enriched_event.dict()
        event_data['timestamp'] = enriched_event.timestamp.isoformat()
        event_data['enrichment_timestamp'] = enriched_event.enrichment_timestamp.isoformat()
        
        # Publish to Pub/Sub
        future = publisher.publish(
            ENRICHED_EVENTS_TOPIC_PATH,
            json.dumps(event_data).encode('utf-8')
        )
        
        logger.info(f"Published enriched event to Pub/Sub: {enriched_event.event_id}")
        
    except Exception as e:
        logger.error(f"Error publishing enriched event: {str(e)}") 