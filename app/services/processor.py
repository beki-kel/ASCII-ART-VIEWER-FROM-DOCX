"""
ASCII Art Processing Service - Core business logic
Handles the complete workflow from URL to final ASCII art
"""

import time
import uuid
import asyncio
import requests
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime
from urllib.parse import urlparse

from ..models.schemas import (
    ProcessingRequest, ProcessingResponse, ProcessingStatus, 
    AsciiArtMetadata, ProcessingStep, ExtractionMethod,
    WebSocketMessage
)
from .parser import ParserService


class ProcessorService:
    """Main service for processing ASCII art requests"""
    
    def __init__(self):
        self.parser_service = ParserService()
        self.active_sessions: Dict[str, ProcessingResponse] = {}
        self.session_callbacks: Dict[str, List[Callable]] = {}
    
    def register_callback(self, session_id: str, callback: Callable):
        """Register callback for session updates"""
        if session_id not in self.session_callbacks:
            self.session_callbacks[session_id] = []
        self.session_callbacks[session_id].append(callback)
    
    def _notify_callbacks(self, session_id: str, message: WebSocketMessage):
        """Notify all callbacks for a session"""
        if session_id in self.session_callbacks:
            for callback in self.session_callbacks[session_id]:
                try:
                    # Handle both sync and async callbacks
                    if asyncio.iscoroutinefunction(callback):
                        asyncio.create_task(callback(message))
                    else:
                        callback(message)
                except Exception as e:
                    print(f"Callback error for session {session_id}: {e}")
                    pass  # Ignore callback errors
    
    async def process_request(self, request: ProcessingRequest) -> str:
        """Process ASCII art request and return session ID"""
        session_id = str(uuid.uuid4())
        
        # Initialize response
        response = ProcessingResponse(
            id=session_id,
            status=ProcessingStatus.PENDING,
            created_at=datetime.now(),
            steps=[]
        )
        
        self.active_sessions[session_id] = response
        
        # Start processing in background
        asyncio.create_task(self._process_async(session_id, request))
        
        return session_id
    
    async def _process_async(self, session_id: str, request: ProcessingRequest):
        """Async processing workflow"""
        response = self.active_sessions[session_id]
        start_time = time.time()
        
        try:
            # Step 1: Fetch document
            await self._update_status(session_id, ProcessingStatus.FETCHING, "Fetching document...")
            html_content = await self._fetch_document(str(request.url))
            
            # Step 2: Parse HTML
            await self._update_status(session_id, ProcessingStatus.PARSING, "Parsing HTML content...")
            stats, parse_steps = self.parser_service.parse_html(html_content)
            response.steps.extend(parse_steps)
            
            # Step 3: Extract ASCII art
            await self._update_status(session_id, ProcessingStatus.EXTRACTING, "Extracting ASCII art...")
            ascii_art, extraction_method, extract_steps = self.parser_service.extract_ascii_art()
            response.steps.extend(extract_steps)
            
            # Step 4: Generate metadata
            metadata = self._generate_metadata(
                ascii_art, extraction_method, str(request.url), 
                int((time.time() - start_time) * 1000), stats
            )
            
            # Complete processing
            response.ascii_art = ascii_art
            response.metadata = metadata
            response.completed_at = datetime.now()
            response.total_duration_ms = int((time.time() - start_time) * 1000)
            
            await self._update_status(session_id, ProcessingStatus.COMPLETED, "Processing completed successfully!")
            
        except Exception as e:
            response.error_message = str(e)
            await self._update_status(session_id, ProcessingStatus.FAILED, f"Processing failed: {str(e)}")
    
    async def _update_status(self, session_id: str, status: ProcessingStatus, message: str):
        """Update processing status and notify callbacks"""
        response = self.active_sessions[session_id]
        response.status = status
        
        # Add step
        step = ProcessingStep(
            step=status.value,
            status=status,
            message=message,
            timestamp=datetime.now()
        )
        response.steps.append(step)
        
        # Notify WebSocket callbacks
        ws_message = WebSocketMessage(
            type="step_update",
            session_id=session_id,
            data={
                "status": status.value,
                "message": message,
                "step": step.dict()
            },
            timestamp=datetime.now()
        )
        
        print(f"Updating status for session {session_id}: {status.value} - {message}")
        self._notify_callbacks(session_id, ws_message)
    
    async def _fetch_document(self, url: str) -> str:
        """Fetch HTML document from URL"""
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("Invalid URL provided")
        
        # Use asyncio to run requests in thread pool
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, self._fetch_sync, url
        )
        
        return response
    
    def _fetch_sync(self, url: str) -> str:
        """Synchronous fetch (run in thread pool)"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'ASCII-Art-Viewer/3.0.0 (Competition-WebApp)'
        })
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = session.get(url, timeout=30)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2)
        
        raise Exception("Failed to fetch document after retries")
    

    
    def _generate_metadata(self, art: str, method: ExtractionMethod, url: str, 
                          extraction_time_ms: int, stats) -> AsciiArtMetadata:
        """Generate metadata for ASCII art"""
        lines = art.split('\n')
        width = max(len(line) for line in lines) if lines else 0
        height = len(lines)
        character_count = len(art)
        unique_characters = len(set(art))
        
        return AsciiArtMetadata(
            width=width,
            height=height,
            character_count=character_count,
            unique_characters=unique_characters,
            extraction_method=method,
            source_url=url,
            extraction_time_ms=extraction_time_ms,
            coordinates_based=(method == ExtractionMethod.COORDINATE_BASED),
            table_based=(method == ExtractionMethod.TABLE_BASED),
            paragraph_based=(method == ExtractionMethod.PARAGRAPH_BASED),
            pre_formatted=(method == ExtractionMethod.PRE_FORMATTED),
            tables_found=stats.tables_found,
            paragraphs_found=stats.paragraphs_found,
            pre_blocks_found=stats.pre_blocks_found
        )
    
    def get_session(self, session_id: str) -> Optional[ProcessingResponse]:
        """Get session by ID"""
        return self.active_sessions.get(session_id)
    
    def cleanup_session(self, session_id: str):
        """Clean up session data"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        if session_id in self.session_callbacks:
            del self.session_callbacks[session_id]