"""
Provider implementations for the processing module.

This module contains implementations of various embedding providers.
"""

from .sentence_transformers import SentenceTransformersEmbedder
from .openai import OpenAIEmbedder
from .deepseek import DeepSeekEmbedder
from .siliconflow import SiliconFlowEmbedder
from .simple import SimpleEmbedder

__all__ = [
    'SentenceTransformersEmbedder',
    'OpenAIEmbedder',
    'DeepSeekEmbedder',
    'SiliconFlowEmbedder',
    'SimpleEmbedder',
]