#!/bin/bash

# Package Cloud Functions for deployment

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required environment variables are set
if [[ -z "$GOOGLE_CLOUD_PROJECT" ]]; then
    print_error "GOOGLE_CLOUD_PROJECT environment variable is not set"
    exit 1
fi

print_info "Packaging Cloud Functions..."

# Create temporary directories
mkdir -p /tmp/functions/ingestion
mkdir -p /tmp/functions/enrichment
mkdir -p /tmp/functions/analytics

# Copy function source code
print_info "Copying ingestion function..."
cp -r src/functions/ingestion_simple.py /tmp/functions/ingestion/main.py
cp requirements-dev-minimal.txt /tmp/functions/ingestion/requirements.txt

print_info "Copying enrichment function..."
cp -r src/functions/enrichment_http_working.py /tmp/functions/enrichment/main.py
cp requirements-dev-minimal.txt /tmp/functions/enrichment/requirements.txt

print_info "Copying analytics function..."
cp -r src/functions/analytics_processor.py /tmp/functions/analytics/main.py
cp requirements-dev-minimal.txt /tmp/functions/analytics/requirements.txt

# Create zip files
print_info "Creating ingestion function zip..."
cd /tmp/functions/ingestion
zip -r ingestion.zip . > /dev/null
cd -

print_info "Creating enrichment function zip..."
cd /tmp/functions/enrichment
zip -r enrichment.zip . > /dev/null
cd -

print_info "Creating analytics function zip..."
cd /tmp/functions/analytics
zip -r analytics.zip . > /dev/null
cd -

# Upload to Cloud Storage
print_info "Uploading functions to Cloud Storage..."

# Get bucket name from Terraform output or construct it
BUCKET_NAME="${GOOGLE_CLOUD_PROJECT}-music-pipeline-dev"

# Upload ingestion function
gsutil cp /tmp/functions/ingestion/ingestion.zip gs://${BUCKET_NAME}/functions/ingestion.zip

# Upload enrichment function
gsutil cp /tmp/functions/enrichment/enrichment.zip gs://${BUCKET_NAME}/functions/enrichment.zip

# Upload analytics function
gsutil cp /tmp/functions/analytics/analytics.zip gs://${BUCKET_NAME}/functions/analytics.zip

print_success "Cloud Functions packaged and uploaded successfully!"

# Clean up
rm -rf /tmp/functions

print_info "Functions are ready for deployment:"
echo "  - gs://${BUCKET_NAME}/functions/ingestion.zip"
echo "  - gs://${BUCKET_NAME}/functions/enrichment.zip"
echo "  - gs://${BUCKET_NAME}/functions/analytics.zip" 