# 🌸 Signal Bloom

A living garden of shared sparks.

## Overview

Signal Bloom is a minimal, real-time collaborative app that visualizes collective ideas as blooming signals. Each user can submit a short phrase (a "signal"), which blossoms into a dynamic visual node on the screen. Over time, the garden evolves into a map of shared creativity — ephemeral, organic, and community-driven.

## Features

- **Real-time collaboration**: Signals appear instantly for all connected users
- **Visual blooming**: Each signal appears with beautiful animated ripple effects
- **Ephemeral creativity**: Signals exist only in memory, creating temporary moments of shared inspiration
- **Responsive design**: Works on desktop and mobile devices
- **Minimal & elegant**: Clean, distraction-free interface focused on the creative experience

## Technical Stack

### Backend
- **Python** with **Starlette** (ASGI framework)
- **WebSocket** server for real-time signal broadcasting
- **In-memory storage** for ephemeral signals
- **uvicorn** ASGI server

### Frontend
- **Svelte** + **Vite** for reactive, minimal UI
- **WebSocket client** for real-time communication
- **CSS animations** for blooming visual effects
- **Responsive design** with glassmorphism aesthetics

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js 18+
- npm or yarn

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd 6degrees-signalbloom
   ```

2. **Set up the backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Set up the frontend**
   ```bash
   cd frontend
   npm install
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
2. **Share a spark**: Type your creative signal in the input field
3. **Watch it bloom**: Your signal appears as a visual bloom on the screen
4. **Collaborate**: See other users' signals appear in real-time
5. **Enjoy the garden**: Watch the living garden of creativity evolve

## Architecture

```
Frontend (Svelte)     ←→     Backend (Starlette)
     ↓                           ↓
WebSocket Client      ←→     WebSocket Server
     ↓                           ↓
Visual Blooms         ←→     Signal Broadcasting
```

### Data Flow
1. User enters a phrase in the frontend
2. Frontend sends signal via WebSocket
3. Backend broadcasts signal to all connected clients
4. All clients receive and display the signal as a visual bloom
5. Signals are stored in memory and shared with new connections

## Project Structure

```
6degrees-signalbloom/
├── backend/
│   ├── main.py              # Main server application
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── lib/
│   │   │   ├── SignalBloom.svelte   # Main app component
│   │   │   ├── Signal.svelte        # Individual signal bloom
│   │   │   └── SignalInput.svelte   # Input component
│   │   └── routes/
│   │       └── +page.svelte         # Main page
│   ├── package.json         # Frontend dependencies
│   └── vite.config.js       # Vite configuration
└── README.md               # This file
```

## Development

### Backend API

- `GET /` - Development test page
- `GET /status` - Health check endpoint  
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

## Future Enhancements

- [ ] Multi-room "gardens" using namespaces
- [ ] Signal persistence with SQLite/Postgres
- [ ] Export garden snapshots as images or JSON
- [ ] Integration with external datasets (Wikidata concepts)
- [ ] Signal decay and lifecycle management
- [ ] User identification and signal attribution
- [ ] Mobile app with native WebSocket support

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