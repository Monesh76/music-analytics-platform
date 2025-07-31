#!/bin/bash

# Development Deployment Script for Real-Time Music Data Pipeline
# This script deploys the core infrastructure without Apache Beam for Python 3.13 compatibility

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

# Install Python dependencies (development version)
install_python_deps() {
    print_info "Installing Python dependencies (development mode)..."
    
    # Create virtual environment if it doesn't exist
    if [[ ! -d "venv" ]]; then
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip and setuptools first
    $PIP_CMD install --upgrade pip setuptools wheel
    
    # Install minimal development dependencies (Python 3.13 compatible)
    $PIP_CMD install -r requirements-dev-minimal.txt
    
    print_success "Python dependencies installed (development mode)"
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

# Test the simplified pipeline
test_simplified_pipeline() {
    print_info "Testing simplified pipeline..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Test the simplified pipeline
    python3 src/pipeline/music_pipeline_simple.py
    
    print_success "Simplified pipeline test completed"
}

# Generate sample data
generate_sample_data() {
    print_info "Generating sample data..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Generate sample events
    python3 scripts/generate_sample_data.py --count 100 --output sample_events.json
    
    print_success "Sample data generated"
}

# Show deployment information
show_info() {
    print_info "Development deployment completed successfully!"
    echo ""
    echo "=== Development Deployment Information ==="
    echo "Project ID: $GOOGLE_CLOUD_PROJECT"
    echo "Environment: ${ENVIRONMENT:-dev}"
    echo "Mode: Development (no Apache Beam)"
    echo ""
    echo "=== What's Available ==="
    echo "✅ Infrastructure deployed (Pub/Sub, BigQuery, Cloud Functions)"
    echo "✅ Python dependencies installed"
    echo "✅ Simplified pipeline working"
    echo "✅ Sample data generation working"
    echo ""
    echo "=== Next Steps ==="
    echo "1. Test the simplified pipeline:"
    echo "   python3 src/pipeline/music_pipeline_simple.py"
    echo ""
    echo "2. Generate sample data:"
    echo "   python3 scripts/generate_sample_data.py --count 1000"
    echo ""
    echo "3. Run unit tests:"
    echo "   python3 -m pytest tests/"
    echo ""
    echo "4. For production deployment (with Apache Beam), use:"
    echo "   ./scripts/deploy.sh"
    echo ""
    echo "=== Useful Commands ==="
    echo "Check BigQuery data:"
    echo "  bq query 'SELECT COUNT(*) FROM \`$GOOGLE_CLOUD_PROJECT.music_analytics_${ENVIRONMENT:-dev}.raw_music_events\`'"
    echo ""
    echo "View Cloud Function logs:"
    echo "  gcloud functions logs read music-event-ingestion-${ENVIRONMENT:-dev} --region=${DATAFLOW_REGION:-us-central1}"
}

# Cleanup function
cleanup() {
    print_info "Cleaning up temporary files..."
    rm -rf temp/
}

# Main deployment function
main() {
    print_info "Starting Real-Time Music Data Pipeline development deployment..."
    
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
    test_simplified_pipeline
    generate_sample_data
    show_info
    
    print_success "Development deployment completed successfully!"
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
        --help|-h)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --environment, -e   Environment name (default: dev)"
            echo "  --region, -r        Dataflow region (default: us-central1)"
            echo "  --help, -h          Show this help message"
            echo ""
            echo "Required environment variables:"
            echo "  GOOGLE_CLOUD_PROJECT  Google Cloud Project ID"
            echo "  CLAUDE_API_KEY        Anthropic Claude API key"
            echo ""
            echo "This script deploys the infrastructure and tests the core functionality"
            echo "without Apache Beam (suitable for Python 3.13 development)"
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