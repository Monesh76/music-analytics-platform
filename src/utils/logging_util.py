"""
Logging utilities for the music data pipeline.
Provides structured logging with Google Cloud integration.
"""

import logging
import sys
from typing import Optional

import structlog
from google.cloud import logging as cloud_logging

from .config import get_config, is_production


def setup_logging(service_name: str) -> structlog.stdlib.BoundLogger:
    """
    Setup structured logging for the service.
    
    Args:
        service_name: Name of the service for log identification
        
    Returns:
        Configured structured logger
    """
    
    config = get_config()
    
    # Configure Python logging
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper()),
        format="%(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # Setup Google Cloud Logging in production
    if is_production():
        try:
            cloud_client = cloud_logging.Client()
            cloud_handler = cloud_client.get_default_handler()
            cloud_logger = logging.getLogger()
            cloud_logger.addHandler(cloud_handler)
            cloud_logger.setLevel(getattr(logging, config.log_level.upper()))
        except Exception as e:
            # Fallback to console logging if Cloud Logging fails
            print(f"Failed to setup Cloud Logging: {e}")
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            # Add JSON formatting for production
            structlog.processors.JSONRenderer() if is_production() 
            else structlog.dev.ConsoleRenderer(colors=True),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Create logger with service context
    logger = structlog.get_logger(service_name)
    logger = logger.bind(service=service_name, environment=_get_environment())
    
    return logger


def _get_environment() -> str:
    """Get the current environment name."""
    from .config import is_production, is_development, is_testing
    
    if is_production():
        return "production"
    elif is_testing():
        return "testing"
    elif is_development():
        return "development"
    else:
        return "unknown"


def log_event_processing(
    logger: structlog.stdlib.BoundLogger,
    event_id: str,
    event_type: str,
    status: str,
    **kwargs
) -> None:
    """
    Log event processing with standardized format.
    
    Args:
        logger: Structured logger instance
        event_id: Unique event identifier
        event_type: Type of music event
        status: Processing status (started, completed, failed)
        **kwargs: Additional context data
    """
    
    logger.info(
        "Event processing",
        event_id=event_id,
        event_type=event_type,
        status=status,
        **kwargs
    )


def log_pipeline_metrics(
    logger: structlog.stdlib.BoundLogger,
    pipeline_stage: str,
    events_processed: int,
    events_failed: int,
    processing_time_ms: float,
    **kwargs
) -> None:
    """
    Log pipeline performance metrics.
    
    Args:
        logger: Structured logger instance
        pipeline_stage: Name of the pipeline stage
        events_processed: Number of successfully processed events
        events_failed: Number of failed events
        processing_time_ms: Processing time in milliseconds
        **kwargs: Additional metrics
    """
    
    logger.info(
        "Pipeline metrics",
        pipeline_stage=pipeline_stage,
        events_processed=events_processed,
        events_failed=events_failed,
        processing_time_ms=processing_time_ms,
        success_rate=events_processed / (events_processed + events_failed) if (events_processed + events_failed) > 0 else 0,
        **kwargs
    )


def log_claude_enrichment(
    logger: structlog.stdlib.BoundLogger,
    event_id: str,
    enrichment_type: str,
    success: bool,
    confidence_score: Optional[float] = None,
    api_response_time_ms: Optional[float] = None,
    **kwargs
) -> None:
    """
    Log Claude LLM enrichment activity.
    
    Args:
        logger: Structured logger instance
        event_id: Event being enriched
        enrichment_type: Type of enrichment (description, mood, etc.)
        success: Whether enrichment was successful
        confidence_score: AI confidence score
        api_response_time_ms: API response time
        **kwargs: Additional context
    """
    
    log_data = {
        "activity": "claude_enrichment",
        "event_id": event_id,
        "enrichment_type": enrichment_type,
        "success": success,
    }
    
    if confidence_score is not None:
        log_data["confidence_score"] = confidence_score
    
    if api_response_time_ms is not None:
        log_data["api_response_time_ms"] = api_response_time_ms
    
    log_data.update(kwargs)
    
    if success:
        logger.info("Claude enrichment completed", **log_data)
    else:
        logger.warning("Claude enrichment failed", **log_data)


def log_bigquery_operation(
    logger: structlog.stdlib.BoundLogger,
    operation: str,
    table_name: str,
    rows_affected: int,
    success: bool,
    error_message: Optional[str] = None,
    **kwargs
) -> None:
    """
    Log BigQuery database operations.
    
    Args:
        logger: Structured logger instance
        operation: Type of operation (insert, update, query)
        table_name: BigQuery table name
        rows_affected: Number of rows affected
        success: Whether operation was successful
        error_message: Error message if failed
        **kwargs: Additional context
    """
    
    log_data = {
        "activity": "bigquery_operation",
        "operation": operation,
        "table_name": table_name,
        "rows_affected": rows_affected,
        "success": success,
    }
    
    if error_message:
        log_data["error_message"] = error_message
    
    log_data.update(kwargs)
    
    if success:
        logger.info("BigQuery operation completed", **log_data)
    else:
        logger.error("BigQuery operation failed", **log_data)


def log_pubsub_operation(
    logger: structlog.stdlib.BoundLogger,
    operation: str,
    topic_name: str,
    message_count: int,
    success: bool,
    message_ids: Optional[list] = None,
    **kwargs
) -> None:
    """
    Log Pub/Sub operations.
    
    Args:
        logger: Structured logger instance
        operation: Type of operation (publish, subscribe, ack)
        topic_name: Pub/Sub topic name
        message_count: Number of messages processed
        success: Whether operation was successful
        message_ids: List of message IDs if available
        **kwargs: Additional context
    """
    
    log_data = {
        "activity": "pubsub_operation",
        "operation": operation,
        "topic_name": topic_name,
        "message_count": message_count,
        "success": success,
    }
    
    if message_ids:
        log_data["message_ids"] = message_ids[:10]  # Limit to first 10 IDs
        log_data["total_message_ids"] = len(message_ids)
    
    log_data.update(kwargs)
    
    if success:
        logger.info("Pub/Sub operation completed", **log_data)
    else:
        logger.error("Pub/Sub operation failed", **log_data)


class EventProcessingContext:
    """Context manager for event processing logging."""
    
    def __init__(
        self, 
        logger: structlog.stdlib.BoundLogger,
        event_id: str,
        event_type: str,
        stage: str
    ):
        self.logger = logger
        self.event_id = event_id
        self.event_type = event_type
        self.stage = stage
        self.start_time = None
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        
        log_event_processing(
            self.logger,
            self.event_id,
            self.event_type,
            "started",
            stage=self.stage
        )
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        end_time = time.time()
        processing_time_ms = (end_time - self.start_time) * 1000
        
        if exc_type is None:
            # Success
            log_event_processing(
                self.logger,
                self.event_id,
                self.event_type,
                "completed",
                stage=self.stage,
                processing_time_ms=processing_time_ms
            )
        else:
            # Failure
            log_event_processing(
                self.logger,
                self.event_id,
                self.event_type,
                "failed",
                stage=self.stage,
                processing_time_ms=processing_time_ms,
                error_type=exc_type.__name__,
                error_message=str(exc_val)
            )
        
        return False  # Don't suppress exceptions


# Helper function to create processing context
def processing_context(
    logger: structlog.stdlib.BoundLogger,
    event_id: str,
    event_type: str,
    stage: str
) -> EventProcessingContext:
    """
    Create an event processing context manager.
    
    Usage:
        with processing_context(logger, event_id, event_type, "validation"):
            # Process event
            pass
    """
    return EventProcessingContext(logger, event_id, event_type, stage) 