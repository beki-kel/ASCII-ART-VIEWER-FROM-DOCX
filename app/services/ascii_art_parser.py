"""
ASCII Art Parser - HTML parsing for ASCII art extraction
Handles HTML parsing logic to extract structured data from HTML documents
"""

from html.parser import HTMLParser
from typing import List, Tuple
from ..models.schemas import ExtractionStats


class AsciiArtParser(HTMLParser):
    """Clean HTML parser focused on ASCII art extraction"""
    
    def __init__(self):
        super().__init__()
        self.reset_state()
    
    def reset_state(self):
        """Reset parser state for new document"""
        # Parsing state
        self.in_table = False
        self.in_td = False
        self.in_paragraph = False
        self.in_pre = False
        self.in_code = False
        
        # Data collection
        self.current_row = []
        self.table_data = []
        self.paragraphs = []
        self.pre_blocks = []
        self.current_para = []
        self.current_pre = []
        
        # Statistics
        self.stats = ExtractionStats()
    
    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str]]):
        """Handle HTML start tags"""
        if tag == 'table':
            self.in_table = True
            self.table_data = []
            self.stats.tables_found += 1
        elif tag == 'tr' and self.in_table:
            self.current_row = []
        elif tag == 'td' and self.in_table:
            self.in_td = True
            self.current_para = []
        elif tag == 'p':
            self.in_paragraph = True
            self.stats.paragraphs_found += 1
        elif tag == 'pre':
            self.in_pre = True
            self.current_pre = []
            self.stats.pre_blocks_found += 1
        elif tag == 'code':
            self.in_code = True
    
    def handle_endtag(self, tag: str):
        """Handle HTML end tags"""
        if tag == 'table':
            self.in_table = False
        elif tag == 'tr' and self.in_table and self.current_row:
            self.table_data.append(self.current_row[:])
        elif tag == 'td' and self.in_table:
            self.in_td = False
            text = ''.join(self.current_para).strip()
            self.current_row.append(text)
            self.current_para = []
        elif tag == 'p':
            self.in_paragraph = False
            if not self.in_table:
                text = ''.join(self.current_para).strip()
                if text:
                    self.paragraphs.append(text)
                self.current_para = []
        elif tag == 'pre':
            self.in_pre = False
            text = ''.join(self.current_pre).strip()
            if text:
                self.pre_blocks.append(text)
            self.current_pre = []
        elif tag == 'code':
            self.in_code = False
    
    def handle_data(self, data: str):
        """Handle text data"""
        self.stats.total_characters += len(data)
        
        if self.in_paragraph:
            self.current_para.append(data)
        elif self.in_pre:
            self.current_pre.append(data)
