#!/usr/bin/env python3
"""
Generation integration test.
Tests the complete RAG pipeline with generation.
"""

import asyncio
import logging
import json
from typing import Dict, Any, List
from knowledge_base.core.knowledge_base import KnowledgeBase
from knowledge_base.core.config import (
    Config,
    StorageConfig, 
    EmbeddingConfig,
    ChunkingConfig,
    RetrievalConfig,
    GenerationConfig
)
from knowledge_base.core.types import Document, DocumentType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GenerationIntegrationTester:
    """Test the complete RAG system with generation."""
    
    def __init__(self):
        self.test_documents = [
            {
                "id": "doc1",
                "content": "Python是一种高级编程语言，以其简洁性和可读性而闻名。Python支持多种编程范式，包括面向对象、函数式和过程式编程。",
                "metadata": {"source": "python_intro", "language": "zh"}
            },
            {
                "id": "doc2", 
                "content": "Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions without being explicitly programmed. It uses algorithms to analyze data and identify patterns.",
                "metadata": {"source": "ml_basics", "language": "en"}
            },
            {
                "id": "doc3",
                "content": "The pandas library in Python provides powerful data structures like DataFrame and Series for data manipulation and analysis. It's widely used in data science and analytics.",
                "metadata": {"source": "pandas_guide", "language": "en"}
            },
            {
                "id": "doc4",
                "content": "深度学习是机器学习的一个分支，使用多层神经网络来模拟人脑的学习过程。它在图像识别、自然语言处理等领域有广泛应用。",
                "metadata": {"source": "deep_learning", "language": "zh"}
            }
        ]
        
        self.test_queries = [
            {
                "query": "What is Python?",
                "expected_language": "en",
                "expected_topics": ["python", "programming"]
            },
            {
                "query": "Python是什么？",
                "expected_language": "zh", 
                "expected_topics": ["python", "编程"]
            },
            {
                "query": "Tell me about machine learning",
                "expected_language": "en",
                "expected_topics": ["machine learning", "ai"]
            },
            {
                "query": "什么是深度学习？",
                "expected_language": "zh",
                "expected_topics": ["深度学习", "神经网络"]
            },
            {
                "query": "How does pandas help with data analysis?",
                "expected_language": "en",
                "expected_topics": ["pandas", "data analysis"]
            }
        ]
    
    async def setup_knowledge_base(self, generation_provider: str = "simple") -> KnowledgeBase:
        """Setup knowledge base with test data."""
        config = Config(
            embedding=EmbeddingConfig(
                provider="sentence_transformers",
                model="all-MiniLM-L6-v2"
            ),
            chunking=ChunkingConfig(
                chunk_size=200,
                chunk_overlap=50
            ),
            storage=StorageConfig(
                provider="memory"
            ),
            retrieval=RetrievalConfig(
                strategy="semantic",
                top_k=3,
                min_score=0.1
            ),
            generation=GenerationConfig(
                provider=generation_provider,
                temperature=0.7,
                max_tokens=500
            )
        )
        
        kb = KnowledgeBase(config)
        await kb.initialize()
        
        # Add test documents
        for doc_data in self.test_documents:
            document = Document(
                id=doc_data["id"],
                content=doc_data["content"],
                type=DocumentType.TEXT,
                metadata=doc_data["metadata"]
            )
            await kb.add_document(document)
        
        return kb
    
    async def test_rag_pipeline(self, generation_provider: str) -> Dict[str, Any]:
        """Test the complete RAG pipeline."""
        logger.info(f"\n=== Testing RAG Pipeline with {generation_provider} ===")
        
        try:
            # Setup knowledge base
            kb = await self.setup_knowledge_base(generation_provider)
            
            results = []
            
            for test_case in self.test_queries:
                query = test_case["query"]
                logger.info(f"Query: {query}")
                
                try:
                    # Perform RAG query
                    query_result = await kb.query(query)
                    
                    # Analyze results
                    result = {
                        "query": query,
                        "answer": query_result.answer,
                        "confidence": query_result.confidence,
                        "retrieval_count": len(query_result.sources),
                        "retrieved_sources": [r.metadata.get("source", "unknown") for r in query_result.sources],
                        "success": True,
                        "error": None,
                        "expected_language": test_case["expected_language"],
                        "expected_topics": test_case["expected_topics"]
                    }
                    
                    logger.info(f"Answer: {query_result.answer[:100]}...")
                    logger.info(f"Confidence: {query_result.confidence:.2f}")
                    logger.info(f"Retrieved {len(query_result.sources)} chunks")
                    
                except Exception as e:
                    result = {
                        "query": query,
                        "answer": None,
                        "confidence": 0.0,
                        "retrieval_count": 0,
                        "retrieved_sources": [],
                        "success": False,
                        "error": str(e),
                        "expected_language": test_case["expected_language"],
                        "expected_topics": test_case["expected_topics"]
                    }
                    logger.error(f"Error: {e}")
                
                results.append(result)
            
            # Close knowledge base
            await kb.close()
            
            return {
                "provider": generation_provider,
                "results": results,
                "total_queries": len(self.test_queries),
                "successful_queries": sum(1 for r in results if r["success"]),
                "average_confidence": sum(r["confidence"] for r in results if r["success"]) / max(1, sum(1 for r in results if r["success"])),
                "average_retrieval_count": sum(r["retrieval_count"] for r in results if r["success"]) / max(1, sum(1 for r in results if r["success"]))
            }
            
        except Exception as e:
            logger.error(f"RAG pipeline test failed: {e}")
            return {
                "provider": generation_provider,
                "error": str(e),
                "results": [],
                "total_queries": 0,
                "successful_queries": 0,
                "average_confidence": 0.0,
                "average_retrieval_count": 0.0
            }
    
    async def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests for different providers."""
        logger.info("Starting RAG integration tests...")
        
        providers_to_test = ["simple"]  # Only test simple provider for now
        
        all_results = {}
        
        for provider in providers_to_test:
            result = await self.test_rag_pipeline(provider)
            all_results[provider] = result
        
        # Generate summary
        summary = self._generate_summary(all_results)
        
        return {
            "summary": summary,
            "detailed_results": all_results,
            "test_timestamp": asyncio.get_event_loop().time()
        }
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test summary."""
        total_providers = len(results)
        working_providers = sum(1 for r in results.values() if r.get("successful_queries", 0) > 0)
        
        provider_stats = {}
        for provider, result in results.items():
            provider_stats[provider] = {
                "working": result.get("successful_queries", 0) > 0,
                "success_rate": result.get("successful_queries", 0) / max(1, result.get("total_queries", 1)),
                "average_confidence": result.get("average_confidence", 0.0),
                "average_retrieval_count": result.get("average_retrieval_count", 0.0),
                "error": result.get("error")
            }
        
        return {
            "total_providers_tested": total_providers,
            "working_providers": working_providers,
            "provider_stats": provider_stats,
            "overall_success_rate": working_providers / total_providers if total_providers > 0 else 0
        }


async def main():
    """Main test function."""
    tester = GenerationIntegrationTester()
    
    try:
        results = await tester.run_integration_tests()
        
        # Save results to file
        with open("rag_integration_test_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print("\n" + "="*60)
        print("RAG INTEGRATION TEST SUMMARY")
        print("="*60)
        
        summary = results["summary"]
        print(f"Total providers tested: {summary['total_providers_tested']}")
        print(f"Working providers: {summary['working_providers']}")
        print(f"Overall success rate: {summary['overall_success_rate']:.1%}")
        
        print("\nProvider Details:")
        for provider, stats in summary["provider_stats"].items():
            status = "✓ Working" if stats["working"] else "✗ Failed"
            print(f"  {provider}: {status}")
            if stats["working"]:
                print(f"    Success rate: {stats['success_rate']:.1%}")
                print(f"    Avg confidence: {stats['average_confidence']:.2f}")
                print(f"    Avg retrieval count: {stats['average_retrieval_count']:.1f}")
            elif stats["error"]:
                print(f"    Error: {stats['error']}")
        
        print(f"\nDetailed results saved to: rag_integration_test_results.json")
        
    except Exception as e:
        logger.error(f"Integration test execution failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())