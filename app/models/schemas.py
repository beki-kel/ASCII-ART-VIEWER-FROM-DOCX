"""
Data models for ASCII Art Viewer - Competition Edition
Clean, type-safe data structures for the application
"""

from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ExtractionMethod(str, Enum):
    """Enumeration of available extraction methods"""
    COORDINATE_BASED = "coordinate-based"
    TABLE_BASED = "table-based"
    PRE_FORMATTED = "pre-formatted"
    PARAGRAPH_BASED = "paragraph-based"
    NONE = "none"


class ProcessingStatus(str, Enum):
    """Processing status enumeration"""
    PENDING = "pending"
    FETCHING = "fetching"
    PARSING = "parsing"
    EXTRACTING = "extracting"
    ENHANCING = "enhancing"
    COMPLETED = "completed"
    FAILED = "failed"


class ColorMode(str, Enum):
    """Display color modes"""
    AUTO = "auto"
    RAINBOW = "rainbow"
    HIGHLIGHT = "highlight"
    GRADIENT = "gradient"
    MATRIX = "matrix"
    CYBERPUNK = "cyberpunk"
    CLASSIC = "classic"
    NONE = "none"





class OutputFormat(str, Enum):
    """Output format options"""
    TXT = "txt"
    JSON = "json"
    HTML = "html"
    SVG = "svg"
    PNG = "png"


class ThemeMode(str, Enum):
    """UI theme modes"""
    DARK = "dark"
    CYBERPUNK = "cyberpunk"
    MATRIX = "matrix"
    CLASSIC = "classic"


class ProcessingStep(BaseModel):
    """Individual processing step information"""
    step: str
    status: ProcessingStatus
    message: str
    timestamp: datetime
    duration_ms: Optional[int] = None
    details: Optional[Dict[str, Any]] = None


class AsciiArtMetadata(BaseModel):
    """Metadata about extracted ASCII art"""
    width: int
    height: int
    character_count: int
    unique_characters: int
    extraction_method: ExtractionMethod
    source_url: str
    extraction_time_ms: int
    coordinates_based: bool = False
    table_based: bool = False
    paragraph_based: bool = False
    pre_formatted: bool = False
    tables_found: int = 0
    paragraphs_found: int = 0
    pre_blocks_found: int = 0


class ProcessingRequest(BaseModel):
    """Request model for ASCII art processing"""
    url: HttpUrl
    color_mode: ColorMode = ColorMode.AUTO
    output_format: OutputFormat = OutputFormat.TXT


class ProcessingResponse(BaseModel):
    """Response model for ASCII art processing"""
    id: str
    status: ProcessingStatus
    ascii_art: Optional[str] = None
    metadata: Optional[AsciiArtMetadata] = None
    steps: List[ProcessingStep] = []
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    total_duration_ms: Optional[int] = None


class ExtractionStats(BaseModel):
    """Statistics about the extraction process"""
    tables_found: int = 0
    paragraphs_found: int = 0
    pre_blocks_found: int = 0
    total_characters: int = 0
    valid_coordinates: int = 0
    invalid_rows: int = 0


class WebSocketMessage(BaseModel):
    """WebSocket message structure"""
    type: str  # "step_update", "progress", "completed", "error"
    session_id: str
    data: Dict[str, Any]
    timestamp: datetime