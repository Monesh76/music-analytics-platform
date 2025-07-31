"""
Cloud Function for Claude LLM enrichment of music events.
Triggered by Pub/Sub messages and enriches event descriptions using Claude API.
"""

import json
import base64
import logging
from datetime import datetime
from typing import Dict, List, Optional

import functions_framework
from anthropic import Anthropic
from google.cloud import pubsub_v1
from google.cloud import bigquery
from pydantic import ValidationError

from src.models.music_events import MusicEvent, EnrichedMusicEvent, Genre
from src.utils.config import get_config
from src.utils.logging_util import setup_logging


# Setup logging
logger = setup_logging("claude-enrichment-function")

# Initialize clients
config = get_config()
anthropic_client = Anthropic(api_key=config.claude_api_key)
bigquery_client = bigquery.Client()
publisher = pubsub_v1.PublisherClient()

# BigQuery table reference
table_ref = bigquery_client.dataset(config.bigquery_dataset).table(config.enriched_events_table)

# Pub/Sub topic for enriched events
ENRICHED_EVENTS_TOPIC = publisher.topic_path(
    config.google_cloud_project,
    config.enriched_events_topic
)


@functions_framework.cloud_event
def enrich_music_event(cloud_event) -> None:
    """
    Cloud Function triggered by Pub/Sub to enrich music events with Claude LLM.
    
    Expected message format:
    - data: base64 encoded JSON of MusicEvent
    - attributes: event metadata
    """
    
    try:
        # Decode Pub/Sub message
        if 'data' in cloud_event.data:
            message_data = base64.b64decode(cloud_event.data['data']).decode('utf-8')
        else:
            logger.error("No data in Pub/Sub message")
            return
        
        # Parse music event
        try:
            event_data = json.loads(message_data)
            music_event = MusicEvent(**event_data)
            logger.info(f"Processing event for enrichment: {music_event.event_id}")
            
        except (json.JSONDecodeError, ValidationError) as e:
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
        Dictionary containing enrichment data or None if failed
    """
    
    try:
        # Prepare context for Claude
        context = prepare_event_context(music_event)
        
        # Generate enhanced description
        enhanced_description = generate_event_description(context)
        
        # Analyze mood and emotion
        mood_analysis = analyze_mood(context)
        
        # Predict genres
        genre_predictions = predict_genres(context)
        
        # Infer listening context
        listening_context = infer_listening_context(context)
        
        # Generate similar track recommendations
        similar_tracks = generate_similar_tracks(context)
        
        # Calculate confidence score based on available data
        confidence = calculate_enrichment_confidence(music_event)
        
        enrichments = {
            'enhanced_description': enhanced_description,
            'mood_analysis': mood_analysis,
            'genre_prediction': genre_predictions,
            'listening_context': listening_context,
            'similar_tracks': similar_tracks,
            'enrichment_confidence': confidence,
            'enrichment_model': 'claude-3-sonnet'
        }
        
        # Filter out None values
        return {k: v for k, v in enrichments.items() if v is not None}
        
    except Exception as e:
        logger.error(f"Claude enrichment failed: {e}")
        return None


def prepare_event_context(music_event: MusicEvent) -> str:
    """Prepare context string for Claude analysis."""
    
    track = music_event.track
    artist = music_event.artist
    user = music_event.user_interaction
    streaming = music_event.streaming_event
    
    context_parts = [
        f"Event Type: {music_event.event_type.value}",
        f"Track: '{track.name}' by {artist.name}",
        f"Platform: {streaming.platform.value}",
    ]
    
    if track.genres:
        context_parts.append(f"Track Genres: {', '.join([g.value for g in track.genres])}")
    
    if track.duration_ms:
        duration_min = track.duration_ms / 60000
        context_parts.append(f"Duration: {duration_min:.1f} minutes")
    
    if track.energy is not None:
        context_parts.append(f"Energy Level: {track.energy:.2f}")
    
    if track.valence is not None:
        context_parts.append(f"Valence (Positivity): {track.valence:.2f}")
    
    if track.tempo:
        context_parts.append(f"Tempo: {track.tempo:.0f} BPM")
    
    if user.device_type:
        context_parts.append(f"Device: {user.device_type}")
    
    if user.location:
        context_parts.append(f"Location: {user.location}")
    
    # Add play-specific context
    if music_event.play_event:
        play = music_event.play_event
        duration_played = play.played_duration_ms / 1000
        context_parts.append(f"Played Duration: {duration_played:.1f} seconds")
        
        if play.skip_reason:
            context_parts.append(f"Skip Reason: {play.skip_reason}")
        
        if play.shuffle_mode:
            context_parts.append("Shuffle Mode: ON")
        
        if play.repeat_mode != "off":
            context_parts.append(f"Repeat Mode: {play.repeat_mode}")
    
    return " | ".join(context_parts)


def generate_event_description(context: str) -> Optional[str]:
    """Generate enhanced event description using Claude."""
    
    try:
        prompt = f"""
        Given this music streaming event context, generate a concise, engaging description 
        that captures the listening experience. Focus on the musical qualities, user behavior, 
        and contextual elements. Keep it under 200 characters.

        Context: {context}

        Generate a description that would be interesting for music analytics and user engagement:
        """
        
        response = anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}]
        )
        
        description = response.content[0].text.strip()
        
        # Ensure description is within limits
        if len(description) > 200:
            description = description[:197] + "..."
        
        return description
        
    except Exception as e:
        logger.error(f"Failed to generate description: {e}")
        return None


def analyze_mood(context: str) -> Optional[str]:
    """Analyze mood and emotion from the music event."""
    
    try:
        prompt = f"""
        Analyze the mood and emotional characteristics of this music streaming event.
        Consider the musical attributes, user behavior, and listening context.

        Context: {context}

        Provide a brief mood analysis (1-2 words max) such as:
        - energetic
        - relaxed
        - melancholic
        - upbeat
        - contemplative
        - nostalgic
        - focused
        - celebratory

        Return only the mood descriptor:
        """
        
        response = anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=50,
            messages=[{"role": "user", "content": prompt}]
        )
        
        mood = response.content[0].text.strip().lower()
        
        # Validate mood is reasonable length
        if len(mood.split()) <= 2:
            return mood
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to analyze mood: {e}")
        return None


def predict_genres(context: str) -> Optional[List[Genre]]:
    """Predict additional genres using Claude."""
    
    try:
        # Get valid genre values for the prompt
        valid_genres = [g.value for g in Genre]
        
        prompt = f"""
        Based on this music streaming context, predict 1-3 additional genres that might 
        apply to this track. Consider the musical attributes and user behavior patterns.

        Context: {context}

        Valid genres to choose from: {', '.join(valid_genres)}

        Return only genre names separated by commas, or "none" if no additional genres apply:
        """
        
        response = anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}]
        )
        
        genres_text = response.content[0].text.strip().lower()
        
        if genres_text == "none":
            return None
        
        # Parse and validate genres
        predicted_genres = []
        for genre_name in genres_text.split(','):
            genre_name = genre_name.strip()
            try:
                genre = Genre(genre_name)
                predicted_genres.append(genre)
            except ValueError:
                continue
        
        return predicted_genres if predicted_genres else None
        
    except Exception as e:
        logger.error(f"Failed to predict genres: {e}")
        return None


def infer_listening_context(context: str) -> Optional[str]:
    """Infer the listening context/activity."""
    
    try:
        prompt = f"""
        Based on this music streaming event, infer the likely listening context or activity.
        Consider the time, device, user behavior, and musical characteristics.

        Context: {context}

        Provide a brief context description (2-3 words max) such as:
        - workout
        - commute
        - work/focus
        - relaxation
        - party/social
        - study
        - sleep
        - cooking
        - background

        Return only the context descriptor:
        """
        
        response = anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=50,
            messages=[{"role": "user", "content": prompt}]
        )
        
        listening_context = response.content[0].text.strip().lower()
        
        # Validate context is reasonable length
        if len(listening_context.split()) <= 3:
            return listening_context
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to infer listening context: {e}")
        return None


def generate_similar_tracks(context: str) -> Optional[List[str]]:
    """Generate similar track recommendations."""
    
    try:
        prompt = f"""
        Based on this music streaming event, suggest 2-3 similar tracks that a user might enjoy.
        Consider the musical style, artist, and listening context.

        Context: {context}

        Return track suggestions in format "Artist - Track Name", separated by commas.
        If you cannot suggest similar tracks, return "none":
        """
        
        response = anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        
        suggestions_text = response.content[0].text.strip()
        
        if suggestions_text.lower() == "none":
            return None
        
        # Parse track suggestions
        suggestions = [track.strip() for track in suggestions_text.split(',')]
        return suggestions[:3]  # Limit to 3 suggestions
        
    except Exception as e:
        logger.error(f"Failed to generate similar tracks: {e}")
        return None


def calculate_enrichment_confidence(music_event: MusicEvent) -> float:
    """Calculate confidence score for enrichments based on available data."""
    
    confidence_factors = []
    
    # Track metadata completeness
    track = music_event.track
    if track.genres:
        confidence_factors.append(0.2)
    if track.energy is not None:
        confidence_factors.append(0.15)
    if track.valence is not None:
        confidence_factors.append(0.15)
    if track.tempo:
        confidence_factors.append(0.1)
    if track.popularity is not None:
        confidence_factors.append(0.1)
    
    # User context completeness
    user = music_event.user_interaction
    if user.device_type:
        confidence_factors.append(0.1)
    if user.location:
        confidence_factors.append(0.1)
    
    # Play event data
    if music_event.play_event:
        confidence_factors.append(0.1)
    
    return min(sum(confidence_factors), 1.0)


def store_enriched_event(enriched_event: EnrichedMusicEvent) -> None:
    """Store enriched event in BigQuery."""
    
    try:
        # Convert to BigQuery row format
        row = {
            'event_id': enriched_event.event_id,
            'event_type': enriched_event.event_type.value,
            'timestamp': enriched_event.timestamp,
            'track_id': enriched_event.track.id,
            'track_name': enriched_event.track.name,
            'artist_id': enriched_event.artist.id,
            'artist_name': enriched_event.artist.name,
            'album_id': enriched_event.album.id if enriched_event.album else None,
            'album_name': enriched_event.album.name if enriched_event.album else None,
            'platform': enriched_event.streaming_event.platform.value,
            'user_id': enriched_event.user_interaction.user_id,
            'session_id': enriched_event.user_interaction.session_id,
            'enhanced_description': enriched_event.enhanced_description,
            'mood_analysis': enriched_event.mood_analysis,
            'listening_context': enriched_event.listening_context,
            'enrichment_timestamp': enriched_event.enrichment_timestamp,
            'processing_timestamp': enriched_event.processing_timestamp,
        }
        
        # Insert row
        errors = bigquery_client.insert_rows_json(table_ref, [row])
        
        if errors:
            logger.error(f"BigQuery insert errors: {errors}")
        else:
            logger.info(f"Stored enriched event in BigQuery: {enriched_event.event_id}")
            
    except Exception as e:
        logger.error(f"Failed to store in BigQuery: {e}")
        raise


def publish_enriched_event(enriched_event: EnrichedMusicEvent) -> None:
    """Publish enriched event to Pub/Sub for downstream processing."""
    
    try:
        event_data = enriched_event.json().encode('utf-8')
        
        future = publisher.publish(
            ENRICHED_EVENTS_TOPIC,
            event_data,
            event_id=enriched_event.event_id,
            event_type=enriched_event.event_type.value,
            enriched='true'
        )
        
        message_id = future.result()
        logger.info(f"Published enriched event: {message_id}")
        
    except Exception as e:
        logger.error(f"Failed to publish enriched event: {e}")
        raise 