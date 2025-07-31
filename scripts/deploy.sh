#!/bin/bash

# Real-Time Music Data Aggregation Pipeline Deployment Script
# This script deploys the entire pipeline to Google Cloud Platform

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required environment variables are set
check_environment() {
    print_info "Checking environment variables..."
    
    required_vars=("GOOGLE_CLOUD_PROJECT" "CLAUDE_API_KEY")
    missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        print_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        echo ""
        echo "Please set these variables and run the script again:"
        echo "  export GOOGLE_CLOUD_PROJECT=your-project-id"
        echo "  export CLAUDE_API_KEY=your-claude-api-key"
        exit 1
    fi
    
    print_success "Environment variables check passed"
}

# Check if required tools are installed
check_dependencies() {
    print_info "Checking dependencies..."
    
    dependencies=("gcloud" "terraform" "python3")
    missing_deps=()
    
    # Check basic dependencies
    for dep in "${dependencies[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing_deps+=("$dep")
        fi
    done
    
    # Check for pip or pip3
    if command -v "pip" &> /dev/null; then
        PIP_CMD="pip"
    elif command -v "pip3" &> /dev/null; then
        PIP_CMD="pip3"
    else
        missing_deps+=("pip")
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        print_error "Missing required dependencies:"
        for dep in "${missing_deps[@]}"; do
            echo "  - $dep"
        done
        exit 1
    fi
    
    print_success "Dependencies check passed"
    print_info "Using pip command: $PIP_CMD"
}

# Authenticate with Google Cloud
authenticate() {
    print_info "Checking Google Cloud authentication..."
    
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        print_warning "Not authenticated with Google Cloud"
        print_info "Running gcloud auth login..."
        gcloud auth login
    fi
    
    # Set the project
    gcloud config set project "$GOOGLE_CLOUD_PROJECT"
    print_success "Google Cloud authentication configured"
}

# Install Python dependencies
install_python_deps() {
    print_info "Installing Python dependencies..."
    
    # Use the specialized installation script for Python 3.13 compatibility
    if [[ -f "scripts/install_dependencies.sh" ]]; then
        print_info "Using specialized dependency installation script..."
        ./scripts/install_dependencies.sh
    else
        print_warning "Specialized installation script not found, using standard method..."
        
        # Create virtual environment if it doesn't exist
        if [[ ! -d "venv" ]]; then
            python3 -m venv venv
        fi
        
        # Activate virtual environment
        source venv/bin/activate
        
        # Upgrade pip and setuptools first
        $PIP_CMD install --upgrade pip setuptools wheel
        
        # Install dependencies
        $PIP_CMD install -r requirements.txt
    fi
    
    print_success "Python dependencies installed"
}

# Deploy infrastructure with Terraform
deploy_infrastructure() {
    print_info "Deploying infrastructure with Terraform..."
    
    cd infrastructure/terraform
    
    # Initialize Terraform
    terraform init
    
    # Plan deployment
    terraform plan \
        -var="project_id=$GOOGLE_CLOUD_PROJECT" \
        -var="claude_api_key=$CLAUDE_API_KEY" \
        -var="environment=${ENVIRONMENT:-dev}"
    
    # Apply deployment
    print_warning "About to deploy infrastructure. Continue? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        terraform apply \
            -var="project_id=$GOOGLE_CLOUD_PROJECT" \
            -var="claude_api_key=$CLAUDE_API_KEY" \
            -var="environment=${ENVIRONMENT:-dev}" \
            -auto-approve
        print_success "Infrastructure deployed"
    else
        print_warning "Infrastructure deployment cancelled"
        exit 0
    fi
    
    cd ../..
}

# Create BigQuery tables
setup_bigquery() {
    print_info "Setting up BigQuery tables..."
    
    # Replace PROJECT_ID placeholder in SQL file
    sed "s/\${PROJECT_ID}/$GOOGLE_CLOUD_PROJECT/g" schemas/bigquery_schemas.sql > /tmp/bigquery_schemas_processed.sql
    
    # Execute SQL commands
    gcloud bq query \
        --use_legacy_sql=false \
        --format=none \
        < /tmp/bigquery_schemas_processed.sql
    
    # Clean up temporary file
    rm /tmp/bigquery_schemas_processed.sql
    
    print_success "BigQuery tables created"
}

# Package and deploy Cloud Functions
deploy_functions() {
    print_info "Deploying Cloud Functions..."
    
    # Create temporary directory for function packages
    mkdir -p temp/functions
    
    # Package ingestion function
    print_info "Packaging ingestion function..."
    cd temp/functions
    cp -r ../../src .
    cp ../../requirements.txt .
    zip -r ingestion.zip src/ requirements.txt
    
    # Upload to Cloud Storage
    BUCKET_NAME="$GOOGLE_CLOUD_PROJECT-music-pipeline-${ENVIRONMENT:-dev}"
    gsutil cp ingestion.zip "gs://$BUCKET_NAME/functions/"
    
    # Package enrichment function
    print_info "Packaging enrichment function..."
    zip -r enrichment.zip src/ requirements.txt
    gsutil cp enrichment.zip "gs://$BUCKET_NAME/functions/"
    
    cd ../..
    rm -rf temp/functions
    
    print_success "Cloud Functions deployed"
}

# Start Dataflow pipeline
start_dataflow() {
    print_info "Starting Dataflow pipeline..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Run the pipeline
    python -m src.pipeline.music_pipeline \
        --project="$GOOGLE_CLOUD_PROJECT" \
        --region="${DATAFLOW_REGION:-us-central1}" \
        --runner=DataflowRunner \
        --streaming \
        --temp_location="gs://$GOOGLE_CLOUD_PROJECT-music-pipeline-${ENVIRONMENT:-dev}/temp" \
        --staging_location="gs://$GOOGLE_CLOUD_PROJECT-music-pipeline-${ENVIRONMENT:-dev}/staging" \
        --job_name="music-pipeline-$(date +%Y%m%d-%H%M%S)"
    
    print_success "Dataflow pipeline started"
}

# Test the deployment
test_deployment() {
    print_info "Testing deployment..."
    
    # Create a test event
    cat > temp/test_event.json << EOF
{
    "event_type": "play",
    "track": {
        "id": "test-track-001",
        "name": "Test Song",
        "artist_id": "test-artist-001",
        "duration_ms": 210000,
        "popularity": 75,
        "energy": 0.8,
        "valence": 0.6,
        "tempo": 120.0,
        "genres": ["pop"]
    },
    "artist": {
        "id": "test-artist-001",
        "name": "Test Artist",
        "genres": ["pop"],
        "verified": true
    },
    "user_interaction": {
        "user_id": "test-user-001",
        "session_id": "test-session-001",
        "device_type": "mobile"
    },
    "streaming_event": {
        "platform": "spotify",
        "stream_quality": "high"
    },
    "play_event": {
        "played_duration_ms": 180000,
        "shuffle_mode": false,
        "repeat_mode": "off"
    }
}
EOF
    
    # Get the ingestion function URL
    FUNCTION_URL=$(gcloud functions describe music-event-ingestion-${ENVIRONMENT:-dev} \
        --region="${DATAFLOW_REGION:-us-central1}" \
        --format="value(serviceConfig.uri)" 2>/dev/null || echo "")
    
    if [[ -n "$FUNCTION_URL" ]]; then
        # Send test event
        curl -X POST "$FUNCTION_URL" \
            -H "Content-Type: application/json" \
            -d @temp/test_event.json
        
        print_success "Test event sent successfully"
    else
        print_warning "Could not find ingestion function URL for testing"
    fi
    
    # Clean up test file
    rm -f temp/test_event.json
}

# Show deployment information
show_info() {
    print_info "Deployment completed successfully!"
    echo ""
    echo "=== Deployment Information ==="
    echo "Project ID: $GOOGLE_CLOUD_PROJECT"
    echo "Environment: ${ENVIRONMENT:-dev}"
    echo "Region: ${DATAFLOW_REGION:-us-central1}"
    echo ""
    echo "=== Next Steps ==="
    echo "1. Check the Dataflow console for pipeline status:"
    echo "   https://console.cloud.google.com/dataflow/jobs"
    echo ""
    echo "2. Monitor BigQuery tables for incoming data:"
    echo "   https://console.cloud.google.com/bigquery"
    echo ""
    echo "3. View Cloud Function logs:"
    echo "   https://console.cloud.google.com/functions/list"
    echo ""
    echo "4. Send music events to the ingestion endpoint"
    echo ""
    echo "=== Useful Commands ==="
    echo "View Dataflow job status:"
    echo "  gcloud dataflow jobs list --region=${DATAFLOW_REGION:-us-central1}"
    echo ""
    echo "Check BigQuery data:"
    echo "  bq query 'SELECT COUNT(*) FROM \`$GOOGLE_CLOUD_PROJECT.music_analytics_${ENVIRONMENT:-dev}.raw_music_events\`'"
    echo ""
    echo "View function logs:"
    echo "  gcloud functions logs read music-event-ingestion-${ENVIRONMENT:-dev} --region=${DATAFLOW_REGION:-us-central1}"
}

# Cleanup function
cleanup() {
    print_info "Cleaning up temporary files..."
    rm -rf temp/
}

# Main deployment function
main() {
    print_info "Starting Real-Time Music Data Pipeline deployment..."
    
    # Create temp directory
    mkdir -p temp
    
    # Trap to ensure cleanup on exit
    trap cleanup EXIT
    
    # Run deployment steps
    check_environment
    check_dependencies
    authenticate
    install_python_deps
    deploy_infrastructure
    setup_bigquery
    deploy_functions
    start_dataflow
    test_deployment
    show_info
    
    print_success "Deployment completed successfully!"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --environment|-e)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --region|-r)
            DATAFLOW_REGION="$2"
            shift 2
            ;;
        --skip-test)
            SKIP_TEST=true
            shift
            ;;
        --dev-mode)
            DEV_MODE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --environment, -e   Environment name (default: dev)"
            echo "  --region, -r        Dataflow region (default: us-central1)"
            echo "  --skip-test         Skip deployment testing"
            echo "  --dev-mode          Use development mode (no Apache Beam)"
            echo "  --help, -h          Show this help message"
            echo ""
            echo "Required environment variables:"
            echo "  GOOGLE_CLOUD_PROJECT  Google Cloud Project ID"
            echo "  CLAUDE_API_KEY        Anthropic Claude API key"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Run main deployment
main 