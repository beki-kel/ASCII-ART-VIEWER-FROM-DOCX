"""
ASCII Art Viewer - Competition Edition Web Application
Modern FastAPI application with WebSocket support and beautiful UI
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import JSONResponse
import json
from typing import Dict, List
import asyncio
import os

from app.models.schemas import ProcessingRequest, ProcessingResponse, WebSocketMessage
from app.services.processor import ProcessorService
from app.config import settings

# Initialize FastAPI app
app = FastAPI(
    title="ASCII Art Viewer - Competition Edition",
    description="Professional ASCII Art Extraction Web Application",
    version="3.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Initialize services
processor_service = ProcessorService()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
    
    async def send_message(self, session_id: str, message: WebSocketMessage):
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_text(
                    json.dumps(message.dict(), default=str)
                )
            except Exception:
                # Connection closed, remove it
                self.disconnect(session_id)

manager = ConnectionManager()


@app.get("/health")
async def health_check():
    """Health check endpoint for deployment platforms"""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "version": "3.0.0"
    }


@app.get("/")
async def home(request: Request):
    """Serve the main web interface"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/process", response_model=dict)
async def process_ascii_art(request: ProcessingRequest):
    """Start processing ASCII art from URL"""
    try:
        print(f"Starting processing for URL: {request.url}")
        session_id = await processor_service.process_request(request)
        print(f"Created session: {session_id}")
        return {"session_id": session_id, "status": "processing_started"}
    except Exception as e:
        print(f"Processing error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/session/{session_id}", response_model=ProcessingResponse)
async def get_session_status(session_id: str):
    """Get current status of processing session"""
    session = processor_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.delete("/api/session/{session_id}")
async def cleanup_session(session_id: str):
    """Clean up processing session"""
    processor_service.cleanup_session(session_id)
    manager.disconnect(session_id)
    return {"message": "Session cleaned up"}


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket, session_id)
    
    # Register callback for this session with proper error handling
    async def send_update(message: WebSocketMessage):
        try:
            await manager.send_message(session_id, message)
        except Exception as e:
            print(f"WebSocket send error for session {session_id}: {e}")
            manager.disconnect(session_id)
    
    processor_service.register_callback(session_id, send_update)
    
    try:
        while True:
            # Keep connection alive and handle ping/pong
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_text('{"type":"ping"}')
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        print(f"WebSocket error for session {session_id}: {e}")
        manager.disconnect(session_id)


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ASCII Art Viewer",
        "version": "3.0.0",
        "active_sessions": len(processor_service.active_sessions)
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if app.debug else "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host=settings.host, 
        port=settings.port, 
        reload=settings.debug,
        log_level=settings.log_level
    )