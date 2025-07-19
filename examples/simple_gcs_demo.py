#!/usr/bin/env python
"""
Simple GCS Storage Demo.

This script demonstrates how to use Google Cloud Storage for the unified knowledge base system.
"""

import os
import sys
import json
from datetime import datetime

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the simplified KnowledgeBase
from src.knowledge_base import KnowledgeBase


class GCSDemo:
    """Simple GCS Storage Demo."""
    
    def __init__(self):
        """Initialize the demo."""
        self.kb = KnowledgeBase()
    
    def run(self):
        """Run the demo."""
        print("====================================================================")
        print("    Google Cloud Storage (GCS) Simple Demo")
        print("====================================================================\n")
        
        # Add a document about GCS
        print("Adding document about GCS...")
        gcs_doc = """
        # Google Cloud Storage
        
        Google Cloud Storage is a RESTful online file storage web service for storing and accessing data on
        Google Cloud Platform infrastructure. The service combines the performance and scalability of Google's
        cloud with advanced security and sharing capabilities.
        
        ## Key Features
        
        - Object storage with high durability and availability
        - Multiple storage classes for different use cases
        - Strong consistency
        - Integrated with Google Cloud IAM
        - Lifecycle management policies
        - Object versioning and retention policies
        """
        
        result = self.kb.add_document(
            content=gcs_doc,
            metadata={
                "title": "Google Cloud Storage Overview",
                "source": "documentation",
                "date": datetime.now().isoformat()
            }
        )
        
        print(f"Document added with ID: {result.document_id}")
        print(f"Created {len(result.chunk_ids)} chunks")
        
        # Query the knowledge base
        print("\nQuerying about GCS features...")
        query_result = self.kb.query("What are the key features of Google Cloud Storage?")
        
        print(f"\nAnswer: {query_result.answer}")
        print("\nSources:")
        for i, chunk in enumerate(query_result.chunks):
            print(f"  {i+1}. {chunk.text[:100]}...")
        
        # Save results to file
        print("\nSaving results to gcs_demo_results.json...")
        with open("gcs_demo_results.json", "w", encoding="utf-8") as f:
            json.dump({
                "query": "What are the key features of Google Cloud Storage?",
                "answer": query_result.answer,
                "sources": [chunk.text for chunk in query_result.chunks]
            }, f, indent=2)
        
        print("\nDemo completed successfully!")


if __name__ == "__main__":
    demo = GCSDemo()
    demo.run()