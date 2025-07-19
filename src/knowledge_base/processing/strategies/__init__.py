"""
Chunking strategies for the unified knowledge base system.
"""

# Import all strategies
from .recursive import RecursiveChunker
from .sentence import SentenceChunker
from .paragraph import ParagraphChunker
from .fixed import FixedLengthChunker

# Register strategies
def register_strategies():
    """Register all chunking strategies."""
    from ..chunker import TextChunker
    TextChunker.register_strategy("recursive", RecursiveChunker)
    TextChunker.register_strategy("sentence", SentenceChunker)
    TextChunker.register_strategy("paragraph", ParagraphChunker)
    TextChunker.register_strategy("fixed", FixedLengthChunker)