# 🌸 Signal Bloom

A living garden of shared sparks - **Now with Voice Integration & Enterprise Features!**

## ✨ What's New in v2.0

![Signal Bloom Interface](https://github.com/user-attachments/assets/33985a4e-46c1-480e-a4d5-f2d39bda3c3d)

### 🎤 Voice Integration
- **Voice Input**: Speak your signals using Web Speech API
- **Voice Output**: Hear signals through ElevenLabs TTS
- **Real-time Processing**: Seamless voice-to-text-to-speech pipeline

![Signal in Action](https://github.com/user-attachments/assets/5322131b-2aee-4b0b-beac-cce2f12fd2cc)

### 🚀 Major Improvements
- **Database Persistence**: SQLite storage with automatic cleanup
- **Environment Configuration**: Flexible .env-based settings
- **Enhanced Error Handling**: Comprehensive logging and failsafes
- **WebSocket Reliability**: Auto-reconnection with exponential backoff
- **Professional UI**: Glassmorphism design with voice controls
- **Docker Support**: Full containerization for easy deployment

## Overview

Signal Bloom is a minimal, real-time collaborative app that visualizes collective ideas as blooming signals. Each user can submit a short phrase (a "signal"), which blossoms into a dynamic visual node on the screen. Over time, the garden evolves into a map of shared creativity — ephemeral, organic, and community-driven.

## Features

### Core Features
- **Real-time collaboration**: Signals appear instantly for all connected users
- **Visual blooming**: Each signal appears with beautiful animated ripple effects
- **Database persistence**: Signals are stored and restored on reconnection
- **Responsive design**: Works on desktop and mobile devices
- **Minimal & elegant**: Clean, distraction-free interface focused on the creative experience

### Voice Features 🎤
- **Voice Input**: Click the microphone to speak your signal
- **Voice Output**: Automatic text-to-speech for new signals (when enabled)
- **Smart Processing**: Enhanced text formatting for natural speech
- **Fallback Support**: Graceful degradation when voice features unavailable

### Enterprise Features 🏢
- **Environment Configuration**: Flexible settings via .env files
- **Database Persistence**: SQLite with automatic signal cleanup
- **Health Monitoring**: Comprehensive status endpoints
- **Docker Support**: Full containerization with docker-compose
- **Nginx Integration**: Production-ready reverse proxy configuration
- **Rate Limiting**: Built-in protection against abuse

## Technical Stack

### Backend
- **Python** with **Starlette** (ASGI framework)
- **WebSocket** server for real-time signal broadcasting
- **SQLite/SQLAlchemy** for persistent signal storage
- **ElevenLabs API** for text-to-speech synthesis
- **uvicorn** ASGI server with structured logging

### Frontend
- **Svelte** + **Vite** for reactive, minimal UI
- **WebSocket client** with auto-reconnection
- **Web Speech API** for voice input
- **CSS animations** for blooming visual effects
- **Responsive design** with glassmorphism aesthetics

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js 18+
- npm or yarn
- (Optional) ElevenLabs API key for voice features

### Quick Start with Docker

1. **Clone and configure**
   ```bash
   git clone <repository-url>
   cd 6degrees-signalbloom
   cp backend/.env.example backend/.env
   ```

2. **Add ElevenLabs API key (optional)**
   ```bash
   # Edit backend/.env
   ELEVENLABS_API_KEY=your_api_key_here
   ELEVENLABS_VOICE_ID=your_voice_id_here
   ```

3. **Start with Docker**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Status: http://localhost:8000/status

### Manual Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd 6degrees-signalbloom
   ```

2. **Set up the backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   cp .env.example .env
   ```

3. **Set up the frontend**
   ```bash
   cd frontend
   npm install
   ```

4. **Configure voice features (optional)**
   ```bash
   # Edit backend/.env
   ELEVENLABS_API_KEY=your_api_key_here
   ELEVENLABS_VOICE_ID=your_voice_id_here
   ```

### Running the Application

1. **Start the backend server** (Terminal 1)
   ```bash
   cd backend
   python main.py
   ```
   Server will start on `http://localhost:8000`

2. **Start the frontend development server** (Terminal 2)
   ```bash
   cd frontend
   npm run dev
   ```
   Frontend will be available on `http://localhost:5173`

3. **Open your browser** and navigate to `http://localhost:5173`

## Usage

1. **Connect**: The app automatically connects to the WebSocket server
2. **Share a spark**: Type your creative signal in the input field or use voice input 🎤
3. **Watch it bloom**: Your signal appears as a visual bloom on the screen
4. **Listen**: Enable voice output to hear signals as speech 🔊
5. **Collaborate**: See and hear other users' signals appear in real-time
6. **Enjoy the garden**: Watch the living garden of creativity evolve

## Architecture

```
Frontend (Svelte)     ←→     Backend (Starlette)
     ↓                           ↓
WebSocket Client      ←→     WebSocket Server
     ↓                           ↓
Voice Controls        ←→     ElevenLabs API
     ↓                           ↓
Visual Blooms         ←→     SQLite Database
```

### Data Flow
1. User enters a phrase via text input or voice input
2. Frontend sends signal via WebSocket
3. Backend validates, stores in database, and broadcasts to all clients
4. All clients receive and display the signal as a visual bloom
5. Optional: Voice output speaks the signal text

## Configuration

### Environment Variables

```bash
# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=true
LOG_LEVEL=info

# Database Configuration
DATABASE_URL=sqlite:///signals.db

# CORS Configuration
CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]

# Signal Configuration
MAX_SIGNALS=1000
MAX_SIGNAL_LENGTH=1000

# ElevenLabs Voice Configuration
ELEVENLABS_API_KEY=your_api_key_here
ELEVENLABS_VOICE_ID=your_voice_id_here
ELEVENLABS_BASE_URL=https://api.elevenlabs.io

# Security
SECRET_KEY=your-secret-key-change-this-in-production
```

## API Documentation

### REST Endpoints

- `GET /` - Development test page
- `GET /status` - Health check with feature status
- `GET /voice/status` - Voice service availability
- `GET|POST /voice/tts?text=hello` - Text-to-speech conversion

### WebSocket Endpoint

- `WebSocket /ws` - Real-time signal communication

### Signal Format
```json
{
  "type": "signal",
  "id": "signal_0_1234567890.123",
  "text": "Your creative spark",
  "timestamp": "2024-01-01T12:00:00.000Z", 
  "x": 45.2,
  "y": 67.8
}
```

## Production Deployment

### Docker Deployment

1. **Production with Nginx**
   ```bash
   docker-compose --profile production up -d
   ```

2. **SSL Setup**
   ```bash
   # Add SSL certificates to ./ssl/
   # Configure domains in nginx.conf
   ```

### Manual Deployment

1. **Backend Production**
   ```bash
   pip install gunicorn
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

2. **Frontend Production**
   ```bash
   npm run build
   npm install -g serve
   serve -s build -l 3000
   ```

## Monitoring & Maintenance

### Health Checks
- Backend: `GET /status`
- Voice: `GET /voice/status`
- Database: Automatic migration and cleanup

### Logging
- Structured logging with timestamps
- Configurable log levels
- Error tracking and monitoring

### Database Maintenance
- Automatic signal cleanup (configurable limits)
- Database backup recommended for production
- Migration support for schema changes

## Voice Integration Guide

### Setting Up ElevenLabs

1. **Get API Key**
   - Sign up at [ElevenLabs](https://elevenlabs.io)
   - Generate API key from dashboard

2. **Choose Voice**
   - Browse available voices
   - Copy voice ID for configuration

3. **Configure**
   ```bash
   ELEVENLABS_API_KEY=your_key_here
   ELEVENLABS_VOICE_ID=voice_id_here
   ```

### Voice Features
- **Input**: Web Speech API (Chrome/Edge recommended)
- **Output**: ElevenLabs TTS with streaming
- **Fallback**: Text-only mode when voice unavailable

## Development

### Project Structure

```
6degrees-signalbloom/
├── backend/
│   ├── main.py              # Main server application
│   ├── config.py            # Configuration management
│   ├── database.py          # Database models and operations
│   ├── voice.py             # ElevenLabs voice integration
│   ├── requirements.txt     # Python dependencies
│   ├── .env.example         # Environment template
│   └── Dockerfile           # Backend container
├── frontend/
│   ├── src/
│   │   ├── lib/
│   │   │   ├── SignalBloom.svelte   # Main app component
│   │   │   ├── Signal.svelte        # Individual signal bloom
│   │   │   ├── SignalInput.svelte   # Input component
│   │   │   └── VoiceControls.svelte # Voice input/output
│   │   └── routes/
│   │       └── +page.svelte         # Main page
│   ├── package.json         # Frontend dependencies
│   ├── vite.config.js       # Vite configuration
│   └── Dockerfile           # Frontend container
├── docker-compose.yml       # Container orchestration
├── nginx.conf              # Production proxy config
└── README.md               # This file
```

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Testing

```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
npm test

# Integration tests
npm run test:integration
```

## Future Enhancements

- [ ] Multi-room "gardens" using namespaces
- [ ] Export garden snapshots as images or JSON
- [ ] Integration with external datasets (Wikidata concepts)
- [ ] Advanced signal decay and lifecycle management
- [ ] User identification and signal attribution
- [ ] Mobile app with native WebSocket support
- [ ] Real-time voice conversations
- [ ] AI-powered signal suggestions
- [ ] Advanced analytics and insights

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test the implementation
5. Submit a pull request

## License

MIT License - Feel free to use this project for your creative endeavors!

---

*Built with ❤️ for creative communities, online collectives, and collaborative inspiration.*

**Now featuring voice integration powered by ElevenLabs! 🎤🔊**