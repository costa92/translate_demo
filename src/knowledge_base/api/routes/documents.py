"""
Document management routes for the knowledge base API.

This module provides routes for managing documents in the knowledge base.
It serves as a compatibility layer for clients expecting /api/documents endpoints.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from src.knowledge_base.agents.orchestrator import OrchestratorAgent
from src.knowledge_base.api.routes.knowledge import (
    DocumentModel,
    AddDocumentResponse,
    BulkDocumentRequest,
    BulkDocumentResponse
)
from ..dependencies import get_orchestrator

router = APIRouter(prefix="/api", tags=["Document Management"])


@router.post("/documents", response_model=AddDocumentResponse)
async def add_document(
    document: DocumentModel,
    orchestrator: OrchestratorAgent = Depends(get_orchestrator)
):
    """Add a document to the knowledge base.
    
    Args:
        document: The document to add.
        orchestrator: The orchestrator agent.
        
    Returns:
        The result of adding the document.
    """
    response = await orchestrator.receive_request(
        source="api",
        request_type="add_document",
        payload={
            "document": {
                "id": document.id,
                "content": document.content,
                "type": document.type,
                "metadata": document.metadata
            }
        }
    )
    
    if response.get("status") == "error":
        raise HTTPException(status_code=500, detail=response.get("error", "Unknown error"))
    
    return response


@router.get("/documents/{document_id}")
async def get_document(
    document_id: str,
    orchestrator: OrchestratorAgent = Depends(get_orchestrator)
):
    """Get a document from the knowledge base.
    
    Args:
        document_id: The document ID.
        orchestrator: The orchestrator agent.
        
    Returns:
        The document.
    """
    response = await orchestrator.receive_request(
        source="api",
        request_type="get_document",
        payload={"document_id": document_id}
    )
    
    if response.get("status") == "error":
        if "not found" in response.get("error", "").lower():
            raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
        raise HTTPException(status_code=500, detail=response.get("error", "Unknown error"))
    
    return response


@router.put("/documents/{document_id}")
async def update_document(
    document_id: str,
    document: DocumentModel,
    orchestrator: OrchestratorAgent = Depends(get_orchestrator)
):
    """Update a document in the knowledge base.
    
    Args:
        document_id: The document ID.
        document: The updated document.
        orchestrator: The orchestrator agent.
        
    Returns:
        The result of updating the document.
    """
    # Override the document ID in the payload with the path parameter
    document_data = document.dict()
    document_data["id"] = document_id
    
    response = await orchestrator.receive_request(
        source="api",
        request_type="update_document",
        payload={
            "document": document_data
        }
    )
    
    if response.get("status") == "error":
        if "not found" in response.get("error", "").lower():
            raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
        raise HTTPException(status_code=500, detail=response.get("error", "Unknown error"))
    
    return response


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    orchestrator: OrchestratorAgent = Depends(get_orchestrator)
):
    """Delete a document from the knowledge base.
    
    Args:
        document_id: The document ID.
        orchestrator: The orchestrator agent.
        
    Returns:
        The result of deleting the document.
    """
    response = await orchestrator.receive_request(
        source="api",
        request_type="delete_document",
        payload={"document_id": document_id}
    )
    
    if response.get("status") == "error":
        if "not found" in response.get("error", "").lower():
            raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
        raise HTTPException(status_code=500, detail=response.get("error", "Unknown error"))
    
    return response


@router.get("/documents")
async def list_documents(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    filter: Optional[str] = None,
    orchestrator: OrchestratorAgent = Depends(get_orchestrator)
):
    """List documents in the knowledge base.
    
    Args:
        limit: Maximum number of documents to return.
        offset: Number of documents to skip.
        filter: Filter expression.
        orchestrator: The orchestrator agent.
        
    Returns:
        The list of documents.
    """
    response = await orchestrator.receive_request(
        source="api",
        request_type="list_documents",
        payload={
            "limit": limit,
            "offset": offset,
            "filter": filter
        }
    )
    
    if response.get("status") == "error":
        raise HTTPException(status_code=500, detail=response.get("error", "Unknown error"))
    
    return response


@router.post("/documents/batch", response_model=BulkDocumentResponse)
async def bulk_add_documents(
    request: BulkDocumentRequest,
    orchestrator: OrchestratorAgent = Depends(get_orchestrator)
):
    """Add multiple documents to the knowledge base in a single request.
    
    Args:
        request: The bulk document request.
        orchestrator: The orchestrator agent.
        
    Returns:
        The result of adding the documents.
    """
    response = await orchestrator.receive_request(
        source="api",
        request_type="bulk_add_documents",
        payload={
            "documents": [doc.dict() for doc in request.documents]
        }
    )
    
    if response.get("status") == "error":
        raise HTTPException(status_code=500, detail=response.get("error", "Unknown error"))
    
    return response


@router.post("/documents/batch/delete")
async def bulk_delete_documents(
    document_ids: List[str],
    orchestrator: OrchestratorAgent = Depends(get_orchestrator)
):
    """Delete multiple documents from the knowledge base in a single request.
    
    Args:
        document_ids: The list of document IDs to delete.
        orchestrator: The orchestrator agent.
        
    Returns:
        The result of deleting the documents.
    """
    response = await orchestrator.receive_request(
        source="api",
        request_type="bulk_delete_documents",
        payload={
            "document_ids": document_ids
        }
    )
    
    if response.get("status") == "error":
        raise HTTPException(status_code=500, detail=response.get("error", "Unknown error"))
    
    return response