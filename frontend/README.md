# 🎵 Music Event Enrichment Frontend

A beautiful, modern web interface for testing the Music Event Enrichment Pipeline with Claude LLM.

## 🚀 Features

- **Modern UI**: Beautiful, responsive design with Tailwind CSS
- **Real-time Processing**: Direct integration with Cloud Functions
- **Claude LLM Integration**: AI-powered enrichments
- **BigQuery Storage**: Real data persistence
- **Form Validation**: Real-time input validation
- **Loading States**: Smooth user experience
- **Error Handling**: Graceful error management

## 🎯 What You Can Do

1. **Create Music Events**: Fill out a comprehensive form with track details
2. **Generate Enrichments**: Get AI-powered insights from Claude LLM
3. **View Results**: See detailed enrichments in a beautiful interface
4. **Store Data**: Automatically save to BigQuery
5. **Test Different Scenarios**: Try various artists, tracks, and platforms

## 🛠️ Setup & Installation

### Prerequisites

- Python 3.7+
- Google Cloud SDK configured
- Access to the deployed Cloud Functions

### Quick Start

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install Python dependencies**:
   ```bash
   pip install requests
   ```

3. **Start the server**:
   ```bash
   python server.py
   ```

4. **Open your browser** and go to:
   ```
   http://localhost:8000
   ```

## 🎨 UI Components

### Status Cards
- **Enrichment Function**: Shows if the Cloud Function is active
- **Claude LLM**: Displays AI integration status
- **BigQuery**: Shows data storage readiness

### Input Form
- **Event Information**: Event ID, type, and metadata
- **Track Details**: Title, artist, album, genre, duration, year
- **User Interaction**: User ID and location
- **Streaming Platform**: Platform, quality, and bitrate

### Results Display
- **Claude LLM Enrichments**: AI-generated insights
- **BigQuery Storage**: Data persistence confirmation
- **Try Another**: Quick form reset

## 🔧 Configuration

### Cloud Function URL
The server is configured to call the enrichment function at:
```
https://music-event-enrichment-dev-y42dokfiga-uc.a.run.app/enrich_music_event
```

### Authentication
The server automatically handles Google Cloud authentication using:
```bash
gcloud auth print-identity-token
```

## 📊 Sample Data

The form comes pre-filled with sample data for easy testing:

- **Event ID**: `evt_ui_demo_001`
- **Track**: Hotel California by Eagles
- **Album**: Hotel California (1976)
- **Genre**: Rock
- **Platform**: Spotify
- **Quality**: High (320 kbps)

## 🎯 Testing Scenarios

### 1. Classic Rock (Eagles)
- **Track**: Hotel California
- **Expected Mood**: Melancholic, atmospheric
- **Genres**: Classic rock, soft rock, country rock
- **Context**: Evening relaxation or road trip vibes

### 2. Progressive Rock (Queen)
- **Track**: Bohemian Rhapsody
- **Expected Mood**: Dramatic, theatrical
- **Genres**: Progressive rock, hard rock, art rock
- **Context**: Party atmosphere or dramatic listening

### 3. Custom Tracks
- Try your own favorite songs
- Test different artists and genres
- Experiment with various platforms

## 🔍 Troubleshooting

### Common Issues

1. **Authentication Error**:
   ```bash
   gcloud auth login
   gcloud config set project mystage-claudellm
   ```

2. **Port Already in Use**:
   ```bash
   python server.py 8001  # Use different port
   ```

3. **Cloud Function Unavailable**:
   - Check if the function is deployed
   - Verify the URL is correct
   - Check authentication token

### Debug Mode

Enable debug logging by setting the environment variable:
```bash
export DEBUG=1
python server.py
```

## 🎨 Customization

### Styling
The UI uses Tailwind CSS. Modify `index.html` to change:
- Colors and gradients
- Layout and spacing
- Animations and transitions

### JavaScript
Edit `script.js` to customize:
- Form validation rules
- API call logic
- Result display format

### Server
Modify `server.py` to:
- Change Cloud Function URL
- Add custom error handling
- Implement caching

## 📱 Mobile Support

The interface is fully responsive and works on:
- Desktop browsers
- Tablets
- Mobile phones

## 🔒 Security

- CORS headers configured for local development
- Authentication tokens handled securely
- Input validation and sanitization
- Error messages don't expose sensitive data

## 🚀 Production Deployment

For production deployment:

1. **Use a proper web server** (nginx, Apache)
2. **Enable HTTPS** with SSL certificates
3. **Configure CORS** for your domain
4. **Set up monitoring** and logging
5. **Implement rate limiting**

## 📈 Performance

- **Fast Loading**: Optimized CSS and JavaScript
- **Smooth Animations**: Hardware-accelerated transitions
- **Efficient API Calls**: Minimal network overhead
- **Responsive Design**: Works on all screen sizes

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is part of the Music Event Enrichment Pipeline.

---

**🎵 Enjoy testing your Claude LLM-powered music enrichment pipeline!** 