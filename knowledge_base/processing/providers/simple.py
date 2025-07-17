"""Simple fallback embedding provider."""

import hashlib
import logging
from typing import List

logger = logging.getLogger(__name__)


class SimpleEmbedder:
    """
    Simple fallback embedder that generates deterministic embeddings
    based on text content. Used when advanced embedding models are not available.
    """
    
    def __init__(self, dimensions: int = 384):
        """Initialize simple embedder."""
        self.dimensions = dimensions
        
        # Enhanced vocabulary with semantic relationships
        self.vocab = {
            # Programming concepts
            'python': [0.8, 0.2, 0.1, 0.3, 0.5, 0.7, 0.4, 0.6],
            '编程': [0.8, 0.2, 0.1, 0.3, 0.5, 0.7, 0.4, 0.6],
            'programming': [0.8, 0.2, 0.1, 0.3, 0.5, 0.7, 0.4, 0.6],
            'language': [0.7, 0.3, 0.2, 0.4, 0.6, 0.8, 0.3, 0.5],
            '语言': [0.7, 0.3, 0.2, 0.4, 0.6, 0.8, 0.3, 0.5],
            'code': [0.6, 0.4, 0.3, 0.5, 0.7, 0.9, 0.2, 0.4],
            '代码': [0.6, 0.4, 0.3, 0.5, 0.7, 0.9, 0.2, 0.4],
            
            # Web frameworks
            'fastapi': [0.5, 0.6, 0.4, 0.7, 0.3, 0.8, 0.5, 0.9],
            'web': [0.4, 0.7, 0.5, 0.8, 0.2, 0.9, 0.6, 0.8],
            'framework': [0.3, 0.8, 0.6, 0.9, 0.1, 0.7, 0.7, 0.7],
            'api': [0.2, 0.9, 0.7, 0.6, 0.4, 0.6, 0.8, 0.6],
            '框架': [0.3, 0.8, 0.6, 0.9, 0.1, 0.7, 0.7, 0.7],
            
            # Machine learning
            'machine': [0.9, 0.1, 0.8, 0.2, 0.7, 0.3, 0.6, 0.4],
            'learning': [0.8, 0.2, 0.9, 0.1, 0.6, 0.4, 0.7, 0.3],
            '机器学习': [0.85, 0.15, 0.85, 0.15, 0.65, 0.35, 0.65, 0.35],
            'artificial': [0.7, 0.3, 0.8, 0.2, 0.5, 0.5, 0.8, 0.2],
            'intelligence': [0.6, 0.4, 0.7, 0.3, 0.4, 0.6, 0.9, 0.1],
            '人工智能': [0.65, 0.35, 0.75, 0.25, 0.45, 0.55, 0.85, 0.15],
            'algorithm': [0.5, 0.5, 0.6, 0.4, 0.3, 0.7, 0.8, 0.2],
            '算法': [0.5, 0.5, 0.6, 0.4, 0.3, 0.7, 0.8, 0.2],
            
            # General concepts
            'design': [0.4, 0.6, 0.5, 0.5, 0.2, 0.8, 0.7, 0.3],
            '设计': [0.4, 0.6, 0.5, 0.5, 0.2, 0.8, 0.7, 0.3],
            'philosophy': [0.3, 0.7, 0.4, 0.6, 0.1, 0.9, 0.6, 0.4],
            '哲学': [0.3, 0.7, 0.4, 0.6, 0.1, 0.9, 0.6, 0.4],
            'modern': [0.2, 0.8, 0.3, 0.7, 0.4, 0.6, 0.5, 0.5],
            '现代': [0.2, 0.8, 0.3, 0.7, 0.4, 0.6, 0.5, 0.5],
            'fast': [0.1, 0.9, 0.2, 0.8, 0.5, 0.5, 0.4, 0.6],
            '快速': [0.1, 0.9, 0.2, 0.8, 0.5, 0.5, 0.4, 0.6],
            'performance': [0.9, 0.1, 0.7, 0.3, 0.8, 0.2, 0.6, 0.4],
            '性能': [0.9, 0.1, 0.7, 0.3, 0.8, 0.2, 0.6, 0.4],
            
            # Common words
            'high': [0.8, 0.2, 0.6, 0.4, 0.7, 0.3, 0.5, 0.5],
            '高级': [0.8, 0.2, 0.6, 0.4, 0.7, 0.3, 0.5, 0.5],
            'simple': [0.2, 0.8, 0.4, 0.6, 0.3, 0.7, 0.5, 0.5],
            '简洁': [0.2, 0.8, 0.4, 0.6, 0.3, 0.7, 0.5, 0.5],
            'readable': [0.3, 0.7, 0.5, 0.5, 0.2, 0.8, 0.6, 0.4],
            '可读性': [0.3, 0.7, 0.5, 0.5, 0.2, 0.8, 0.6, 0.4],
        }
        
        logger.info(f"SimpleEmbedder initialized with {dimensions} dimensions and {len(self.vocab)} vocabulary terms")
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text using vocabulary and hash-based features."""
        if not text or not text.strip():
            return [0.0] * self.dimensions
        
        text_lower = text.lower()
        
        # Find vocabulary matches
        vocab_matches = []
        for word, embedding in self.vocab.items():
            if word in text_lower:
                vocab_matches.append(embedding)
        
        # Generate base embedding
        if vocab_matches:
            # Average vocabulary embeddings
            base_embedding = []
            for i in range(len(vocab_matches[0])):
                avg_val = sum(emb[i] for emb in vocab_matches) / len(vocab_matches)
                base_embedding.append(avg_val)
        else:
            # Use hash-based embedding for unknown text
            base_embedding = self._hash_embedding(text)
        
        # Extend to target dimensions
        if len(base_embedding) < self.dimensions:
            # Repeat and pad the base embedding
            extended = []
            while len(extended) < self.dimensions:
                remaining = self.dimensions - len(extended)
                if remaining >= len(base_embedding):
                    extended.extend(base_embedding)
                else:
                    extended.extend(base_embedding[:remaining])
            return extended
        else:
            return base_embedding[:self.dimensions]
    
    def _hash_embedding(self, text: str) -> List[float]:
        """Generate hash-based embedding for unknown text."""
        # Create multiple hash values for diversity
        hash_values = []
        
        # Use different hash algorithms/seeds
        for seed in [0, 1, 2, 3, 4, 5, 6, 7]:
            hash_input = f"{text}_{seed}".encode('utf-8')
            hash_hex = hashlib.md5(hash_input).hexdigest()
            
            # Convert hex to float values
            for i in range(0, len(hash_hex), 2):
                hex_pair = hash_hex[i:i+2]
                float_val = int(hex_pair, 16) / 255.0
                hash_values.append(float_val)
        
        return hash_values[:8]  # Return first 8 values