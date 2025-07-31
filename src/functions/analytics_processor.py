"""
Production-ready Analytics Processor Cloud Function.
Processes music events and generates real-time analytics.
"""

import json
import base64
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

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

# Initialize clients
bigquery_client = bigquery.Client()
publisher = pubsub_v1.PublisherClient()

# BigQuery table references
processed_events_table = bigquery_client.dataset(BIGQUERY_DATASET).table('processed_events')
engagement_metrics_table = bigquery_client.dataset(BIGQUERY_DATASET).table('engagement_metrics')
genre_metrics_table = bigquery_client.dataset(BIGQUERY_DATASET).table('genre_metrics')
platform_metrics_table = bigquery_client.dataset(BIGQUERY_DATASET).table('platform_metrics')


# Data models
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


class ProcessedEvent(BaseModel):
    event_id: str
    event_type: str
    track_title: str
    artist_name: str
    genre: str
    platform: str
    user_location: str
    timestamp: str
    processing_time: str
    engagement_score: float
    engagement_level: str
    genre_popularity: float
    is_popular_genre: bool
    platform_quality: str
    is_premium_platform: bool
    time_context: str
    time_multiplier: float
    adjusted_engagement: float


@functions_framework.cloud_event
def process_music_analytics(cloud_event) -> None:
    """
    Cloud Function triggered by Pub/Sub to process music events and generate analytics.
    """
    
    try:
        logger.info(f"Received analytics event: {cloud_event}")
        
        # Handle Pub/Sub message format
        message_data = None
        
        if hasattr(cloud_event, 'data') and cloud_event.data:
            if isinstance(cloud_event.data, dict) and 'data' in cloud_event.data:
                try:
                    encoded_data = cloud_event.data['data']
                    message_data = base64.b64decode(encoded_data).decode('utf-8')
                    logger.info("Successfully decoded base64 Pub/Sub message data")
                except Exception as e:
                    logger.error(f"Failed to decode base64 data: {e}")
                    return
            else:
                logger.error("Pub/Sub message does not contain expected 'data' field")
                return
        
        if not message_data:
            logger.error("No data in Pub/Sub message")
            return
        
        logger.info(f"Message data: {message_data[:200]}...")
        
        # Parse music event
        try:
            event_data = json.loads(message_data)
            music_event = MusicEvent(**event_data)
            logger.info(f"Processing analytics for event: {music_event.event_id}")
            
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Failed to parse music event: {e}")
            return
        
        # Process analytics
        processed_event = process_event_analytics(music_event)
        
        if processed_event:
            # Store processed event
            store_processed_event(processed_event)
            
            # Update real-time metrics
            update_engagement_metrics(processed_event)
            update_genre_metrics(processed_event)
            update_platform_metrics(processed_event)
            
            logger.info(f"Successfully processed analytics for event: {music_event.event_id}")
        else:
            logger.warning(f"Failed to process analytics for event: {music_event.event_id}")
            
    except Exception as e:
        logger.error(f"Analytics processing failed: {str(e)}", exc_info=True)
        raise


def process_event_analytics(music_event: MusicEvent) -> ProcessedEvent:
    """Process music event and generate analytics."""
    
    # Calculate engagement score
    engagement_scores = {
        'play': 1.0,
        'like': 2.0,
        'share': 3.0,
        'pause': 0.5,
        'skip': 0.1
    }
    
    base_score = engagement_scores.get(music_event.event_type.value, 1.0)
    
    # Location bonus
    location = music_event.user_interaction.location.lower()
    if 'new york' in location or 'los angeles' in location:
        base_score *= 1.2
    elif 'london' in location or 'miami' in location:
        base_score *= 1.1
    
    # Genre popularity
    genre_popularity_map = {
        'rock': 0.9,
        'pop': 0.8,
        'hip_hop': 0.7,
        'electronic': 0.6,
        'jazz': 0.5,
        'classical': 0.4
    }
    
    genre_popularity = genre_popularity_map.get(music_event.track.genre.lower(), 0.5)
    is_popular_genre = genre_popularity > 0.7
    
    # Platform quality
    platform_quality_map = {
        'spotify': 'high',
        'apple_music': 'high',
        'youtube_music': 'medium',
        'soundcloud': 'medium'
    }
    
    platform_quality = platform_quality_map.get(music_event.streaming_event.platform.value, 'unknown')
    is_premium_platform = music_event.streaming_event.platform.value in ['spotify', 'apple_music']
    
    # Time-based analytics
    hour = music_event.timestamp.hour
    
    if 6 <= hour <= 9:
        time_context = 'morning_commute'
        time_multiplier = 1.3
    elif 12 <= hour <= 14:
        time_context = 'lunch_break'
        time_multiplier = 1.1
    elif 17 <= hour <= 19:
        time_context = 'evening_commute'
        time_multiplier = 1.4
    elif 20 <= hour <= 23:
        time_context = 'evening_relaxation'
        time_multiplier = 1.2
    else:
        time_context = 'other'
        time_multiplier = 1.0
    
    adjusted_engagement = base_score * time_multiplier
    
    # Determine engagement level
    if adjusted_engagement > 1.5:
        engagement_level = 'high'
    elif adjusted_engagement > 0.8:
        engagement_level = 'medium'
    else:
        engagement_level = 'low'
    
    return ProcessedEvent(
        event_id=music_event.event_id,
        event_type=music_event.event_type.value,
        track_title=music_event.track.title,
        artist_name=music_event.artist.name,
        genre=music_event.track.genre,
        platform=music_event.streaming_event.platform.value,
        user_location=music_event.user_interaction.location,
        timestamp=music_event.timestamp.isoformat(),
        processing_time=datetime.utcnow().isoformat(),
        engagement_score=base_score,
        engagement_level=engagement_level,
        genre_popularity=genre_popularity,
        is_popular_genre=is_popular_genre,
        platform_quality=platform_quality,
        is_premium_platform=is_premium_platform,
        time_context=time_context,
        time_multiplier=time_multiplier,
        adjusted_engagement=adjusted_engagement
    )


def store_processed_event(processed_event: ProcessedEvent) -> None:
    """Store processed event in BigQuery."""
    try:
        row = processed_event.dict()
        
        errors = bigquery_client.insert_rows_json(processed_events_table, [row])
        if errors:
            logger.error(f"BigQuery insert errors: {errors}")
        else:
            logger.info(f"Stored processed event in BigQuery: {processed_event.event_id}")
            
    except Exception as e:
        logger.error(f"Failed to store processed event: {e}")


def update_engagement_metrics(processed_event: ProcessedEvent) -> None:
    """Update engagement metrics in BigQuery."""
    try:
        # This would typically aggregate metrics over time windows
        # For now, we'll store individual metrics
        row = {
            'event_type': processed_event.event_type,
            'count': 1,
            'avg_engagement': processed_event.engagement_score,
            'window_start': datetime.utcnow().isoformat()
        }
        
        errors = bigquery_client.insert_rows_json(engagement_metrics_table, [row])
        if errors:
            logger.error(f"BigQuery engagement metrics errors: {errors}")
        else:
            logger.info(f"Updated engagement metrics for: {processed_event.event_type}")
            
    except Exception as e:
        logger.error(f"Failed to update engagement metrics: {e}")


def update_genre_metrics(processed_event: ProcessedEvent) -> None:
    """Update genre metrics in BigQuery."""
    try:
        row = {
            'genre': processed_event.genre,
            'count': 1,
            'avg_popularity': processed_event.genre_popularity,
            'window_start': datetime.utcnow().isoformat()
        }
        
        errors = bigquery_client.insert_rows_json(genre_metrics_table, [row])
        if errors:
            logger.error(f"BigQuery genre metrics errors: {errors}")
        else:
            logger.info(f"Updated genre metrics for: {processed_event.genre}")
            
    except Exception as e:
        logger.error(f"Failed to update genre metrics: {e}")


def update_platform_metrics(processed_event: ProcessedEvent) -> None:
    """Update platform metrics in BigQuery."""
    try:
        row = {
            'platform': processed_event.platform,
            'count': 1,
            'premium_ratio': 1.0 if processed_event.is_premium_platform else 0.0,
            'window_start': datetime.utcnow().isoformat()
        }
        
        errors = bigquery_client.insert_rows_json(platform_metrics_table, [row])
        if errors:
            logger.error(f"BigQuery platform metrics errors: {errors}")
        else:
            logger.info(f"Updated platform metrics for: {processed_event.platform}")
            
    except Exception as e:
        logger.error(f"Failed to update platform metrics: {e}")


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
        "service": "music-analytics-processor",
        "timestamp": datetime.utcnow().isoformat()
    }), 200, headers) 