"""
Unit tests for the reranking system.
"""

import pytest
from unittest.mock import MagicMock, patch

from src.knowledge_base.core.config import Config
from src.knowledge_base.core.types import TextChunk
from src.knowledge_base.retrieval.reranker import (
    Reranker, 
    ExactMatchReranker, 
    LengthNormalizedReranker,
    MetadataBoostReranker,
    EnsembleReranker
)


class TestReranker:
    """Test the Reranker class."""
    
    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        config = Config()
        config.retrieval.enable_reranking = True
        config.retrieval.rerank_model = "exact_match"
        config.retrieval.rerank_top_k = 3
        return config
    
    @pytest.fixture
    def results(self):
        """Create test results."""
        chunks = [
            TextChunk(id="chunk1", text="This is a test document about AI and machine learning", document_id="doc1"),
            TextChunk(id="chunk2", text="Python is a programming language", document_id="doc2"),
            TextChunk(id="chunk3", text="Machine learning is a subset of artificial intelligence", document_id="doc3"),
            TextChunk(id="chunk4", text="This document discusses AI applications", document_id="doc4"),
            TextChunk(id="chunk5", text="Natural language processing is important for AI", document_id="doc5"),
        ]
        
        # Initial scores
        scores = [0.85, 0.75, 0.65, 0.55, 0.45]
        
        return [(chunks[i], scores[i]) for i in range(len(chunks))]
    
    def test_reranker_initialization(self, config):
        """Test that the reranker initializes correctly."""
        reranker = Reranker(config)
        assert reranker.config == config
        assert isinstance(reranker.strategy, ExactMatchReranker)
    
    def test_reranker_disabled(self, config, results):
        """Test that reranking is skipped when disabled."""
        config.retrieval.enable_reranking = False
        reranker = Reranker(config)
        
        reranked = reranker.rerank("AI machine learning", results)
        
        # Should return original results unchanged
        assert reranked == results
    
    def test_exact_match_reranker(self, config, results):
        """Test the exact match reranker."""
        config.retrieval.rerank_model = "exact_match"
        reranker = Reranker(config)
        
        reranked = reranker.rerank("AI machine learning", results)
        
        # Check that results are reordered
        assert len(reranked) == len(results)
        
        # The third chunk (index 2) should be boosted because it contains both "AI" and "machine learning"
        # It might not be first because the original score was lower
        chunk_ids = [chunk.id for chunk, _ in reranked]
        assert "chunk3" in chunk_ids[:3]
    
    def test_length_normalized_reranker(self, config, results):
        """Test the length normalized reranker."""
        config.retrieval.rerank_model = "length_normalized"
        reranker = Reranker(config)
        
        reranked = reranker.rerank("AI", results)
        
        # Check that results are reordered
        assert len(reranked) == len(results)
        
        # Shorter chunks should be boosted
        # chunk2 and chunk4 are shorter than others
        chunk_ids = [chunk.id for chunk, _ in reranked]
        assert "chunk2" in chunk_ids[:3] or "chunk4" in chunk_ids[:3]
    
    def test_metadata_boost_reranker(self, config, results):
        """Test the metadata boost reranker."""
        config.retrieval.rerank_model = "metadata_boost"
        reranker = Reranker(config)
        
        # Add metadata to chunks
        results[2][0].metadata["relevance"] = "high"
        results[4][0].metadata["relevance"] = "high"
        
        # Provide boost fields in kwargs
        reranked = reranker.rerank(
            "AI", 
            results, 
            boost_fields={"relevance": 0.2}
        )
        
        # Check that results with boosted metadata are ranked higher
        assert len(reranked) == len(results)
        
        # chunk3 and chunk5 should be boosted due to metadata
        chunk_ids = [chunk.id for chunk, _ in reranked]
        assert "chunk3" in chunk_ids[:3]
        assert "chunk5" in chunk_ids[:3]
    
    def test_ensemble_reranker(self, config, results):
        """Test the ensemble reranker."""
        config.retrieval.rerank_model = "ensemble"
        reranker = Reranker(config)
        
        # Add metadata to chunks
        results[2][0].metadata["relevance"] = "high"
        
        reranked = reranker.rerank(
            "AI machine learning", 
            results,
            boost_fields={"relevance": 0.2}
        )
        
        # Check that results are reordered
        assert len(reranked) == len(results)
        
        # chunk3 should be boosted by all rerankers
        chunk_ids = [chunk.id for chunk, _ in reranked]
        assert "chunk3" in chunk_ids[:2]
    
    def test_rerank_top_k(self, config, results):
        """Test that reranking respects top_k limit."""
        config.retrieval.rerank_top_k = 3
        reranker = Reranker(config)
        
        reranked = reranker.rerank("AI", results)
        
        # Should only return top 3 results
        assert len(reranked) == 3
    
    def test_rerank_empty_results(self, config):
        """Test reranking with empty results."""
        reranker = Reranker(config)
        
        reranked = reranker.rerank("AI", [])
        
        # Should return empty list
        assert reranked == []
    
    def test_rerank_error_handling(self, config, results):
        """Test error handling during reranking."""
        reranker = Reranker(config)
        
        # Mock the strategy to raise an exception
        reranker.strategy.rerank = MagicMock(side_effect=Exception("Test error"))
        
        # Should return original results on error
        reranked = reranker.rerank("AI", results)
        assert reranked == results