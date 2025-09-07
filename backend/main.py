"""
Signal Bloom Backend
A real-time WebSocket server for broadcasting creative signals.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Optional, Set

import uvicorn
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route, WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect

from config import Config
from database import InnovationObject, Signal, db_manager
from voice import voice_processor

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class SignalBloomManager:
    """Manages connections and signal broadcasting with database persistence."""

    def __init__(self):
        self.connections: Set[WebSocket] = set()
        self.signals: Dict[str, dict] = {}  # In-memory cache
        self.max_signals = Config.MAX_SIGNALS
        logger.info("SignalBloomManager initialized")

    async def initialize(self):
        """Initialize database and load recent signals"""
        try:
            await db_manager.initialize()

            # Seed innovation data
            await db_manager.seed_innovation_data()

            # Load recent signals from database
            db_signals = await db_manager.get_recent_signals(limit=100)
            for db_signal in db_signals:
                self.signals[db_signal.id] = db_signal.to_dict()

            logger.info(f"Loaded {len(db_signals)} signals from database")
        except Exception as e:
            logger.error(f"Failed to initialize SignalBloomManager: {e}")
            raise

    async def connect(self, websocket: WebSocket):
        """Add a new WebSocket connection."""
        try:
            await websocket.accept()
            self.connections.add(websocket)
            logger.info(f"New WebSocket connection. Total connections: {len(self.connections)}")

            # Send existing signals to new connection
            for signal_id, signal_data in self.signals.items():
                try:
                    message = json.dumps({"type": "signal", "id": signal_id, **signal_data})
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
        if (
            not isinstance(text, str)
            or len(text.strip()) == 0
            or len(text) > Config.MAX_SIGNAL_LENGTH
        ):
            return False

        x = signal_data.get("x", 50)
        y = signal_data.get("y", 50)
        if not (isinstance(x, (int, float)) and 0 <= x <= 100):
            return False
        if not (isinstance(y, (int, float)) and 0 <= y <= 100):
            return False

        return True

    async def broadcast_signal(self, signal_data: dict):
        """Broadcast a new signal to all connected clients and save to database."""
        try:
            # Validate input
            if not self._validate_signal_data(signal_data):
                logger.warning(f"Invalid signal data received: {signal_data}")
                return

            # Generate unique signal ID
            signal_id = f"signal_{len(self.signals)}_{datetime.now().timestamp()}"

            # Check if signal text matches an innovation object
            innovation_object = await db_manager.find_innovation_object(signal_data["text"])
            innovation_object_id = innovation_object.id if innovation_object else None

            # Prepare signal data
            processed_signal = {
                "id": signal_id,
                "text": signal_data["text"].strip(),
                "timestamp": datetime.now().isoformat(),
                "x": max(0, min(100, signal_data.get("x", 50))),
                "y": max(0, min(100, signal_data.get("y", 50))),
                "innovation_object_id": innovation_object_id,
            }

            # Save to database
            try:
                await db_manager.save_signal(processed_signal)
            except Exception as e:
                logger.error(f"Failed to save signal to database: {e}")
                # Continue with broadcasting even if database save fails

            # Store in memory cache
            self.signals[signal_id] = processed_signal.copy()
            self.signals[signal_id]["has_innovation_tree"] = innovation_object_id is not None

            # Cleanup old signals if needed
            if len(self.signals) >= self.max_signals:
                await self._cleanup_signals()

            # Broadcast to all connections
            message = json.dumps(
                {
                    "type": "signal",
                    **processed_signal,
                    "has_innovation_tree": innovation_object_id is not None,
                }
            )

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

    async def _cleanup_signals(self):
        """Clean up old signals from memory and database"""
        try:
            # Remove oldest signals from memory (simple FIFO)
            signals_to_remove = len(self.signals) - (self.max_signals // 2)
            if signals_to_remove > 0:
                oldest_keys = list(self.signals.keys())[:signals_to_remove]
                for key in oldest_keys:
                    del self.signals[key]
                logger.info(f"Cleaned up {len(oldest_keys)} old signals from memory")

            # Cleanup database
            cleaned_count = await db_manager.cleanup_old_signals()
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} old signals from database")

        except Exception as e:
            logger.error(f"Error during signal cleanup: {e}")

    async def shutdown(self):
        """Cleanup resources on shutdown"""
        try:
            await db_manager.close()
            logger.info("SignalBloomManager shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


# Global manager instance
bloom_manager = SignalBloomManager()


async def create_app():
    """Create and configure the Starlette application."""

    async def startup_event():
        """Initialize application on startup"""
        try:
            await bloom_manager.initialize()
            await voice_processor.initialize()
            logger.info("Application startup complete")
        except Exception as e:
            logger.error(f"Failed to start application: {e}")
            raise

    async def shutdown_event():
        """Cleanup on application shutdown"""
        try:
            await bloom_manager.shutdown()
            await voice_processor.close()
            logger.info("Application shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

    # Application routes
    routes = [
        Route("/", frontend_endpoint),
        Route("/status", status_endpoint),
        Route("/voice/status", voice_status_endpoint),
        Route("/voice/tts", text_to_speech_endpoint, methods=["GET", "POST"]),
        Route("/api/innovation/objects", innovation_objects_endpoint),
        Route("/api/innovation/tree/{object_id}", innovation_tree_endpoint),
        WebSocketRoute("/ws", websocket_endpoint),
    ]

    # Create application
    app = Starlette(debug=Config.DEBUG, routes=routes)

    # Add startup and shutdown events
    app.add_event_handler("startup", startup_event)
    app.add_event_handler("shutdown", shutdown_event)

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=Config.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


async def startup_event():
    """Initialize application on startup"""
    try:
        await bloom_manager.initialize()
        await voice_processor.initialize()
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise


async def shutdown_event():
    """Cleanup on application shutdown"""
    try:
        await bloom_manager.shutdown()
        await voice_processor.close()
        logger.info("Application shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


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
                await websocket.send_text(
                    json.dumps({"type": "error", "message": "Invalid JSON format"})
                )
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
        voice_available = (
            await voice_processor.elevenlabs_client.is_available()
            if voice_processor.voice_enabled
            else False
        )

        return JSONResponse(
            {
                "status": "healthy",
                "service": "Signal Bloom Backend",
                "version": "1.0.0",
                "connections": len(bloom_manager.connections),
                "signals": len(bloom_manager.signals),
                "timestamp": datetime.now().isoformat(),
                "features": {
                    "voice_enabled": voice_processor.voice_enabled,
                    "voice_available": voice_available,
                    "database_enabled": True,
                },
                "uptime": "N/A",  # TODO: Add uptime tracking
            }
        )
    except Exception as e:
        logger.error(f"Error in status endpoint: {e}")
        return JSONResponse({"status": "error", "message": "Health check failed"}, status_code=500)


async def voice_status_endpoint(request):
    """Voice service status endpoint."""
    try:
        if not voice_processor.voice_enabled:
            return JSONResponse(
                {"voice_enabled": False, "message": "Voice processing not configured"}
            )

        available = await voice_processor.elevenlabs_client.is_available()
        voices = await voice_processor.get_available_voices() if available else None

        return JSONResponse(
            {
                "voice_enabled": True,
                "voice_available": available,
                "voices_count": len(voices) if voices else 0,
                "current_voice_id": voice_processor.elevenlabs_client.voice_id,
            }
        )
    except Exception as e:
        logger.error(f"Error in voice status endpoint: {e}")
        return JSONResponse({"error": "Voice status check failed"}, status_code=500)


async def text_to_speech_endpoint(request):
    """Convert text to speech endpoint."""
    try:
        if not voice_processor.voice_enabled:
            return JSONResponse({"error": "Voice processing not enabled"}, status_code=503)

        # Get text from query params or JSON body
        text = request.query_params.get("text")
        if not text:
            try:
                body = await request.json()
                text = body.get("text")
            except:
                pass

        if not text:
            return JSONResponse({"error": "No text provided"}, status_code=400)

        # Generate speech
        audio_data = await voice_processor.process_signal_to_speech(text)

        if audio_data:
            from starlette.responses import Response

            return Response(
                audio_data,
                media_type="audio/mpeg",
                headers={"Content-Disposition": "inline; filename=speech.mp3"},
            )
        else:
            return JSONResponse({"error": "Failed to generate speech"}, status_code=500)

    except Exception as e:
        logger.error(f"Error in TTS endpoint: {e}")
        return JSONResponse({"error": "TTS processing failed"}, status_code=500)


async def innovation_tree_endpoint(request):
    """Get innovation tree for a specific object."""
    try:
        object_id = request.path_params.get("object_id")
        if not object_id:
            return JSONResponse({"error": "Object ID is required"}, status_code=400)

        tree = await db_manager.get_innovation_tree(object_id)
        if not tree:
            return JSONResponse({"error": "Innovation object not found"}, status_code=404)

        return JSONResponse(tree)

    except Exception as e:
        logger.error(f"Error in innovation tree endpoint: {e}")
        return JSONResponse({"error": "Failed to get innovation tree"}, status_code=500)


async def innovation_objects_endpoint(request):
    """List available innovation objects."""
    try:
        async with await db_manager.get_session() as session:
            from sqlalchemy import select

            stmt = select(InnovationObject).order_by(InnovationObject.name)
            result = await session.execute(stmt)
            objects = result.scalars().all()

            return JSONResponse({"objects": [obj.to_dict() for obj in objects]})

    except Exception as e:
        logger.error(f"Error in innovation objects endpoint: {e}")
        return JSONResponse({"error": "Failed to get innovation objects"}, status_code=500)


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


if __name__ == "__main__":
    import asyncio

    async def run_server():
        """Run the development server."""
        app = await create_app()

        logger.info("Starting Signal Bloom Backend Server")
        try:
            # Import uvicorn here to avoid import issues in tests
            import uvicorn

            config = uvicorn.Config(
                app=app,
                host=Config.HOST,
                port=Config.PORT,
                log_level=Config.LOG_LEVEL,
                access_log=True,
            )
            server = uvicorn.Server(config)
            await server.serve()
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            raise

    asyncio.run(run_server())
