# Real-Time Music Data Aggregation Pipeline Infrastructure
# Terraform configuration for Google Cloud Platform

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Variables
variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "Default region for resources"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "claude_api_key" {
  description = "Anthropic Claude API key"
  type        = string
  sensitive   = true
}

# Provider configuration
provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "pubsub.googleapis.com",
    "dataflow.googleapis.com",
    "bigquery.googleapis.com",
    "cloudfunctions.googleapis.com",
    "storage.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "cloudbuild.googleapis.com",
    "run.googleapis.com",
    "eventarc.googleapis.com",
    "secretmanager.googleapis.com"
  ])

  service = each.value
  project = var.project_id

  disable_on_destroy = false
}

# Cloud Storage bucket for pipeline artifacts
resource "google_storage_bucket" "pipeline_bucket" {
  name          = "${var.project_id}-music-pipeline-${var.environment}"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }

  versioning {
    enabled = true
  }
}

# Cloud Storage bucket folders
resource "google_storage_bucket_object" "pipeline_folders" {
  for_each = toset([
    "temp/",
    "staging/", 
    "functions/",
    "processed/",
    "failed/"
  ])

  name   = each.value
  bucket = google_storage_bucket.pipeline_bucket.name
  content = " "
}

# Pub/Sub topics
resource "google_pubsub_topic" "raw_events" {
  name = "raw-music-events-${var.environment}"

  message_retention_duration = "604800s" # 7 days

  depends_on = [google_project_service.required_apis]
}

resource "google_pubsub_topic" "enrichment_events" {
  name = "music-events-enrichment-${var.environment}"

  message_retention_duration = "604800s" # 7 days

  depends_on = [google_project_service.required_apis]
}

resource "google_pubsub_topic" "enriched_events" {
  name = "enriched-music-events-${var.environment}"

  message_retention_duration = "604800s" # 7 days

  depends_on = [google_project_service.required_apis]
}

# Pub/Sub subscriptions
resource "google_pubsub_subscription" "raw_events_dataflow" {
  name  = "raw-events-dataflow-${var.environment}"
  topic = google_pubsub_topic.raw_events.name

  ack_deadline_seconds = 20

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dead_letter.id
    max_delivery_attempts = 5
  }
}

resource "google_pubsub_subscription" "enrichment_events_function" {
  name  = "enrichment-events-function-${var.environment}"
  topic = google_pubsub_topic.enrichment_events.name

  ack_deadline_seconds = 60

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dead_letter.id
    max_delivery_attempts = 5
  }
}

# Dead letter topic for failed messages
resource "google_pubsub_topic" "dead_letter" {
  name = "dead-letter-${var.environment}"

  message_retention_duration = "2592000s" # 30 days
}

# BigQuery dataset
resource "google_bigquery_dataset" "music_analytics" {
  dataset_id  = "music_analytics_${var.environment}"
  description = "Real-time music event analytics dataset"
  location    = "US"

  delete_contents_on_destroy = var.environment != "prod"

  depends_on = [google_project_service.required_apis]
}

# Service account for Cloud Functions
resource "google_service_account" "cloud_functions_sa" {
  account_id   = "music-pipeline-functions-${var.environment}"
  display_name = "Music Pipeline Cloud Functions Service Account"
  description  = "Service account for music pipeline Cloud Functions"
}

# Service account for Dataflow
resource "google_service_account" "dataflow_sa" {
  account_id   = "music-pipeline-dataflow-${var.environment}"
  display_name = "Music Pipeline Dataflow Service Account"
  description  = "Service account for music pipeline Dataflow jobs"
}

# IAM roles for Cloud Functions service account
resource "google_project_iam_member" "functions_roles" {
  for_each = toset([
    "roles/pubsub.publisher",
    "roles/pubsub.subscriber",
    "roles/bigquery.dataEditor",
    "roles/storage.objectAdmin",
    "roles/logging.logWriter"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cloud_functions_sa.email}"
}

# IAM roles for Dataflow service account
resource "google_project_iam_member" "dataflow_roles" {
  for_each = toset([
    "roles/dataflow.worker",
    "roles/pubsub.subscriber",
    "roles/bigquery.dataEditor",
    "roles/storage.objectAdmin",
    "roles/logging.logWriter"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.dataflow_sa.email}"
}

# Secret Manager for Claude API key
resource "google_secret_manager_secret" "claude_api_key" {
  secret_id = "claude-api-key-${var.environment}"

  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "claude_api_key_version" {
  secret      = google_secret_manager_secret.claude_api_key.id
  secret_data = var.claude_api_key
}

# Grant Cloud Functions access to the secret
resource "google_secret_manager_secret_iam_member" "claude_api_key_access" {
  secret_id = google_secret_manager_secret.claude_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_functions_sa.email}"
}

# Cloud Function for ingestion (placeholder - will be deployed separately)
resource "google_cloudfunctions2_function" "ingestion_function" {
  name     = "music-event-ingestion-${var.environment}"
  location = var.region

  build_config {
    runtime     = "python311"
    entry_point = "ingest_music_event"
    
    source {
      storage_source {
        bucket = google_storage_bucket.pipeline_bucket.name
        object = "functions/ingestion.zip"
      }
    }
  }

  service_config {
    max_instance_count = 100
    min_instance_count = 1
    available_memory   = "512Mi"
    timeout_seconds    = 60
    
    environment_variables = {
      GOOGLE_CLOUD_PROJECT = var.project_id
      RAW_EVENTS_TOPIC    = google_pubsub_topic.raw_events.name
      ENRICHMENT_TOPIC    = google_pubsub_topic.enrichment_events.name
      BIGQUERY_DATASET    = google_bigquery_dataset.music_analytics.dataset_id
      ENVIRONMENT         = var.environment
    }

    service_account_email = google_service_account.cloud_functions_sa.email
  }

  depends_on = [google_project_service.required_apis]
}

# Cloud Function for Claude enrichment (placeholder)
resource "google_cloudfunctions2_function" "enrichment_function" {
  name     = "music-event-enrichment-${var.environment}"
  location = var.region

  build_config {
    runtime     = "python311"
    entry_point = "enrich_music_event"
    
    source {
      storage_source {
        bucket = google_storage_bucket.pipeline_bucket.name
        object = "functions/enrichment.zip"
      }
    }
  }

  service_config {
    max_instance_count = 50
    min_instance_count = 0
    available_memory   = "1Gi"
    timeout_seconds    = 540
    
    environment_variables = {
      GOOGLE_CLOUD_PROJECT     = var.project_id
      ENRICHED_EVENTS_TOPIC   = google_pubsub_topic.enriched_events.name
      BIGQUERY_DATASET        = google_bigquery_dataset.music_analytics.dataset_id
      CLAUDE_API_KEY_SECRET   = google_secret_manager_secret.claude_api_key.secret_id
      ENVIRONMENT             = var.environment
    }

    service_account_email = google_service_account.cloud_functions_sa.email
  }

  depends_on = [google_project_service.required_apis]
}

# Cloud Function for analytics processing
resource "google_cloudfunctions2_function" "analytics_function" {
  name     = "music-analytics-processor-${var.environment}"
  location = var.region

  build_config {
    runtime     = "python311"
    entry_point = "process_music_analytics"
    
    source {
      storage_source {
        bucket = google_storage_bucket.pipeline_bucket.name
        object = "functions/analytics.zip"
      }
    }
  }

  service_config {
    max_instance_count = 50
    min_instance_count = 0
    available_memory   = "1Gi"
    timeout_seconds    = 540
    
    environment_variables = {
      GOOGLE_CLOUD_PROJECT = var.project_id
      BIGQUERY_DATASET     = google_bigquery_dataset.music_analytics.dataset_id
      ENVIRONMENT          = var.environment
    }

    service_account_email = google_service_account.cloud_functions_sa.email
  }

  event_trigger {
    trigger_region = var.region
    event_type     = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic   = google_pubsub_topic.raw_events.id
  }

  depends_on = [google_project_service.required_apis]
}

# Monitoring and alerting
resource "google_monitoring_notification_channel" "email" {
  count = var.environment == "prod" ? 1 : 0
  
  display_name = "Email Notifications"
  type         = "email"

  labels = {
    email_address = "alerts@yourcompany.com"
  }

  depends_on = [google_project_service.required_apis]
}

# Alerting policy for pipeline health
resource "google_monitoring_alert_policy" "pipeline_health" {
  count = var.environment == "prod" ? 1 : 0

  display_name = "Music Pipeline Health Alert"
  combiner     = "OR"

  conditions {
    display_name = "High Error Rate"

    condition_threshold {
      filter         = "resource.type=\"cloud_function\" AND metric.type=\"cloudfunctions.googleapis.com/function/execution_count\""
      duration       = "300s"
      comparison     = "COMPARISON_GT"
      threshold_value = 10

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email[0].name]

  depends_on = [google_project_service.required_apis]
}

# Outputs
output "project_id" {
  description = "Google Cloud Project ID"
  value       = var.project_id
}

output "pipeline_bucket" {
  description = "Cloud Storage bucket for pipeline artifacts"
  value       = google_storage_bucket.pipeline_bucket.name
}

output "bigquery_dataset" {
  description = "BigQuery dataset for analytics"
  value       = google_bigquery_dataset.music_analytics.dataset_id
}

output "pubsub_topics" {
  description = "Pub/Sub topics"
  value = {
    raw_events        = google_pubsub_topic.raw_events.name
    enrichment_events = google_pubsub_topic.enrichment_events.name
    enriched_events   = google_pubsub_topic.enriched_events.name
  }
}

output "cloud_functions" {
  description = "Cloud Functions"
  value = {
    ingestion_function   = google_cloudfunctions2_function.ingestion_function.name
    enrichment_function  = google_cloudfunctions2_function.enrichment_function.name
  }
} 