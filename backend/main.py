"""
Signal Bloom Backend
A real-time WebSocket server for broadcasting creative signals.
"""

import json
import asyncio
import logging
from typing import Dict, Set, Optional
from datetime import datetime
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route, WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect
from starlette.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SignalBloomManager:
    """Manages connections and signal broadcasting."""
    
    def __init__(self):
        self.connections: Set[WebSocket] = set()
        self.signals: Dict[str, dict] = {}
        self.max_signals = 1000  # Limit signal storage
        logger.info("SignalBloomManager initialized")
    
    async def connect(self, websocket: WebSocket):
        """Add a new WebSocket connection."""
        try:
            await websocket.accept()
            self.connections.add(websocket)
            logger.info(f"New WebSocket connection. Total connections: {len(self.connections)}")
            
            # Send existing signals to new connection
            for signal_id, signal_data in self.signals.items():
                try:
                    message = json.dumps({
                        "type": "signal",
                        "id": signal_id,
                        **signal_data
                    })
                    await websocket.send_text(message)
                except Exception as e:
                    logger.error(f"Error sending existing signal to new connection: {e}")
                    break
        except Exception as e:
            logger.error(f"Error accepting WebSocket connection: {e}")
            raise
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        self.connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.connections)}")
    
    def _validate_signal_data(self, signal_data: dict) -> bool:
        """Validate signal data format."""
        if not isinstance(signal_data, dict):
            return False
        
        text = signal_data.get("text", "")
        if not isinstance(text, str) or len(text.strip()) == 0 or len(text) > 1000:
            return False
        
        x = signal_data.get("x", 50)
        y = signal_data.get("y", 50)
        if not (isinstance(x, (int, float)) and 0 <= x <= 100):
            return False
        if not (isinstance(y, (int, float)) and 0 <= y <= 100):
            return False
        
        return True
    
    async def broadcast_signal(self, signal_data: dict):
        """Broadcast a new signal to all connected clients."""
        try:
            # Validate input
            if not self._validate_signal_data(signal_data):
                logger.warning(f"Invalid signal data received: {signal_data}")
                return
            
            # Generate unique signal ID
            signal_id = f"signal_{len(self.signals)}_{datetime.now().timestamp()}"
            
            # Store signal in memory with cleanup if needed
            if len(self.signals) >= self.max_signals:
                # Remove oldest signals (simple FIFO)
                oldest_keys = list(self.signals.keys())[:100]
                for key in oldest_keys:
                    del self.signals[key]
                logger.info(f"Cleaned up {len(oldest_keys)} old signals")
            
            self.signals[signal_id] = {
                "text": signal_data["text"].strip(),
                "timestamp": datetime.now().isoformat(),
                "x": max(0, min(100, signal_data.get("x", 50))),
                "y": max(0, min(100, signal_data.get("y", 50)))
            }
            
            # Broadcast to all connections
            message = json.dumps({
                "type": "signal",
                "id": signal_id,
                **self.signals[signal_id]
            })
            
            # Remove disconnected clients and send to active ones
            disconnected = set()
            for connection in self.connections:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.warning(f"Failed to send message to connection: {e}")
                    disconnected.add(connection)
            
            # Clean up disconnected clients
            self.connections -= disconnected
            if disconnected:
                logger.info(f"Removed {len(disconnected)} disconnected clients")
            
            logger.info(f"Broadcast signal {signal_id} to {len(self.connections)} connections")
            
        except Exception as e:
            logger.error(f"Error broadcasting signal: {e}")
            raise


# Global manager instance
bloom_manager = SignalBloomManager()


async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections for real-time signals."""
    await bloom_manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "signal":
                    # Broadcast new signal to all clients
                    await bloom_manager.broadcast_signal(message)
                else:
                    logger.warning(f"Unknown message type: {message.get('type')}")
                    
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected normally")
    except Exception as e:
        logger.error(f"Unexpected WebSocket error: {e}")
    finally:
        bloom_manager.disconnect(websocket)


async def status_endpoint(request):
    """Health check and status endpoint."""
    try:
        return JSONResponse({
            "status": "healthy",
            "service": "Signal Bloom Backend",
            "version": "1.0.0",
            "connections": len(bloom_manager.connections),
            "signals": len(bloom_manager.signals),
            "timestamp": datetime.now().isoformat(),
            "uptime": "N/A"  # TODO: Add uptime tracking
        })
    except Exception as e:
        logger.error(f"Error in status endpoint: {e}")
        return JSONResponse({
            "status": "error",
            "message": "Health check failed"
        }, status_code=500)


async def frontend_endpoint(request):
    """Serve a simple test page for development."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Signal Bloom - Development</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 600px; margin: 0 auto; }
            input, button { padding: 10px; margin: 5px; }
            #signals { margin-top: 20px; }
            .signal { background: #f0f0f0; padding: 10px; margin: 5px 0; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌸 Signal Bloom</h1>
            <div>
                <input type="text" id="signalInput" placeholder="Enter your signal..." />
                <button onclick="sendSignal()">Bloom Signal</button>
            </div>
            <div id="status">Connecting...</div>
            <div id="signals"></div>
        </div>
        
        <script>
            const ws = new WebSocket('ws://localhost:8000/ws');
            const statusDiv = document.getElementById('status');
            const signalsDiv = document.getElementById('signals');
            const signalInput = document.getElementById('signalInput');
            
            ws.onopen = function() {
                statusDiv.textContent = 'Connected to Signal Bloom';
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.type === 'signal') {
                    const signalEl = document.createElement('div');
                    signalEl.className = 'signal';
                    signalEl.innerHTML = `<strong>${data.text}</strong> <small>(${new Date(data.timestamp).toLocaleTimeString()})</small>`;
                    signalsDiv.insertBefore(signalEl, signalsDiv.firstChild);
                }
            };
            
            ws.onclose = function() {
                statusDiv.textContent = 'Disconnected';
            };
            
            function sendSignal() {
                const text = signalInput.value.trim();
                if (text) {
                    ws.send(JSON.stringify({
                        type: 'signal',
                        text: text,
                        x: Math.random() * 100,
                        y: Math.random() * 100
                    }));
                    signalInput.value = '';
                }
            }
            
            signalInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendSignal();
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html)


# Application routes
routes = [
    Route("/", frontend_endpoint),
    Route("/status", status_endpoint),
    WebSocketRoute("/ws", websocket_endpoint),
]

# Add CORS middleware for development
app = Starlette(debug=True, routes=routes)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    logger.info("Starting Signal Bloom Backend Server")
    try:
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8000, 
            log_level="info",
            access_log=True
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise