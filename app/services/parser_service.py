"""
Parser Service - ASCII art extraction service
Handles the overall parsing workflow and extraction strategies
"""

import re
import time
from typing import List, Tuple, Optional
from datetime import datetime
from ..models.schemas import ExtractionMethod, ExtractionStats, ProcessingStep, ProcessingStatus
from .ascii_art_parser import AsciiArtParser


class ParserService:
    """Service for parsing HTML and extracting ASCII art"""
    
    def __init__(self):
        self.parser = AsciiArtParser()
    
    def parse_html(self, html_content: str) -> Tuple[ExtractionStats, List[ProcessingStep]]:
        """Parse HTML content and collect data"""
        steps = []
        start_time = time.time()
        
        # Reset parser state
        self.parser.reset_state()
        
        # Parse HTML
        steps.append(ProcessingStep(
            step="html_parsing",
            status=ProcessingStatus.PENDING,
            message="Parsing HTML content...",
            timestamp=datetime.now()
        ))
        
        try:
            self.parser.feed(html_content)
            
            duration_ms = int((time.time() - start_time) * 1000)
            steps[-1].status = ProcessingStatus.COMPLETED
            steps[-1].message = f"HTML parsed successfully in {duration_ms}ms"
            steps[-1].duration_ms = duration_ms
            steps[-1].details = {
                "tables_found": self.parser.stats.tables_found,
                "paragraphs_found": self.parser.stats.paragraphs_found,
                "pre_blocks_found": self.parser.stats.pre_blocks_found,
                "total_characters": self.parser.stats.total_characters
            }
            
            return self.parser.stats, steps
            
        except Exception as e:
            steps[-1].status = ProcessingStatus.FAILED
            steps[-1].message = f"HTML parsing failed: {str(e)}"
            raise
    
    def extract_ascii_art(self) -> Tuple[str, ExtractionMethod, List[ProcessingStep]]:
        """Extract ASCII art using multiple strategies"""
        steps = []
        
        # Strategy 1: Coordinate-based rendering
        if self.parser.table_data:
            steps.append(ProcessingStep(
                step="coordinate_extraction",
                status=ProcessingStatus.PENDING,
                message="Attempting coordinate-based extraction...",
                timestamp=datetime.now()
            ))
            
            start_time = time.time()
            art_content = self._render_from_coordinates()
            
            if art_content:
                duration_ms = int((time.time() - start_time) * 1000)
                steps[-1].status = ProcessingStatus.COMPLETED
                steps[-1].message = "Coordinate-based extraction successful"
                steps[-1].duration_ms = duration_ms
                return art_content, ExtractionMethod.COORDINATE_BASED, steps
            else:
                steps[-1].status = ProcessingStatus.FAILED
                steps[-1].message = "Coordinate-based extraction failed, trying table-based"
                
                # Strategy 2: Direct table rendering
                steps.append(ProcessingStep(
                    step="table_extraction",
                    status=ProcessingStatus.PENDING,
                    message="Attempting table-based extraction...",
                    timestamp=datetime.now()
                ))
                
                start_time = time.time()
                art_content = self._render_from_table()
                duration_ms = int((time.time() - start_time) * 1000)
                
                steps[-1].status = ProcessingStatus.COMPLETED
                steps[-1].message = "Table-based extraction successful"
                steps[-1].duration_ms = duration_ms
                return art_content, ExtractionMethod.TABLE_BASED, steps
        
        # Strategy 3: Pre-formatted blocks
        elif self.parser.pre_blocks:
            steps.append(ProcessingStep(
                step="pre_extraction",
                status=ProcessingStatus.PENDING,
                message="Extracting from pre-formatted blocks...",
                timestamp=datetime.now()
            ))
            
            start_time = time.time()
            art_content = '\n\n'.join(self.parser.pre_blocks)
            duration_ms = int((time.time() - start_time) * 1000)
            
            steps[-1].status = ProcessingStatus.COMPLETED
            steps[-1].message = f"Extracted from {len(self.parser.pre_blocks)} pre-formatted blocks"
            steps[-1].duration_ms = duration_ms
            return art_content, ExtractionMethod.PRE_FORMATTED, steps
        
        # Strategy 4: Paragraph analysis
        elif self.parser.paragraphs:
            steps.append(ProcessingStep(
                step="paragraph_extraction",
                status=ProcessingStatus.PENDING,
                message="Analyzing paragraphs for ASCII content...",
                timestamp=datetime.now()
            ))
            
            start_time = time.time()
            art_content = self._extract_from_paragraphs()
            duration_ms = int((time.time() - start_time) * 1000)
            
            steps[-1].status = ProcessingStatus.COMPLETED
            steps[-1].message = f"Extracted ASCII art from {len(self.parser.paragraphs)} paragraphs"
            steps[-1].duration_ms = duration_ms
            return art_content, ExtractionMethod.PARAGRAPH_BASED, steps
        
        # No extraction possible
        steps.append(ProcessingStep(
            step="extraction_failed",
            status=ProcessingStatus.FAILED,
            message="No ASCII art content found in document",
            timestamp=datetime.now()
        ))
        
        return "No ASCII art found in the document", ExtractionMethod.NONE, steps
    
    def _render_from_coordinates(self) -> Optional[str]:
        """Render ASCII art from coordinate-based table data"""
        try:
            data_rows = []
            
            for i, row in enumerate(self.parser.table_data):
                if len(row) >= 3:
                    try:
                        x = int(row[0])
                        char = row[1]
                        y = int(row[2])
                        if char:  # Only add if character is not empty
                            data_rows.append((x, y, char))
                    except (ValueError, IndexError):
                        self.parser.stats.invalid_rows += 1
                        continue
                else:
                    self.parser.stats.invalid_rows += 1
            
            if not data_rows:
                return None
            
            self.parser.stats.valid_coordinates = len(data_rows)
            
            # Calculate canvas dimensions
            max_x = max(row[0] for row in data_rows)
            max_y = max(row[1] for row in data_rows)
            min_x = min(row[0] for row in data_rows)
            min_y = min(row[1] for row in data_rows)
            
            # Create canvas
            width = max_x - min_x + 1
            height = max_y - min_y + 1
            canvas = [[' ' for _ in range(width)] for _ in range(height)]
            
            # Place characters on canvas (flip Y-axis)
            for x, y, char in data_rows:
                canvas_x = x - min_x
                canvas_y = max_y - y  # Flip Y-axis
                if 0 <= canvas_x < width and 0 <= canvas_y < height:
                    canvas[canvas_y][canvas_x] = char
            
            # Convert to string
            lines = [''.join(row).rstrip() for row in canvas]
            while lines and not lines[-1].strip():
                lines.pop()
            
            return '\n'.join(lines)
            
        except Exception:
            return None
    
    def _render_from_table(self) -> str:
        """Render ASCII art directly from table rows"""
        rows_to_render = self.parser.table_data
        
        # Skip header row if it doesn't contain ASCII art
        if rows_to_render and not any(c.isdigit() for c in ''.join(rows_to_render[0])):
            rows_to_render = rows_to_render[1:]
        
        return '\n'.join([''.join(row) for row in rows_to_render])
    
    def _extract_from_paragraphs(self) -> str:
        """Extract ASCII art from paragraphs using intelligent filtering"""
        ascii_lines = []
        ascii_chars = ['█', '▀', '▄', '▌', '▐', '░', '▒', '▓', '|', '_', '/', '\\', '+', '*', '#', '@', '■', '□', '▪', '▫', '○', '●']
        
        for para in self.parser.paragraphs:
            # Check for ASCII art characteristics
            ascii_char_count = sum(1 for c in para if c in ascii_chars)
            ascii_density = ascii_char_count / len(para) if para else 0
            
            # Multiple criteria for identifying ASCII art
            is_ascii_art = (
                ascii_density > 0.1 or  # High density of ASCII characters
                any(c in para for c in ascii_chars) or  # Contains ASCII art characters
                '  ' in para or  # Contains multiple spaces
                len(para) > 20 and para.count(' ') / len(para) > 0.3 or  # Spaced content
                re.search(r'[|\\/_\-+*#@]{3,}', para)  # Pattern of ASCII characters
            )
            
            if is_ascii_art:
                ascii_lines.append(para)
        
        if ascii_lines:
            return '\n'.join(ascii_lines)
        
        # Fallback: return all paragraphs
        return '\n'.join(self.parser.paragraphs)
