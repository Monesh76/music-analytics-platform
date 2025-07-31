"""
Debug Cloud Function to understand Eventarc Pub/Sub trigger format.
"""

import json
import base64
import os
import logging
from datetime import datetime

import functions_framework

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@functions_framework.cloud_event
def debug_enrichment(cloud_event) -> None:
    """
    Debug function to understand Eventarc Pub/Sub trigger format.
    """
    
    try:
        logger.info("=" * 60)
        logger.info("DEBUG: ENRICHMENT FUNCTION TRIGGERED")
        logger.info("=" * 60)
        
        # Log the entire cloud event
        logger.info(f"Cloud event type: {type(cloud_event)}")
        logger.info(f"Cloud event attributes: {cloud_event.attributes}")
        logger.info(f"Cloud event data type: {type(cloud_event.data)}")
        logger.info(f"Cloud event data: {cloud_event.data}")
        
        # Try different parsing approaches
        message_data = None
        
        # Approach 1: Direct string (Eventarc format)
        if isinstance(cloud_event.data, str):
            logger.info("APPROACH 1: Direct string (Eventarc format)")
            try:
                message_data = base64.b64decode(cloud_event.data).decode('utf-8')
                logger.info("✅ SUCCESS: Decoded base64 string")
                logger.info(f"Decoded data: {message_data[:200]}...")
            except Exception as e:
                logger.error(f"❌ FAILED: {e}")
        
        # Approach 2: Dict with 'data' field (Pub/Sub format)
        elif isinstance(cloud_event.data, dict):
            logger.info("APPROACH 2: Dict with 'data' field (Pub/Sub format)")
            if 'data' in cloud_event.data:
                try:
                    encoded_data = cloud_event.data['data']
                    message_data = base64.b64decode(encoded_data).decode('utf-8')
                    logger.info("✅ SUCCESS: Decoded dict['data']")
                    logger.info(f"Decoded data: {message_data[:200]}...")
                except Exception as e:
                    logger.error(f"❌ FAILED: {e}")
            else:
                logger.error("❌ FAILED: No 'data' field in dict")
        
        # Approach 3: Dict with 'message' field
        elif isinstance(cloud_event.data, dict) and 'message' in cloud_event.data:
            logger.info("APPROACH 3: Dict with 'message' field")
            if 'data' in cloud_event.data['message']:
                try:
                    encoded_data = cloud_event.data['message']['data']
                    message_data = base64.b64decode(encoded_data).decode('utf-8')
                    logger.info("✅ SUCCESS: Decoded message['data']")
                    logger.info(f"Decoded data: {message_data[:200]}...")
                except Exception as e:
                    logger.error(f"❌ FAILED: {e}")
            else:
                logger.error("❌ FAILED: No 'data' field in message")
        
        else:
            logger.error(f"❌ UNKNOWN FORMAT: {type(cloud_event.data)}")
        
        if message_data:
            # Try to parse as JSON
            try:
                event_data = json.loads(message_data)
                logger.info("✅ SUCCESS: Parsed as JSON")
                logger.info(f"Event ID: {event_data.get('event_id', 'N/A')}")
                logger.info(f"Event Type: {event_data.get('event_type', 'N/A')}")
                logger.info(f"Track: {event_data.get('track', {}).get('title', 'N/A')}")
            except Exception as e:
                logger.error(f"❌ FAILED to parse JSON: {e}")
        
        logger.info("=" * 60)
        logger.info("DEBUG COMPLETE")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Debug function failed: {str(e)}", exc_info=True)
        raise


@functions_framework.http
def health_check(request):
    """Health check endpoint."""
    return (json.dumps({
        "status": "healthy",
        "service": "enrichment-debug",
        "timestamp": datetime.utcnow().isoformat()
    }), 200, {'Content-Type': 'application/json'}) 