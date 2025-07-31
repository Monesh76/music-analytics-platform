#!/usr/bin/env python3
"""
Production-ready Dataflow pipeline for Real-Time Music Data Analytics.
Processes music events from Pub/Sub and generates advanced analytics.
"""

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.io import ReadFromPubSub
from apache_beam.io import WriteToBigQuery
from apache_beam.transforms import window
from apache_beam.transforms import trigger
from apache_beam.transforms import core
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MusicEventProcessor(beam.DoFn):
    """Process music events and extract analytics."""
    
    def process(self, element):
        try:
            # Parse the Pub/Sub message
            if isinstance(element, bytes):
                data = element.decode('utf-8')
            else:
                data = str(element)
            
            # Parse JSON
            event = json.loads(data)
            
            # Extract analytics
            analytics = {
                'event_id': event.get('event_id'),
                'event_type': event.get('event_type'),
                'track_title': event.get('track', {}).get('title'),
                'artist_name': event.get('artist', {}).get('name'),
                'genre': event.get('track', {}).get('genre'),
                'platform': event.get('streaming_event', {}).get('platform'),
                'user_location': event.get('user_interaction', {}).get('location'),
                'timestamp': event.get('timestamp'),
                'processing_time': datetime.utcnow().isoformat()
            }
            
            yield analytics
            
        except Exception as e:
            logger.error(f"Error processing event: {e}")
            yield None

class EngagementCalculator(beam.DoFn):
    """Calculate engagement metrics."""
    
    def process(self, element):
        if element is None:
            return
        
        # Calculate engagement score based on event type
        engagement_scores = {
            'play': 1.0,
            'like': 2.0,
            'share': 3.0,
            'pause': 0.5,
            'skip': 0.1
        }
        
        event_type = element.get('event_type', 'play')
        base_score = engagement_scores.get(event_type, 1.0)
        
        # Add location bonus
        location = element.get('user_location', '').lower()
        if 'new york' in location or 'los angeles' in location:
            base_score *= 1.2
        elif 'london' in location or 'miami' in location:
            base_score *= 1.1
        
        element['engagement_score'] = base_score
        element['engagement_level'] = 'high' if base_score > 1.5 else 'medium' if base_score > 0.8 else 'low'
        
        yield element

class GenreAnalytics(beam.DoFn):
    """Generate genre-based analytics."""
    
    def process(self, element):
        if element is None:
            return
        
        genre = element.get('genre', '').lower()
        
        # Genre popularity mapping
        genre_popularity = {
            'rock': 0.9,
            'pop': 0.8,
            'hip_hop': 0.7,
            'electronic': 0.6,
            'jazz': 0.5,
            'classical': 0.4
        }
        
        popularity = genre_popularity.get(genre, 0.5)
        element['genre_popularity'] = popularity
        element['is_popular_genre'] = popularity > 0.7
        
        yield element

class PlatformAnalytics(beam.DoFn):
    """Generate platform-based analytics."""
    
    def process(self, element):
        if element is None:
            return
        
        platform = element.get('platform', '').lower()
        
        # Platform quality mapping
        platform_quality = {
            'spotify': 'high',
            'apple_music': 'high',
            'youtube_music': 'medium',
            'soundcloud': 'medium'
        }
        
        element['platform_quality'] = platform_quality.get(platform, 'unknown')
        element['is_premium_platform'] = platform in ['spotify', 'apple_music']
        
        yield element

class TimeWindowAnalytics(beam.DoFn):
    """Generate time-based analytics."""
    
    def process(self, element):
        if element is None:
            return
        
        try:
            timestamp = datetime.fromisoformat(element.get('timestamp', '').replace('Z', '+00:00'))
            hour = timestamp.hour
            
            # Time-based engagement patterns
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
            
            element['time_context'] = time_context
            element['time_multiplier'] = time_multiplier
            element['adjusted_engagement'] = element.get('engagement_score', 1.0) * time_multiplier
            
        except Exception as e:
            logger.error(f"Error processing timestamp: {e}")
            element['time_context'] = 'unknown'
            element['time_multiplier'] = 1.0
            element['adjusted_engagement'] = element.get('engagement_score', 1.0)
        
        yield element

def run_pipeline():
    """Run the Dataflow pipeline."""
    
    # Pipeline options
    pipeline_options = PipelineOptions([
        '--project=mystage-claudellm',
        '--region=us-central1',
        '--temp_location=gs://mystage-claudellm-music-pipeline-dev/temp',
        '--staging_location=gs://mystage-claudellm-music-pipeline-dev/staging',
        '--runner=DataflowRunner',
        '--job_name=music-analytics-pipeline',
        '--setup_file=./setup.py',
        '--requirements_file=requirements.txt',
        '--save_main_session',
        '--max_num_workers=10',
        '--autoscaling_algorithm=THROUGHPUT_BASED',
        '--worker_machine_type=n1-standard-2'
    ])
    
    with beam.Pipeline(options=pipeline_options) as pipeline:
        
        # Read from Pub/Sub
        events = (
            pipeline
            | 'Read from Pub/Sub' >> ReadFromPubSub(
                topic='projects/mystage-claudellm/topics/raw-music-events-dev'
            )
        )
        
        # Process events
        processed_events = (
            events
            | 'Process Events' >> beam.ParDo(MusicEventProcessor())
            | 'Calculate Engagement' >> beam.ParDo(EngagementCalculator())
            | 'Genre Analytics' >> beam.ParDo(GenreAnalytics())
            | 'Platform Analytics' >> beam.ParDo(PlatformAnalytics())
            | 'Time Analytics' >> beam.ParDo(TimeWindowAnalytics())
        )
        
        # Window and aggregate
        windowed_events = (
            processed_events
            | 'Window Events' >> beam.WindowInto(
                window.FixedWindows(300),  # 5-minute windows
                trigger=trigger.AfterWatermark(),
                accumulation_mode=trigger.AccumulationMode.ACCUMULATING
            )
        )
        
        # Real-time aggregations
        engagement_metrics = (
            windowed_events
            | 'Key by Event Type' >> beam.Map(lambda x: (x.get('event_type', 'unknown'), x))
            | 'Group by Event Type' >> beam.GroupByKey()
            | 'Calculate Event Metrics' >> beam.Map(lambda x: {
                'event_type': x[0],
                'count': len(x[1]),
                'avg_engagement': sum(e.get('engagement_score', 0) for e in x[1]) / len(x[1]),
                'window_start': datetime.utcnow().isoformat()
            })
        )
        
        genre_metrics = (
            windowed_events
            | 'Key by Genre' >> beam.Map(lambda x: (x.get('genre', 'unknown'), x))
            | 'Group by Genre' >> beam.GroupByKey()
            | 'Calculate Genre Metrics' >> beam.Map(lambda x: {
                'genre': x[0],
                'count': len(x[1]),
                'avg_popularity': sum(e.get('genre_popularity', 0) for e in x[1]) / len(x[1]),
                'window_start': datetime.utcnow().isoformat()
            })
        )
        
        platform_metrics = (
            windowed_events
            | 'Key by Platform' >> beam.Map(lambda x: (x.get('platform', 'unknown'), x))
            | 'Group by Platform' >> beam.GroupByKey()
            | 'Calculate Platform Metrics' >> beam.Map(lambda x: {
                'platform': x[0],
                'count': len(x[1]),
                'premium_ratio': sum(1 for e in x[1] if e.get('is_premium_platform', False)) / len(x[1]),
                'window_start': datetime.utcnow().isoformat()
            })
        )
        
        # Write to BigQuery
        processed_events | 'Write Processed Events' >> WriteToBigQuery(
            'mystage-claudellm:music_analytics_dev.processed_events',
            schema='event_id:STRING,event_type:STRING,track_title:STRING,artist_name:STRING,genre:STRING,platform:STRING,user_location:STRING,timestamp:STRING,processing_time:STRING,engagement_score:FLOAT,engagement_level:STRING,genre_popularity:FLOAT,is_popular_genre:BOOLEAN,platform_quality:STRING,is_premium_platform:BOOLEAN,time_context:STRING,time_multiplier:FLOAT,adjusted_engagement:FLOAT'
        )
        
        engagement_metrics | 'Write Engagement Metrics' >> WriteToBigQuery(
            'mystage-claudellm:music_analytics_dev.engagement_metrics',
            schema='event_type:STRING,count:INTEGER,avg_engagement:FLOAT,window_start:STRING'
        )
        
        genre_metrics | 'Write Genre Metrics' >> WriteToBigQuery(
            'mystage-claudellm:music_analytics_dev.genre_metrics',
            schema='genre:STRING,count:INTEGER,avg_popularity:FLOAT,window_start:STRING'
        )
        
        platform_metrics | 'Write Platform Metrics' >> WriteToBigQuery(
            'mystage-claudellm:music_analytics_dev.platform_metrics',
            schema='platform:STRING,count:INTEGER,premium_ratio:FLOAT,window_start:STRING'
        )

if __name__ == '__main__':
    run_pipeline() 