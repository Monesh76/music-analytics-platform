"""
Simplified Music Pipeline for Local Development
This version doesn't require Apache Beam and can be used for testing and development.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.models.music_events import MusicEvent
from src.utils.config import get_config
from src.utils.logging_util import setup_logging


# Setup logging
logger = setup_logging("music-pipeline-simple")


class SimpleMusicProcessor:
    """Simple processor for music events without Apache Beam."""
    
    def __init__(self):
        self.config = get_config()
        self.processed_count = 0
        self.error_count = 0
    
    def process_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single music event.
        
        Args:
            event_data: Raw event data dictionary
            
        Returns:
            Processed event data
        """
        try:
            # Validate event with Pydantic
            music_event = MusicEvent(**event_data)
            
            # Calculate derived fields
            enriched_data = self._calculate_derived_fields(music_event)
            
            # Convert to BigQuery-compatible format
            bq_row = self._convert_to_bigquery_row(music_event, enriched_data)
            
            self.processed_count += 1
            return bq_row
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Failed to process event: {e}", exc_info=True)
            return None
    
    def _calculate_derived_fields(self, event: MusicEvent) -> Dict[str, Any]:
        """Calculate derived fields for analytics."""
        
        derived_fields = {}
        
        # Time-based fields
        timestamp = event.timestamp
        derived_fields.update({
            'hour_of_day': timestamp.hour,
            'day_of_week': timestamp.weekday(),
            'is_weekend': timestamp.weekday() >= 5,
            'month': timestamp.month,
            'year': timestamp.year,
        })
        
        # Track duration analysis
        if event.track.duration_ms:
            duration_seconds = event.track.duration_ms / 1000
            derived_fields.update({
                'track_duration_seconds': duration_seconds,
                'is_long_track': duration_seconds > 300,  # 5+ minutes
                'is_short_track': duration_seconds < 120,  # <2 minutes
            })
        
        # Play completion analysis
        if event.play_event and event.track.duration_ms:
            play_ratio = event.play_event.played_duration_ms / event.track.duration_ms
            derived_fields.update({
                'play_completion_ratio': min(play_ratio, 1.0),
                'is_full_play': play_ratio >= 0.8,
                'is_skip': play_ratio < 0.3,
            })
        
        # User engagement score
        engagement_score = self._calculate_engagement_score(event)
        derived_fields['engagement_score'] = engagement_score
        
        # Platform-specific fields
        platform = event.streaming_event.platform.value if hasattr(event.streaming_event.platform, 'value') else str(event.streaming_event.platform)
        derived_fields['platform_category'] = self._categorize_platform(platform)
        
        return derived_fields
    
    def _calculate_engagement_score(self, event: MusicEvent) -> float:
        """Calculate user engagement score (0-1)."""
        
        score = 0.5  # Base score
        
        # Boost for full track plays
        if event.play_event and event.track.duration_ms:
            play_ratio = event.play_event.played_duration_ms / event.track.duration_ms
            score += play_ratio * 0.3
        
        # Boost for interactive events
        event_type_str = event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type)
        if event_type_str in ['like', 'share', 'playlist_add']:
            score += 0.4
        
        # Boost for repeat listening
        if event.play_event and event.play_event.repeat_mode != 'off':
            score += 0.1
        
        # Penalty for skips
        if event_type_str == 'skip':
            score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def _categorize_platform(self, platform: str) -> str:
        """Categorize streaming platform."""
        
        premium_platforms = ['spotify', 'apple_music', 'tidal']
        ad_supported = ['youtube_music', 'soundcloud', 'pandora']
        
        if platform in premium_platforms:
            return 'premium'
        elif platform in ad_supported:
            return 'ad_supported'
        else:
            return 'other'
    
    def _convert_to_bigquery_row(self, event: MusicEvent, enriched_data: Dict) -> Dict[str, Any]:
        """Convert event to BigQuery row format."""
        
        row = {
            # Core event data
            'event_id': event.event_id,
            'event_type': event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type),
            'timestamp': event.timestamp.isoformat(),
            'processing_timestamp': event.processing_timestamp.isoformat(),
            
            # Track information
            'track_id': event.track.id,
            'track_name': event.track.name,
            'track_duration_ms': event.track.duration_ms,
            'track_explicit': event.track.explicit,
            'track_popularity': event.track.popularity,
            'track_energy': event.track.energy,
            'track_valence': event.track.valence,
            'track_tempo': event.track.tempo,
            'track_genres': [g.value for g in event.track.genres] if event.track.genres else [],
            
            # Artist information
            'artist_id': event.artist.id,
            'artist_name': event.artist.name,
            'artist_followers': event.artist.followers,
            'artist_verified': event.artist.verified,
            'artist_country': event.artist.country,
            'artist_genres': [g.value for g in event.artist.genres] if event.artist.genres else [],
            
            # Album information
            'album_id': event.album.id if event.album else None,
            'album_name': event.album.name if event.album else None,
            'album_release_date': event.album.release_date.isoformat() if event.album and event.album.release_date else None,
            
            # User interaction
            'user_id': event.user_interaction.user_id,
            'session_id': event.user_interaction.session_id,
            'device_type': event.user_interaction.device_type,
            'user_location': event.user_interaction.location,
            'subscription_type': event.user_interaction.subscription_type,
            'user_age_group': event.user_interaction.user_age_group,
            
            # Streaming platform
            'platform': event.streaming_event.platform.value if hasattr(event.streaming_event.platform, 'value') else str(event.streaming_event.platform),
            'stream_quality': event.streaming_event.stream_quality,
            'bandwidth_kbps': event.streaming_event.bandwidth_kbps,
            'buffer_events': event.streaming_event.buffer_events,
            
            # Play event details
            'played_duration_ms': event.play_event.played_duration_ms if event.play_event else None,
            'skip_reason': event.play_event.skip_reason if event.play_event else None,
            'playlist_id': event.play_event.playlist_id if event.play_event else None,
            'shuffle_mode': event.play_event.shuffle_mode if event.play_event else None,
            'repeat_mode': event.play_event.repeat_mode if event.play_event else None,
        }
        
        # Add derived fields
        row.update(enriched_data)
        
        return row
    
    def process_events_batch(self, events_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a batch of events.
        
        Args:
            events_data: List of raw event data dictionaries
            
        Returns:
            List of processed event data
        """
        processed_events = []
        
        for event_data in events_data:
            processed_event = self.process_event(event_data)
            if processed_event:
                processed_events.append(processed_event)
        
        logger.info(f"Processed {len(processed_events)} events successfully")
        return processed_events
    
    def get_stats(self) -> Dict[str, int]:
        """Get processing statistics."""
        return {
            'processed_count': self.processed_count,
            'error_count': self.error_count,
            'success_rate': self.processed_count / (self.processed_count + self.error_count) if (self.processed_count + self.error_count) > 0 else 0
        }


def test_pipeline():
    """Test the simplified pipeline with sample data."""
    
    # Sample event data
    sample_event = {
        "event_type": "play",
        "track": {
            "id": "track-001",
            "name": "Test Song",
            "artist_id": "artist-001",
            "duration_ms": 210000,
            "popularity": 75,
            "energy": 0.8,
            "valence": 0.6,
            "tempo": 120.0,
            "genres": ["pop"],
            "explicit": False
        },
        "artist": {
            "id": "artist-001",
            "name": "Test Artist",
            "genres": ["pop"],
            "verified": True,
            "followers": 100000,
            "country": "US"
        },
        "user_interaction": {
            "user_id": "user-001",
            "session_id": "session-001",
            "device_type": "mobile",
            "location": "US",
            "subscription_type": "premium",
            "user_age_group": "25-34"
        },
        "streaming_event": {
            "platform": "spotify",
            "stream_quality": "high",
            "bandwidth_kbps": 320,
            "buffer_events": 0
        },
        "play_event": {
            "played_duration_ms": 180000,
            "shuffle_mode": False,
            "repeat_mode": "off"
        }
    }
    
    # Process the event
    processor = SimpleMusicProcessor()
    result = processor.process_event(sample_event)
    
    if result:
        print("✅ Pipeline test successful!")
        print(f"Processed event: {result['track_name']} by {result['artist_name']}")
        print(f"Engagement score: {result.get('engagement_score', 'N/A')}")
        print(f"Platform: {result['platform']}")
    else:
        print("❌ Pipeline test failed!")
    
    return result


if __name__ == "__main__":
    test_pipeline() 