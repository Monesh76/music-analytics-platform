#!/bin/bash

echo "🗑️  Cleaning up GCP resources to save costs..."
echo "=================================================="

# Set project
PROJECT_ID="mystage-claudellm"
REGION="us-central1"

echo "🔧 Setting project to: $PROJECT_ID"
gcloud config set project $PROJECT_ID

echo ""
echo "🗑️  Deleting Cloud Functions..."

# Delete Cloud Functions
echo "   Deleting enrichment function..."
gcloud functions delete music-event-enrichment-dev --region=$REGION --quiet || echo "   ⚠️  Enrichment function not found"

echo "   Deleting ingestion function..."
gcloud functions delete music-event-ingestion-dev --region=$REGION --quiet || echo "   ⚠️  Ingestion function not found"

echo "   Deleting analytics function..."
gcloud functions delete music-event-analytics-dev --region=$REGION --quiet || echo "   ⚠️  Analytics function not found"

echo ""
echo "🗑️  Deleting Pub/Sub topics and subscriptions..."

# Delete Pub/Sub topics and subscriptions
echo "   Deleting music-events-enrichment-dev topic..."
gcloud pubsub topics delete music-events-enrichment-dev --quiet || echo "   ⚠️  Topic not found"

echo "   Deleting enriched-music-events-dev topic..."
gcloud pubsub topics delete enriched-music-events-dev --quiet || echo "   ⚠️  Topic not found"

echo "   Deleting raw-music-events-dev topic..."
gcloud pubsub topics delete raw-music-events-dev --quiet || echo "   ⚠️  Topic not found"

echo ""
echo "🗑️  Deleting BigQuery tables..."

# Delete BigQuery tables
echo "   Deleting enriched_events table..."
bq rm --table $PROJECT_ID:music_analytics_dev.enriched_events --quiet || echo "   ⚠️  Table not found"

echo "   Deleting processed_events table..."
bq rm --table $PROJECT_ID:music_analytics_dev.processed_events --quiet || echo "   ⚠️  Table not found"

echo "   Deleting engagement_metrics table..."
bq rm --table $PROJECT_ID:music_analytics_dev.engagement_metrics --quiet || echo "   ⚠️  Table not found"

echo "   Deleting genre_metrics table..."
bq rm --table $PROJECT_ID:music_analytics_dev.genre_metrics --quiet || echo "   ⚠️  Table not found"

echo "   Deleting platform_metrics table..."
bq rm --table $PROJECT_ID:music_analytics_dev.platform_metrics --quiet || echo "   ⚠️  Table not found"

echo ""
echo "🗑️  Deleting Cloud Storage buckets..."

# Delete Cloud Storage buckets
echo "   Deleting function artifacts bucket..."
gsutil -m rm -r gs://$PROJECT_ID-music-pipeline-dev/ || echo "   ⚠️  Bucket not found"

echo ""
echo "🗑️  Deleting Terraform infrastructure..."

# Destroy Terraform infrastructure
cd infrastructure/terraform
terraform destroy -auto-approve || echo "   ⚠️  Terraform destroy failed"

echo ""
echo "✅ GCP cleanup completed!"
echo "💰 Resources deleted to save costs"
echo "🔧 You can now test locally without GCP charges" 