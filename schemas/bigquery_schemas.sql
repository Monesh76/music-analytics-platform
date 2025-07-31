-- BigQuery table schemas for Real-Time Music Data Aggregation Pipeline
-- Run these commands to create the required tables

-- Create dataset
CREATE SCHEMA IF NOT EXISTS `${PROJECT_ID}.music_analytics`
OPTIONS (
  description = "Real-time music event analytics dataset",
  location = "US"
);

-- Raw music events table (main events)
CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.music_analytics.raw_music_events` (
  -- Core event data
  event_id STRING NOT NULL,
  event_type STRING NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  processing_timestamp TIMESTAMP NOT NULL,
  
  -- Track information
  track_id STRING NOT NULL,
  track_name STRING NOT NULL,
  track_duration_ms INT64,
  track_explicit BOOL,
  track_popularity INT64,
  track_energy FLOAT64,
  track_valence FLOAT64,
  track_tempo FLOAT64,
  track_genres ARRAY<STRING>,
  
  -- Artist information
  artist_id STRING NOT NULL,
  artist_name STRING NOT NULL,
  artist_followers INT64,
  artist_verified BOOL,
  artist_country STRING,
  artist_genres ARRAY<STRING>,
  
  -- Album information
  album_id STRING,
  album_name STRING,
  album_release_date TIMESTAMP,
  
  -- User interaction
  user_id STRING NOT NULL,
  session_id STRING NOT NULL,
  device_type STRING,
  user_location STRING,
  subscription_type STRING,
  user_age_group STRING,
  
  -- Streaming platform
  platform STRING NOT NULL,
  stream_quality STRING,
  bandwidth_kbps INT64,
  buffer_events INT64,
  
  -- Play event details
  played_duration_ms INT64,
  skip_reason STRING,
  playlist_id STRING,
  shuffle_mode BOOL,
  repeat_mode STRING,
  
  -- Derived analytics fields
  hour_of_day INT64,
  day_of_week INT64,
  is_weekend BOOL,
  month INT64,
  year INT64,
  track_duration_seconds FLOAT64,
  is_long_track BOOL,
  is_short_track BOOL,
  play_completion_ratio FLOAT64,
  is_full_play BOOL,
  is_skip BOOL,
  engagement_score FLOAT64,
  platform_category STRING
)
PARTITION BY DATE(timestamp)
CLUSTER BY platform, artist_id, user_id
OPTIONS (
  description = "Raw music events with enriched metadata",
  partition_expiration_days = 90
);

-- Enriched music events table (Claude LLM enhanced)
CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.music_analytics.enriched_music_events` (
  -- All fields from raw events (inherited)
  event_id STRING NOT NULL,
  event_type STRING NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  processing_timestamp TIMESTAMP NOT NULL,
  track_id STRING NOT NULL,
  track_name STRING NOT NULL,
  artist_id STRING NOT NULL,
  artist_name STRING NOT NULL,
  album_id STRING,
  album_name STRING,
  platform STRING NOT NULL,
  user_id STRING NOT NULL,
  session_id STRING NOT NULL,
  
  -- Claude LLM enrichments
  enhanced_description STRING,
  mood_analysis STRING,
  genre_prediction ARRAY<STRING>,
  similar_tracks ARRAY<STRING>,
  listening_context STRING,
  
  -- Enrichment metadata
  enrichment_timestamp TIMESTAMP,
  enrichment_model STRING,
  enrichment_confidence FLOAT64
)
PARTITION BY DATE(timestamp)
CLUSTER BY platform, enrichment_model
OPTIONS (
  description = "Music events enriched with Claude LLM insights",
  partition_expiration_days = 90
);

-- Real-time aggregated metrics table
CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.music_analytics.music_event_metrics` (
  window_start TIMESTAMP NOT NULL,
  window_end TIMESTAMP NOT NULL,
  total_events INT64 NOT NULL,
  unique_users INT64 NOT NULL,
  unique_tracks INT64 NOT NULL,
  platform_distribution STRING, -- JSON string
  event_type_distribution STRING, -- JSON string
  average_engagement_score FLOAT64,
  aggregation_timestamp TIMESTAMP NOT NULL
)
PARTITION BY DATE(window_start)
CLUSTER BY window_start
OPTIONS (
  description = "Real-time aggregated metrics for monitoring and analytics",
  partition_expiration_days = 365
);

-- User analytics summary table
CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.music_analytics.user_analytics` (
  user_id STRING NOT NULL,
  analysis_date DATE NOT NULL,
  total_events INT64,
  total_play_time_ms INT64,
  unique_tracks INT64,
  unique_artists INT64,
  top_genre STRING,
  favorite_platform STRING,
  average_engagement_score FLOAT64,
  listening_sessions INT64,
  preferred_device STRING,
  most_active_hour INT64,
  skip_rate FLOAT64,
  completion_rate FLOAT64
)
PARTITION BY analysis_date
CLUSTER BY user_id
OPTIONS (
  description = "Daily user listening behavior analytics",
  partition_expiration_days = 365
);

-- Track popularity analytics table
CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.music_analytics.track_analytics` (
  track_id STRING NOT NULL,
  artist_id STRING NOT NULL,
  analysis_date DATE NOT NULL,
  total_plays INT64,
  unique_listeners INT64,
  total_play_time_ms INT64,
  average_completion_ratio FLOAT64,
  skip_rate FLOAT64,
  like_rate FLOAT64,
  share_rate FLOAT64,
  playlist_adds INT64,
  platform_distribution STRING, -- JSON
  geographic_distribution STRING, -- JSON
  peak_listening_hour INT64,
  trending_score FLOAT64
)
PARTITION BY analysis_date
CLUSTER BY track_id, artist_id
OPTIONS (
  description = "Track performance and popularity analytics",
  partition_expiration_days = 365
);

-- Platform analytics table
CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.music_analytics.platform_analytics` (
  platform STRING NOT NULL,
  analysis_date DATE NOT NULL,
  total_events INT64,
  unique_users INT64,
  total_streaming_time_ms INT64,
  average_session_duration_ms INT64,
  top_genre STRING,
  most_popular_artist STRING,
  most_popular_track STRING,
  average_engagement_score FLOAT64,
  premium_user_ratio FLOAT64,
  mobile_usage_ratio FLOAT64,
  peak_usage_hour INT64
)
PARTITION BY analysis_date
CLUSTER BY platform
OPTIONS (
  description = "Platform-specific usage analytics",
  partition_expiration_days = 365
);

-- Create views for common queries

-- Daily events summary view
CREATE OR REPLACE VIEW `${PROJECT_ID}.music_analytics.daily_events_summary` AS
SELECT 
  DATE(timestamp) as event_date,
  COUNT(*) as total_events,
  COUNT(DISTINCT user_id) as unique_users,
  COUNT(DISTINCT track_id) as unique_tracks,
  COUNT(DISTINCT artist_id) as unique_artists,
  AVG(engagement_score) as avg_engagement,
  SUM(CASE WHEN event_type = 'play' THEN 1 ELSE 0 END) as total_plays,
  SUM(CASE WHEN event_type = 'skip' THEN 1 ELSE 0 END) as total_skips,
  SUM(CASE WHEN event_type = 'like' THEN 1 ELSE 0 END) as total_likes
FROM `${PROJECT_ID}.music_analytics.raw_music_events`
WHERE DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY DATE(timestamp)
ORDER BY event_date DESC;

-- Top tracks view
CREATE OR REPLACE VIEW `${PROJECT_ID}.music_analytics.top_tracks_weekly` AS
SELECT 
  track_id,
  track_name,
  artist_name,
  COUNT(*) as play_count,
  COUNT(DISTINCT user_id) as unique_listeners,
  AVG(engagement_score) as avg_engagement,
  AVG(play_completion_ratio) as avg_completion
FROM `${PROJECT_ID}.music_analytics.raw_music_events`
WHERE DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
  AND event_type = 'play'
GROUP BY track_id, track_name, artist_name
HAVING play_count >= 10
ORDER BY play_count DESC, avg_engagement DESC
LIMIT 100;

-- Platform performance view
CREATE OR REPLACE VIEW `${PROJECT_ID}.music_analytics.platform_performance` AS
SELECT 
  platform,
  COUNT(*) as total_events,
  COUNT(DISTINCT user_id) as unique_users,
  AVG(engagement_score) as avg_engagement,
  SUM(played_duration_ms) / 1000 / 3600 as total_hours_streamed,
  COUNT(CASE WHEN is_full_play THEN 1 END) / COUNT(*) as completion_rate
FROM `${PROJECT_ID}.music_analytics.raw_music_events`
WHERE DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY platform
ORDER BY total_events DESC; 