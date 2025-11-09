"""
HTML Parser Service - Convenience module for backward compatibility
Re-exports classes from their individual modules
"""

from .ascii_art_parser import AsciiArtParser
from .parser_service import ParserService

__all__ = ['AsciiArtParser', 'ParserService']