"""
Cloud Function for music event data ingestion.
Validates incoming events and publishes to Pub/Sub for stream processing.
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Any

import functions_framework
from google.cloud import pubsub_v1
from pydantic import ValidationError

from src.models.music_events import MusicEvent
from src.utils.config import get_config
from src.utils.logging_util import setup_logging


# Setup logging
logger = setup_logging("ingestion-function")

# Initialize Pub/Sub publisher
publisher = pubsub_v1.PublisherClient()
config = get_config()

# Pub/Sub topic paths
RAW_EVENTS_TOPIC = publisher.topic_path(
    config.google_cloud_project, 
    config.raw_events_topic
)
ENRICHMENT_TOPIC = publisher.topic_path(
    config.google_cloud_project,
    config.enrichment_topic  
)


@functions_framework.http
def ingest_music_event(request) -> tuple[str, int]:
    """
    HTTP Cloud Function to ingest music events.
    
    Expected payload format:
    {
        "event_type": "play",
        "track": {...},
        "artist": {...},
        "user_interaction": {...},
        "streaming_event": {...},
        ...
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
            
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return (f'Data validation failed: {str(e)}', 400, headers)
        
        # Convert to JSON for Pub/Sub
        event_data = music_event.json().encode('utf-8')
        
        # Publish to raw events topic for main pipeline
        future_raw = publisher.publish(
            RAW_EVENTS_TOPIC,
            event_data,
            event_type=music_event.event_type.value,
            platform=music_event.streaming_event.platform.value,
            timestamp=music_event.timestamp.isoformat()
        )
        
        # Publish to enrichment topic for Claude LLM processing
        future_enrichment = publisher.publish(
            ENRICHMENT_TOPIC,
            event_data,
            event_id=music_event.event_id,
            event_type=music_event.event_type.value
        )
        
        # Wait for publish completion
        raw_message_id = future_raw.result()
        enrichment_message_id = future_enrichment.result()
        
        logger.info(
            f"Published event {music_event.event_id} - "
            f"Raw: {raw_message_id}, Enrichment: {enrichment_message_id}"
        )
        
        response = {
            'status': 'success',
            'event_id': music_event.event_id,
            'message_ids': {
                'raw_pipeline': raw_message_id,
                'enrichment_pipeline': enrichment_message_id
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return (json.dumps(response), 200, headers)
        
    except Exception as e:
        logger.error(f"Unexpected error processing event: {str(e)}", exc_info=True)
        return (f'Internal server error: {str(e)}', 500, headers)


@functions_framework.cloud_event
def process_batch_events(cloud_event) -> None:
    """
    Cloud Function triggered by Cloud Storage for batch event processing.
    Processes uploaded JSON files containing multiple music events.
    """
    
    try:
        # Extract file information from Cloud Event
        data = cloud_event.data
        bucket_name = data['bucket']
        file_name = data['name']
        
        logger.info(f"Processing batch file: gs://{bucket_name}/{file_name}")
        
        # Download and process file
        from google.cloud import storage
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        
        # Download file content
        content = blob.download_as_text()
        events_data = json.loads(content)
        
        if not isinstance(events_data, list):
            events_data = [events_data]
        
        successful_events = 0
        failed_events = 0
        
        # Process each event
        for event_data in events_data:
            try:
                # Validate event
                music_event = MusicEvent(**event_data)
                
                # Publish to Pub/Sub
                event_json = music_event.json().encode('utf-8')
                
                # Publish to both topics
                future_raw = publisher.publish(
                    RAW_EVENTS_TOPIC,
                    event_json,
                    event_type=music_event.event_type.value,
                    platform=music_event.streaming_event.platform.value,
                    batch_file=file_name
                )
                
                future_enrichment = publisher.publish(
                    ENRICHMENT_TOPIC,
                    event_json,
                    event_id=music_event.event_id,
                    batch_file=file_name
                )
                
                # Wait for completion
                future_raw.result()
                future_enrichment.result()
                
                successful_events += 1
                
            except ValidationError as e:
                logger.error(f"Validation failed for event: {e}")
                failed_events += 1
                continue
                
            except Exception as e:
                logger.error(f"Failed to process event: {e}")
                failed_events += 1
                continue
        
        logger.info(
            f"Batch processing complete - "
            f"Success: {successful_events}, Failed: {failed_events}"
        )
        
        # Move processed file to archive folder
        archive_blob = bucket.blob(f"processed/{file_name}")
        archive_blob.upload_from_string(content)
        blob.delete()
        
        logger.info(f"Archived file to: gs://{bucket_name}/processed/{file_name}")
        
    except Exception as e:
        logger.error(f"Batch processing failed: {str(e)}", exc_info=True)
        raise


def validate_event_data(event_data: Dict[str, Any]) -> bool:
    """
    Additional validation for business rules.
    
    Args:
        event_data: Raw event data dictionary
        
    Returns:
        True if event passes business validation
    """
    
    # Check for required platform-specific fields
    platform = event_data.get('streaming_event', {}).get('platform')
    if not platform:
        return False
    
    # Platform-specific validation
    if platform == 'spotify':
        # Spotify events must have track popularity
        track = event_data.get('track', {})
        if 'popularity' not in track:
            return False
    
    # Check for suspicious user patterns (basic fraud detection)
    user_interaction = event_data.get('user_interaction', {})
    user_id = user_interaction.get('user_id')
    
    # Reject events with invalid user IDs
    if not user_id or len(user_id) < 8:
        return False
    
    return True


# Health check endpoint
@functions_framework.http  
def health_check(request) -> tuple[str, int]:
    """Health check endpoint for monitoring."""
    
    headers = {'Access-Control-Allow-Origin': '*'}
    
    try:
        # Test Pub/Sub connection
        topics = list(publisher.list_topics(
            request={"project": f"projects/{config.google_cloud_project}"}
        ))
        
        response = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'topics_count': len(topics),
            'function': 'music-event-ingestion'
        }
        
        return (json.dumps(response), 200, headers)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        response = {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
        return (json.dumps(response), 500, headers) 