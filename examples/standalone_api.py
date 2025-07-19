#!/usr/bin/env python
"""
Standalone API server for the Unified Knowledge Base System.

This example demonstrates how to create a simple API server
without depending on the full API server implementation.
"""

import sys
import os
from typing import Dict, Any, List, Optional

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from src.knowledge_base import KnowledgeBase


# Create a knowledge base instance
kb = KnowledgeBase()

# Create FastAPI app
app = FastAPI(
    title="Knowledge Base API",
    description="Simple API for the Unified Knowledge Base System",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Define request and response models
class DocumentRequest(BaseModel):
    """Request model for adding a document."""
    content: str
    metadata: Dict[str, Any] = {}


class DocumentResponse(BaseModel):
    """Response model for document operations."""
    document_id: str
    chunk_count: int
    success: bool


class QueryRequest(BaseModel):
    """Request model for querying the knowledge base."""
    query: str
    metadata_filter: Dict[str, Any] = None


class QueryResponse(BaseModel):
    """Response model for query operations."""
    query: str
    answer: str
    sources: List[Dict[str, Any]] = []


# Define API routes
@app.post("/documents", response_model=DocumentResponse)
async def add_document(request: DocumentRequest):
    """Add a document to the knowledge base."""
    result = kb.add_document(
        content=request.content,
        metadata=request.metadata
    )
    
    return {
        "document_id": result.document_id,
        "chunk_count": len(result.chunk_ids),
        "success": result.success
    }


@app.post("/query", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest):
    """Query the knowledge base."""
    result = kb.query(
        query=request.query,
        metadata_filter=request.metadata_filter
    )
    
    sources = []
    for chunk in result.chunks:
        sources.append({
            "text": chunk.text,
            "metadata": chunk.metadata
        })
    
    return {
        "query": result.query,
        "answer": result.answer,
        "sources": sources
    }


@app.delete("/documents")
async def clear_knowledge_base():
    """Clear the knowledge base."""
    kb.clear()
    return {"message": "Knowledge base cleared"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


def main():
    """Run the standalone API server."""
    print("Starting standalone API server...")
    print("API documentation will be available at http://localhost:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    main()