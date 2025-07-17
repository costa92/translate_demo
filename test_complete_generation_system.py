#!/usr/bin/env python3
"""
Complete generation system test.
Tests all generation providers with different configurations.
"""

import asyncio
import logging
import json
from typing import Dict, Any, List
from knowledge_base.core.config import GenerationConfig
from knowledge_base.generation.generator import Generator
from knowledge_base.core.types import RetrievalResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GenerationSystemTester:
    """Test the complete generation system."""
    
    def __init__(self):
        self.test_contexts = [
            "Python is a high-level programming language known for its simplicity and readability.",
            "Machine learning is a subset of artificial intelligence that enables computers to learn without being explicitly programmed.",
            "The pandas library in Python provides data structures and data analysis tools for handling structured data."
        ]
        
        self.test_queries = [
            "What is Python?",
            "Tell me about machine learning",
            "How does pandas help with data analysis?",
            "什么是Python？",  # Chinese query
            "机器学习是什么？"  # Chinese query
        ]
    
    async def test_provider(self, provider_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test a specific generation provider."""
        logger.info(f"\n=== Testing {provider_name} Provider ===")
        
        try:
            # Create configuration
            gen_config = GenerationConfig(
                provider=provider_name,
                **config
            )
            
            # Initialize generator
            generator = Generator(gen_config)
            await generator.initialize()
            
            results = []
            
            for query in self.test_queries:
                logger.info(f"Query: {query}")
                
                try:
                    # Generate answer
                    answer, confidence = await generator.generate(
                        query=query,
                        retrieval_results=self.test_contexts
                    )
                    
                    result = {
                        "query": query,
                        "answer": answer,
                        "confidence": confidence,
                        "success": True,
                        "error": None
                    }
                    
                    logger.info(f"Answer: {answer[:100]}...")
                    logger.info(f"Confidence: {confidence:.2f}")
                    
                except Exception as e:
                    result = {
                        "query": query,
                        "answer": None,
                        "confidence": 0.0,
                        "success": False,
                        "error": str(e)
                    }
                    logger.error(f"Error: {e}")
                
                results.append(result)
            
            # Close generator
            await generator.close()
            
            return {
                "provider": provider_name,
                "config": config,
                "results": results,
                "total_queries": len(self.test_queries),
                "successful_queries": sum(1 for r in results if r["success"]),
                "average_confidence": sum(r["confidence"] for r in results if r["success"]) / max(1, sum(1 for r in results if r["success"]))
            }
            
        except Exception as e:
            logger.error(f"Provider {provider_name} initialization failed: {e}")
            return {
                "provider": provider_name,
                "config": config,
                "error": str(e),
                "results": [],
                "total_queries": 0,
                "successful_queries": 0,
                "average_confidence": 0.0
            }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run tests for all providers."""
        logger.info("Starting complete generation system tests...")
        
        # Test configurations for different providers
        test_configs = {
            "simple": {
                "temperature": 0.7,
                "max_tokens": 500
            },
            "deepseek": {
                "api_key": "fake-key-for-testing",
                "model": "deepseek-chat",
                "temperature": 0.7,
                "max_tokens": 500
            },
            "siliconflow": {
                "api_key": "fake-key-for-testing", 
                "model": "Qwen/Qwen2.5-7B-Instruct",
                "temperature": 0.7,
                "max_tokens": 500
            }
        }
        
        all_results = {}
        
        for provider, config in test_configs.items():
            result = await self.test_provider(provider, config)
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
    tester = GenerationSystemTester()
    
    try:
        results = await tester.run_all_tests()
        
        # Save results to file
        with open("generation_test_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print("\n" + "="*60)
        print("GENERATION SYSTEM TEST SUMMARY")
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
            elif stats["error"]:
                print(f"    Error: {stats['error']}")
        
        print(f"\nDetailed results saved to: generation_test_results.json")
        
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())