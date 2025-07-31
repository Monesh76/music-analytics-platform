# 🎵 Music Analytics Platform - Real-time User Behavior Tracking & AI Insights

A comprehensive, production-ready music analytics platform that processes real-time music streaming events, enriches them with AI-powered insights, and provides actionable business intelligence. Built with Google Cloud Platform, Python, Pydantic, and Claude LLM.

## 🚀 Project Overview

This platform simulates a real-world music streaming analytics system where users listen to music on platforms like Spotify, Apple Music, and YouTube Music. The system captures these events, enriches them with AI-powered insights, and provides detailed analytics for business intelligence.

### 🎯 Key Features

- **Real-time Event Processing**: Captures music streaming events from multiple platforms
- **AI-Powered Enrichment**: Uses Claude LLM to generate intelligent insights
- **Multi-Platform Support**: Spotify, Apple Music, YouTube Music integration
- **Advanced Analytics**: Mood analysis, genre prediction, similar track recommendations
- **Interactive Frontend**: Modern web interface for testing and visualization
- **Production-Ready**: Scalable architecture with proper error handling and monitoring

## 🏗️ Architecture

```
User Listens to Music → Mobile App Tracks Events → Analytics Pipeline Processes → Business Intelligence
```

### 🔧 Technology Stack

- **Backend**: Python 3.13, Pydantic v1.10.13
- **Cloud Platform**: Google Cloud Platform (Pub/Sub, Cloud Functions, BigQuery)
- **AI/ML**: Claude LLM (Anthropic) for intelligent enrichment
- **Frontend**: HTML5, Tailwind CSS, JavaScript (Vanilla)
- **Infrastructure**: Terraform for IaC
- **Monitoring**: Google Cloud Logging, Structured Logging

## 📊 Analytics Capabilities

### AI-Powered Insights
- **User Behavior Analysis**: Intelligent event descriptions
- **Mood & Emotion Analysis**: Track-specific mood analysis
- **Genre Prediction**: Multi-genre classification with confidence
- **Listening Context**: Contextual listening environment inference
- **Recommendation Engine**: Artist-specific similar track suggestions
- **Analytics Confidence**: Realistic confidence scoring (50%-95%)

### Platform Analytics
- **Cross-Platform Tracking**: Spotify, Apple Music, YouTube Music
- **Real-time Processing**: Sub-second event processing
- **Scalable Architecture**: Handles 10,000+ events/day
- **Data Validation**: Pydantic-based schema validation
- **Error Handling**: Dead-letter queues and retry policies

## 🎵 Sample Tracks & Artists

The platform includes 15 classic tracks across different platforms:

### Spotify Tracks
- Hotel California - Eagles
- Sweet Child O Mine - Guns N Roses
- Imagine - John Lennon
- Respect - Aretha Franklin
- What's Going On - Marvin Gaye

### Apple Music Tracks
- Bohemian Rhapsody - Queen
- Billie Jean - Michael Jackson
- Smells Like Teen Spirit - Nirvana
- Purple Haze - Jimi Hendrix
- Johnny B. Goode - Chuck Berry

### YouTube Music Tracks
- Stairway to Heaven - Led Zeppelin
- Like a Rolling Stone - Bob Dylan
- Superstition - Stevie Wonder
- Good Vibrations - The Beach Boys
- I Want to Hold Your Hand - The Beatles

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- Google Cloud SDK
- Terraform
- Git

### 1. Clone and Setup
```bash
git clone <your-repo-url>
cd MyStage-CluadeLLM
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Local Development (Recommended)
```bash
# Start local server (no GCP resources needed)
cd frontend
python3 server_local.py 8001
```

### 3. Access the Platform
Open your browser and navigate to: `http://localhost:8001`

## 🧪 Testing the Platform

### Frontend Testing
1. **Platform Selection**: Click different platform buttons (Spotify, Apple Music, YouTube Music)
2. **Track Loading**: Use "Quick Track Selection" buttons
3. **Next Track**: Test platform-specific track cycling
4. **Form Submission**: Submit events and view AI-powered analytics

### Backend Testing
```bash
# Test API endpoints
curl -X POST http://localhost:8001/api/enrich \
  -H "Content-Type: application/json" \
  -d '{"event_id":"test","event_type":"play",...}'
```

### Test Scenarios
- **Random Track**: Loads any track from any platform
- **Platform-Specific**: Loads tracks from selected platform only
- **Genre-Based**: Loads tracks by genre (Rock, Pop, Soul)
- **Next Track**: Cycles through tracks respecting platform selection

## 🏢 Production Deployment

### GCP Setup
```bash
# Set up GCP project
gcloud config set project mystage-claudellm
gcloud auth application-default login

# Deploy infrastructure
cd infrastructure/terraform
terraform init
terraform apply
```

### Deploy Functions
```bash
# Package and deploy Cloud Functions
./scripts/package_functions.sh
./scripts/deploy.sh
```

### Environment Variables
```bash
# Required environment variables
GOOGLE_CLOUD_PROJECT=mystage-claudellm
CLAUDE_API_KEY=your_anthropic_api_key
GCP_REGION=us-central1
BIGQUERY_DATASET=music_analytics_dev
```

## 📈 Performance Metrics

### Target KPIs
- **Event Processing**: 10,000+ events/day
- **Error Reduction**: 30% reduction in downstream errors (Pydantic validation)
- **User Engagement**: 25% boost through real-time Claude LLM enrichment
- **Processing Time**: Sub-second event processing
- **Availability**: 99.9% uptime

### Monitoring
- **Cloud Logging**: Structured logs for all components
- **Error Tracking**: Dead-letter queues for failed events
- **Performance**: Real-time metrics and alerts
- **Data Quality**: Pydantic validation with detailed error reporting

## 🎯 Use Cases

### Enterprise Applications
- **Music Platforms**: Spotify, Apple Music internal analytics
- **Analytics Companies**: Nielsen Music, Chartmetric, MRC Data
- **Marketing Agencies**: Ad targeting, campaign optimization
- **Record Labels**: Artist performance tracking, A&R decisions

### Business Intelligence
- **User Behavior Analysis**: Understanding listening patterns
- **Content Recommendations**: AI-powered track suggestions
- **Platform Optimization**: Cross-platform performance insights
- **Revenue Optimization**: Targeted advertising and content strategies

## 🔧 Development

### Project Structure
```
MyStage-CluadeLLM/
├── frontend/                 # Web interface
│   ├── index.html           # Main UI
│   ├── script.js            # Frontend logic
│   ├── track_loader.js      # Track selection
│   ├── test_tracks.json     # Sample data
│   └── server_local.py      # Local development server
├── src/                     # Backend code
│   ├── functions/           # Cloud Functions
│   ├── models/              # Pydantic models
│   ├── utils/               # Utilities
│   └── pipeline/            # Data processing
├── infrastructure/          # Terraform IaC
├── scripts/                 # Deployment scripts
├── tests/                   # Test files
└── requirements.txt         # Python dependencies
```

### Key Components
- **Ingestion Function**: Receives and validates music events
- **Enrichment Function**: AI-powered event enrichment
- **Analytics Function**: Real-time analytics processing
- **Frontend**: Interactive web interface for testing
- **Terraform**: Infrastructure as Code

## 🧠 AI Enrichment Features

### Intelligent Analysis
- **Track-Specific Moods**: Accurate mood analysis for each track
- **Artist-Based Genres**: Multi-genre classification
- **Contextual Listening**: Environment and situation inference
- **Similar Tracks**: Artist-specific recommendations
- **Confidence Scoring**: Realistic confidence levels

### Example Enrichments
```
Track: Hotel California - Eagles
Mood: Melancholic, atmospheric, and introspective
Genres: classic_rock, soft_rock, country_rock
Similar: Take It Easy, Desperado, One of These Nights
Context: Evening relaxation or road trip vibes
Confidence: 95%
```

## 🚀 Getting Started with GitHub

### 1. Initialize Git Repository
```bash
git init
git add .
git commit -m "Initial commit: Music Analytics Platform"
```

### 2. Create GitHub Repository
1. Go to GitHub.com
2. Click "New repository"
3. Name: `music-analytics-platform`
4. Description: "Real-time music analytics platform with AI-powered insights"
5. Make it public or private
6. Don't initialize with README (we already have one)

### 3. Push to GitHub
```bash
git remote add origin https://github.com/yourusername/music-analytics-platform.git
git branch -M main
git push -u origin main
```

### 4. Add GitHub Actions (Optional)
Create `.github/workflows/test.yml` for CI/CD:
```yaml
name: Test Music Analytics Platform
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.13
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          python -m pytest tests/
```

## 📚 Documentation

### API Reference
- **POST /api/enrich**: Enrich music events with AI insights
- **GET /**: Main frontend interface
- **GET /test_tracks.json**: Sample track data

### Data Models
- **MusicEvent**: Core event structure
- **EnrichedMusicEvent**: AI-enriched event data
- **Track/Artist/UserInteraction**: Nested data models

### Configuration
- **Environment Variables**: GCP project, API keys, regions
- **Terraform Variables**: Infrastructure configuration
- **Frontend Settings**: Server ports, API endpoints

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Anthropic**: Claude LLM for intelligent enrichment
- **Google Cloud Platform**: Scalable infrastructure
- **Pydantic**: Data validation and serialization
- **Tailwind CSS**: Modern UI components

## 📞 Support

For questions, issues, or contributions:
- **Issues**: https://github.com/Monesh76/music-analytics-platform/issues
- **Discussions**: GitHub Discussions
- **Email**: [monesh6302@gmail.com]

---

**🎵 Built with ❤️ for the music analytics community** 
