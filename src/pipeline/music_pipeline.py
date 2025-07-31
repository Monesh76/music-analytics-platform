"""
Apache Beam streaming pipeline for real-time music event processing.
Handles 10,000+ events per day with sub-second latency.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Iterable

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, GoogleCloudOptions, StandardOptions, WorkerOptions
from apache_beam.io import ReadFromPubSub, WriteToBigQuery
from apache_beam.transforms import window
from pydantic import ValidationError

from src.models.music_events import MusicEvent, EnrichedMusicEvent
from src.utils.config import get_config
from src.utils.logging_util import setup_logging


# Setup logging
logger = setup_logging("music-pipeline")


class ParseMusicEvent(beam.DoFn):
    """Parse and validate incoming music events from Pub/Sub."""
    
    def __init__(self):
        self.success_counter = beam.metrics.Metrics.counter('pipeline', 'events_parsed_success')
        self.error_counter = beam.metrics.Metrics.counter('pipeline', 'events_parsed_error')
    
    def process(self, message: bytes) -> Iterable[MusicEvent]:
        """
        Parse Pub/Sub message into MusicEvent.
        
        Args:
            message: Raw Pub/Sub message
            
        Yields:
            Validated MusicEvent objects
        """
        try:
            # Decode message
            message_str = message.decode('utf-8')
            event_data = json.loads(message_str)
            
            # Validate with Pydantic
            music_event = MusicEvent(**event_data)
            
            self.success_counter.inc()
            yield music_event
            
        except (json.JSONDecodeError, ValidationError, UnicodeDecodeError) as e:
            self.error_counter.inc()
            logger.error(f"Failed to parse music event: {e}", message_sample=message[:100])
            # Could publish to dead letter queue here
            pass
        except Exception as e:
            self.error_counter.inc()
            logger.error(f"Unexpected error parsing event: {e}", exc_info=True)
            pass


class EnrichEventMetadata(beam.DoFn):
    """Enrich events with additional metadata and computed fields."""
    
    def __init__(self):
        self.processed_counter = beam.metrics.Metrics.counter('pipeline', 'events_enriched')
    
    def process(self, event: MusicEvent) -> Iterable[Dict[str, Any]]:
        """
        Enrich event with computed fields for analytics.
        
        Args:
            event: Validated music event
            
        Yields:
            Enriched event data dictionaries
        """
        try:
            # Calculate derived fields
            enriched_data = self._calculate_derived_fields(event)
            
            # Convert to BigQuery-compatible format
            bq_row = self._convert_to_bigquery_row(event, enriched_data)
            
            self.processed_counter.inc()
            yield bq_row
            
        except Exception as e:
            logger.error(f"Failed to enrich event {event.event_id}: {e}")
            # Yield original data as fallback
            yield self._convert_to_bigquery_row(event, {})
    
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
        platform = event.streaming_event.platform.value
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
        if event.event_type.value in ['like', 'share', 'playlist_add']:
            score += 0.4
        
        # Boost for repeat listening
        if event.play_event and event.play_event.repeat_mode != 'off':
            score += 0.1
        
        # Penalty for skips
        if event.event_type.value == 'skip':
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
            'event_type': event.event_type.value,
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
            'platform': event.streaming_event.platform.value,
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


class AggregateEventMetrics(beam.DoFn):
    """Aggregate events for real-time analytics."""
    
    def process(self, events: List[Dict[str, Any]]) -> Iterable[Dict[str, Any]]:
        """
        Aggregate events within a time window.
        
        Args:
            events: List of enriched event dictionaries
            
        Yields:
            Aggregated metrics
        """
        
        if not events:
            return
        
        # Calculate aggregations
        total_events = len(events)
        unique_users = len(set(event['user_id'] for event in events))
        unique_tracks = len(set(event['track_id'] for event in events))
        
        # Platform distribution
        platform_counts = {}
        for event in events:
            platform = event['platform']
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
        # Event type distribution
        event_type_counts = {}
        for event in events:
            event_type = event['event_type']
            event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
        
        # Average engagement
        engagement_scores = [event.get('engagement_score', 0.0) for event in events if 'engagement_score' in event]
        avg_engagement = sum(engagement_scores) / len(engagement_scores) if engagement_scores else 0.0
        
        # Window metadata
        window_start = min(event['timestamp'] for event in events)
        window_end = max(event['timestamp'] for event in events)
        
        aggregated_metrics = {
            'window_start': window_start,
            'window_end': window_end,
            'total_events': total_events,
            'unique_users': unique_users,
            'unique_tracks': unique_tracks,
            'platform_distribution': platform_counts,
            'event_type_distribution': event_type_counts,
            'average_engagement_score': avg_engagement,
            'aggregation_timestamp': datetime.utcnow().isoformat(),
        }
        
        yield aggregated_metrics


def create_pipeline_options(config) -> PipelineOptions:
    """Create Beam pipeline options for Dataflow."""
    
    options = PipelineOptions()
    
    # Google Cloud options
    google_cloud_options = options.view_as(GoogleCloudOptions)
    google_cloud_options.project = config.google_cloud_project
    google_cloud_options.region = config.dataflow_region
    google_cloud_options.temp_location = config.dataflow_temp_location
    google_cloud_options.staging_location = config.dataflow_staging_location
    google_cloud_options.job_name = f'music-pipeline-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
    
    # Standard options
    standard_options = options.view_as(StandardOptions)
    standard_options.runner = 'DataflowRunner'
    standard_options.streaming = True
    
    # Worker options
    worker_options = options.view_as(WorkerOptions)
    worker_options.max_num_workers = config.max_workers
    worker_options.autoscaling_algorithm = 'THROUGHPUT_BASED'
    worker_options.machine_type = 'n1-standard-2'
    
    return options


def run_streaming_pipeline(config=None):
    """
    Run the streaming music data pipeline.
    
    Args:
        config: Pipeline configuration (uses default if None)
    """
    
    if config is None:
        config = get_config()
    
    # Create pipeline options
    pipeline_options = create_pipeline_options(config)
    
    # BigQuery table schemas
    raw_events_schema = {
        'fields': [
            {'name': 'event_id', 'type': 'STRING', 'mode': 'REQUIRED'},
            {'name': 'event_type', 'type': 'STRING', 'mode': 'REQUIRED'},
            {'name': 'timestamp', 'type': 'TIMESTAMP', 'mode': 'REQUIRED'},
            {'name': 'processing_timestamp', 'type': 'TIMESTAMP', 'mode': 'REQUIRED'},
            {'name': 'track_id', 'type': 'STRING', 'mode': 'REQUIRED'},
            {'name': 'track_name', 'type': 'STRING', 'mode': 'REQUIRED'},
            {'name': 'track_duration_ms', 'type': 'INTEGER', 'mode': 'NULLABLE'},
            {'name': 'track_explicit', 'type': 'BOOLEAN', 'mode': 'NULLABLE'},
            {'name': 'track_popularity', 'type': 'INTEGER', 'mode': 'NULLABLE'},
            {'name': 'track_energy', 'type': 'FLOAT', 'mode': 'NULLABLE'},
            {'name': 'track_valence', 'type': 'FLOAT', 'mode': 'NULLABLE'},
            {'name': 'track_tempo', 'type': 'FLOAT', 'mode': 'NULLABLE'},
            {'name': 'track_genres', 'type': 'STRING', 'mode': 'REPEATED'},
            {'name': 'artist_id', 'type': 'STRING', 'mode': 'REQUIRED'},
            {'name': 'artist_name', 'type': 'STRING', 'mode': 'REQUIRED'},
            {'name': 'artist_followers', 'type': 'INTEGER', 'mode': 'NULLABLE'},
            {'name': 'artist_verified', 'type': 'BOOLEAN', 'mode': 'NULLABLE'},
            {'name': 'artist_country', 'type': 'STRING', 'mode': 'NULLABLE'},
            {'name': 'artist_genres', 'type': 'STRING', 'mode': 'REPEATED'},
            {'name': 'album_id', 'type': 'STRING', 'mode': 'NULLABLE'},
            {'name': 'album_name', 'type': 'STRING', 'mode': 'NULLABLE'},
            {'name': 'album_release_date', 'type': 'TIMESTAMP', 'mode': 'NULLABLE'},
            {'name': 'user_id', 'type': 'STRING', 'mode': 'REQUIRED'},
            {'name': 'session_id', 'type': 'STRING', 'mode': 'REQUIRED'},
            {'name': 'device_type', 'type': 'STRING', 'mode': 'NULLABLE'},
            {'name': 'user_location', 'type': 'STRING', 'mode': 'NULLABLE'},
            {'name': 'subscription_type', 'type': 'STRING', 'mode': 'NULLABLE'},
            {'name': 'user_age_group', 'type': 'STRING', 'mode': 'NULLABLE'},
            {'name': 'platform', 'type': 'STRING', 'mode': 'REQUIRED'},
            {'name': 'stream_quality', 'type': 'STRING', 'mode': 'NULLABLE'},
            {'name': 'bandwidth_kbps', 'type': 'INTEGER', 'mode': 'NULLABLE'},
            {'name': 'buffer_events', 'type': 'INTEGER', 'mode': 'NULLABLE'},
            {'name': 'played_duration_ms', 'type': 'INTEGER', 'mode': 'NULLABLE'},
            {'name': 'skip_reason', 'type': 'STRING', 'mode': 'NULLABLE'},
            {'name': 'playlist_id', 'type': 'STRING', 'mode': 'NULLABLE'},
            {'name': 'shuffle_mode', 'type': 'BOOLEAN', 'mode': 'NULLABLE'},
            {'name': 'repeat_mode', 'type': 'STRING', 'mode': 'NULLABLE'},
            # Derived fields
            {'name': 'hour_of_day', 'type': 'INTEGER', 'mode': 'NULLABLE'},
            {'name': 'day_of_week', 'type': 'INTEGER', 'mode': 'NULLABLE'},
            {'name': 'is_weekend', 'type': 'BOOLEAN', 'mode': 'NULLABLE'},
            {'name': 'month', 'type': 'INTEGER', 'mode': 'NULLABLE'},
            {'name': 'year', 'type': 'INTEGER', 'mode': 'NULLABLE'},
            {'name': 'track_duration_seconds', 'type': 'FLOAT', 'mode': 'NULLABLE'},
            {'name': 'is_long_track', 'type': 'BOOLEAN', 'mode': 'NULLABLE'},
            {'name': 'is_short_track', 'type': 'BOOLEAN', 'mode': 'NULLABLE'},
            {'name': 'play_completion_ratio', 'type': 'FLOAT', 'mode': 'NULLABLE'},
            {'name': 'is_full_play', 'type': 'BOOLEAN', 'mode': 'NULLABLE'},
            {'name': 'is_skip', 'type': 'BOOLEAN', 'mode': 'NULLABLE'},
            {'name': 'engagement_score', 'type': 'FLOAT', 'mode': 'NULLABLE'},
            {'name': 'platform_category', 'type': 'STRING', 'mode': 'NULLABLE'},
        ]
    }
    
    aggregated_metrics_schema = {
        'fields': [
            {'name': 'window_start', 'type': 'TIMESTAMP', 'mode': 'REQUIRED'},
            {'name': 'window_end', 'type': 'TIMESTAMP', 'mode': 'REQUIRED'},
            {'name': 'total_events', 'type': 'INTEGER', 'mode': 'REQUIRED'},
            {'name': 'unique_users', 'type': 'INTEGER', 'mode': 'REQUIRED'},
            {'name': 'unique_tracks', 'type': 'INTEGER', 'mode': 'REQUIRED'},
            {'name': 'platform_distribution', 'type': 'STRING', 'mode': 'NULLABLE'},  # JSON string
            {'name': 'event_type_distribution', 'type': 'STRING', 'mode': 'NULLABLE'},  # JSON string
            {'name': 'average_engagement_score', 'type': 'FLOAT', 'mode': 'NULLABLE'},
            {'name': 'aggregation_timestamp', 'type': 'TIMESTAMP', 'mode': 'REQUIRED'},
        ]
    }
    
    # Build pipeline
    with beam.Pipeline(options=pipeline_options) as pipeline:
        
        # Read from Pub/Sub
        raw_messages = (
            pipeline
            | "Read from Pub/Sub" >> ReadFromPubSub(
                topic=f"projects/{config.google_cloud_project}/topics/{config.raw_events_topic}"
            )
        )
        
        # Parse and validate events
        parsed_events = (
            raw_messages
            | "Parse Music Events" >> beam.ParDo(ParseMusicEvent())
        )
        
        # Enrich events with metadata
        enriched_events = (
            parsed_events
            | "Enrich Event Metadata" >> beam.ParDo(EnrichEventMetadata())
        )
        
        # Write enriched events to BigQuery
        _ = (
            enriched_events
            | "Write to BigQuery" >> WriteToBigQuery(
                table=f"{config.google_cloud_project}:{config.bigquery_dataset}.{config.raw_events_table}",
                schema=raw_events_schema,
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
            )
        )
        
        # Create real-time aggregations
        windowed_events = (
            enriched_events
            | "Apply Fixed Window" >> beam.WindowInto(
                window.FixedWindows(60)  # 1-minute windows
            )
            | "Group by Window" >> beam.GroupBy()
            | "Aggregate Metrics" >> beam.ParDo(AggregateEventMetrics())
        )
        
        # Convert aggregations to JSON strings for BigQuery
        json_aggregations = (
            windowed_events
            | "Convert to JSON" >> beam.Map(lambda x: {
                **x,
                'platform_distribution': json.dumps(x['platform_distribution']),
                'event_type_distribution': json.dumps(x['event_type_distribution'])
            })
        )
        
        # Write aggregations to BigQuery
        _ = (
            json_aggregations
            | "Write Aggregations to BigQuery" >> WriteToBigQuery(
                table=f"{config.google_cloud_project}:{config.bigquery_dataset}.music_event_metrics",
                schema=aggregated_metrics_schema,
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
            )
        )
    
    logger.info("Music data streaming pipeline started successfully")


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run_streaming_pipeline() 