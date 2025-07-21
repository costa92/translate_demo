"""
Unified Knowledge Base System

A comprehensive knowledge management, retrieval, and generation system.
"""

__version__ = "0.1.0"

# Import the KnowledgeBase class from core module
from .core.knowledge_base import KnowledgeBase
from .core.config_fixed import Config

# Import the SimpleKnowledgeBase for quick start examples
from .simple_kb import SimpleKnowledgeBase