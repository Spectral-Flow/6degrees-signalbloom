"""
Signal Bloom Backend
A real-time WebSocket server for broadcasting creative signals.
"""

import json
import asyncio
from typing import Dict, Set
from datetime import datetime
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route, WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect
import uvicorn


class SignalBloomManager:
    """Manages connections and signal broadcasting."""
    
    def __init__(self):
        self.connections: Set[WebSocket] = set()
        self.signals: Dict[str, dict] = {}
    
    async def connect(self, websocket: WebSocket):
        """Add a new WebSocket connection."""
        await websocket.accept()
        self.connections.add(websocket)
        
        # Send existing signals to new connection
        for signal_id, signal_data in self.signals.items():
            await websocket.send_text(json.dumps({
                "type": "signal",
                "id": signal_id,
                **signal_data
            }))
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        self.connections.discard(websocket)
    
    async def broadcast_signal(self, signal_data: dict):
        """Broadcast a new signal to all connected clients."""
        signal_id = f"signal_{len(self.signals)}_{datetime.now().timestamp()}"
        
        # Store signal in memory
        self.signals[signal_id] = {
            "text": signal_data.get("text", ""),
            "timestamp": datetime.now().isoformat(),
            "x": signal_data.get("x", 50),
            "y": signal_data.get("y", 50)
        }
        
        # Broadcast to all connections
        message = json.dumps({
            "type": "signal",
            "id": signal_id,
            **self.signals[signal_id]
        })
        
        # Remove disconnected clients
        disconnected = set()
        for connection in self.connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.add(connection)
        
        # Clean up disconnected clients
        self.connections -= disconnected


# Global manager instance
bloom_manager = SignalBloomManager()


async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections for real-time signals."""
    await bloom_manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "signal":
                # Broadcast new signal to all clients
                await bloom_manager.broadcast_signal(message)
                
    except WebSocketDisconnect:
        bloom_manager.disconnect(websocket)


async def status_endpoint(request):
    """Health check and status endpoint."""
    return JSONResponse({
        "status": "healthy",
        "connections": len(bloom_manager.connections),
        "signals": len(bloom_manager.signals),
        "timestamp": datetime.now().isoformat()
    })


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

app = Starlette(debug=True, routes=routes)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")