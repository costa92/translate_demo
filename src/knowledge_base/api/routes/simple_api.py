"""
Simplified API routes for the knowledge base.

This module provides simplified API routes that directly use SimpleKnowledgeBase.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from pydantic import BaseModel, Field

from src.knowledge_base.core.config import Config
from src.knowledge_base.simple_kb import SimpleKnowledgeBase, Document, TextChunk, AddResult, QueryResult

# Import dependencies
from ..dependencies import get_config

# Create a global SimpleKnowledgeBase instance
_kb = None

def get_kb(config: Config = Depends(get_config)) -> SimpleKnowledgeBase:
    """Get the SimpleKnowledgeBase instance."""
    global _kb
    if _kb is None:
        # Import the global instance from run.py
        import sys
        main_module = sys.modules.get('__main__')
        if hasattr(main_module, 'kb'):
            _kb = main_module.kb
            print(f"Using global KB instance from main module with {len(_kb.documents)} documents")
        else:
            _kb = SimpleKnowledgeBase(config)
            print(f"Created new KB instance")
    return _kb

router = APIRouter(tags=["Simple API"])


class DocumentModel(BaseModel):
    """API model for a document."""
    id: Optional[str] = Field(None, description="Document ID (auto-generated if not provided)")
    content: str = Field(..., description="Document content")
    type: str = Field("text", description="Document type")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")


class AddDocumentResponse(BaseModel):
    """API model for add document response."""
    document_id: str = Field(..., description="Document ID")
    chunk_ids: List[str] = Field(..., description="Chunk IDs")
    success: bool = Field(..., description="Success status")
    error: Optional[str] = Field(None, description="Error message if any")


class QueryRequest(BaseModel):
    """API model for a query request."""
    query: str = Field(..., description="Query text")
    metadata_filter: Optional[Dict[str, Any]] = Field(None, description="Metadata filter")


class QueryResponse(BaseModel):
    """API model for a query response."""
    query: str = Field(..., description="Original query")
    answer: str = Field(..., description="Generated answer")
    chunks: List[Dict[str, Any]] = Field(..., description="Retrieved chunks")


@router.post("/add_document", response_model=AddDocumentResponse)
async def add_document(
    document: DocumentModel,
    kb: SimpleKnowledgeBase = Depends(get_kb)
):
    """Add a document to the knowledge base."""
    try:
        # 打印调试信息
        import logging
        logging.info(f"Adding document: {document.content[:50]}...")
        logging.info(f"Metadata: {document.metadata}")
        
        result = kb.add_document(
            content=document.content,
            metadata=document.metadata
        )
        
        # 打印知识库状态
        logging.info(f"Knowledge base now has {len(kb.documents)} documents and {len(kb.chunks)} chunks")
        
        return {
            "document_id": result.document_id,
            "chunk_ids": result.chunk_ids,
            "success": True,
            "error": None
        }
    except Exception as e:
        import logging
        logging.error(f"Error adding document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    kb: SimpleKnowledgeBase = Depends(get_kb)
):
    """Query the knowledge base."""
    try:
        # 打印调试信息
        import logging
        logging.info(f"Querying: {request.query}")
        logging.info(f"Knowledge base has {len(kb.documents)} documents and {len(kb.chunks)} chunks")
        
        result = kb.query(
            query=request.query,
            metadata_filter=request.metadata_filter
        )
        
        # Convert chunks to dictionaries
        chunks = []
        for chunk in result.chunks:
            chunks.append({
                "id": chunk.id,
                "text": chunk.text,
                "document_id": chunk.document_id,
                "metadata": chunk.metadata
            })
        
        logging.info(f"Query returned {len(chunks)} chunks")
        
        return {
            "query": result.query,
            "answer": result.answer,
            "chunks": chunks
        }
    except Exception as e:
        import logging
        logging.error(f"Error querying: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))