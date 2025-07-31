"""
Configuration management for the music data pipeline.
Handles environment variables and configuration settings.
"""

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


@dataclass
class Config:
    """Configuration settings for the music data pipeline."""
    
    # Google Cloud Project
    google_cloud_project: str
    
    # Pub/Sub Topics
    raw_events_topic: str
    enrichment_topic: str
    enriched_events_topic: str
    
    # BigQuery Settings
    bigquery_dataset: str
    raw_events_table: str
    enriched_events_table: str
    
    # Claude LLM API
    claude_api_key: str
    
    # Cloud Storage
    storage_bucket: str
    
    # Dataflow Settings
    dataflow_region: str
    dataflow_zone: str
    dataflow_temp_location: str
    dataflow_staging_location: str
    
    # Processing Settings
    batch_size: int = 100
    max_workers: int = 4
    
    # Monitoring
    enable_monitoring: bool = True
    log_level: str = "INFO"


def get_config() -> Config:
    """
    Get configuration from environment variables.
    
    Returns:
        Config object with all settings
        
    Raises:
        ValueError: If required environment variables are missing
    """
    
    # Required environment variables
    required_vars = [
        'GOOGLE_CLOUD_PROJECT',
        'CLAUDE_API_KEY',
        'BIGQUERY_DATASET',
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    # Build configuration
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    
    config = Config(
        # GCP Project
        google_cloud_project=project_id,
        
        # Pub/Sub Topics
        raw_events_topic=os.getenv('RAW_EVENTS_TOPIC', 'raw-music-events'),
        enrichment_topic=os.getenv('ENRICHMENT_TOPIC', 'music-events-enrichment'),
        enriched_events_topic=os.getenv('ENRICHED_EVENTS_TOPIC', 'enriched-music-events'),
        
        # BigQuery
        bigquery_dataset=os.getenv('BIGQUERY_DATASET'),
        raw_events_table=os.getenv('RAW_EVENTS_TABLE', 'raw_music_events'),
        enriched_events_table=os.getenv('ENRICHED_EVENTS_TABLE', 'enriched_music_events'),
        
        # Claude API
        claude_api_key=os.getenv('CLAUDE_API_KEY'),
        
        # Storage
        storage_bucket=os.getenv('STORAGE_BUCKET', f'{project_id}-music-pipeline'),
        
        # Dataflow
        dataflow_region=os.getenv('DATAFLOW_REGION', 'us-central1'),
        dataflow_zone=os.getenv('DATAFLOW_ZONE', 'us-central1-a'),
        dataflow_temp_location=os.getenv(
            'DATAFLOW_TEMP_LOCATION', 
            f'gs://{project_id}-music-pipeline/temp'
        ),
        dataflow_staging_location=os.getenv(
            'DATAFLOW_STAGING_LOCATION',
            f'gs://{project_id}-music-pipeline/staging'
        ),
        
        # Processing
        batch_size=int(os.getenv('BATCH_SIZE', '100')),
        max_workers=int(os.getenv('MAX_WORKERS', '4')),
        
        # Monitoring
        enable_monitoring=os.getenv('ENABLE_MONITORING', 'true').lower() == 'true',
        log_level=os.getenv('LOG_LEVEL', 'INFO'),
    )
    
    return config


def validate_config(config: Config) -> None:
    """
    Validate configuration settings.
    
    Args:
        config: Configuration object to validate
        
    Raises:
        ValueError: If configuration is invalid
    """
    
    # Validate batch size
    if config.batch_size < 1 or config.batch_size > 1000:
        raise ValueError("Batch size must be between 1 and 1000")
    
    # Validate worker count
    if config.max_workers < 1 or config.max_workers > 16:
        raise ValueError("Max workers must be between 1 and 16")
    
    # Validate log level
    valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if config.log_level.upper() not in valid_log_levels:
        raise ValueError(f"Log level must be one of: {', '.join(valid_log_levels)}")
    
    # Validate cloud storage paths
    if not config.dataflow_temp_location.startswith('gs://'):
        raise ValueError("Dataflow temp location must be a GCS path (gs://)")
    
    if not config.dataflow_staging_location.startswith('gs://'):
        raise ValueError("Dataflow staging location must be a GCS path (gs://)")


# Global configuration instance
_config: Optional[Config] = None


def get_global_config() -> Config:
    """Get the global configuration instance (singleton pattern)."""
    global _config
    
    if _config is None:
        _config = get_config()
        validate_config(_config)
    
    return _config


def reload_config() -> Config:
    """Reload configuration from environment variables."""
    global _config
    _config = None
    return get_global_config()


# Environment-specific configuration
def is_production() -> bool:
    """Check if running in production environment."""
    return os.getenv('ENVIRONMENT', 'development').lower() == 'production'


def is_development() -> bool:
    """Check if running in development environment."""
    return os.getenv('ENVIRONMENT', 'development').lower() == 'development'


def is_testing() -> bool:
    """Check if running in testing environment."""
    return os.getenv('ENVIRONMENT', 'development').lower() == 'testing' 