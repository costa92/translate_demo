"""
Knowledge management routes for the knowledge base API.

This module provides routes for managing knowledge in the knowledge base.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from pydantic import BaseModel, Field

from src.knowledge_base.core.config import Config
from src.knowledge_base.agents.orchestrator import OrchestratorAgent
from src.knowledge_base.core.types import DocumentType

# Import dependencies from server module at runtime to avoid circular imports
from fastapi import Depends

# Define dependency functions that will be imported from server at runtime
def get_config():
    from ..server import get_config as server_get_config
    return server_get_config()

def get_orchestrator():
    from ..server import get_orchestrator as server_get_orchestrator
    return server_get_orchestrator()

router = APIRouter(prefix="/knowledge", tags=["Knowledge Management"])


class DocumentModel(BaseModel):
    """API model for a document."""
    id: Optional[str] = Field(None, description="Document ID (auto-generated if not provided)")
    content: str = Field(..., description="Document content")
    type: str = Field(DocumentType.TEXT.value, description="Document type")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")


class AddDocumentResponse(BaseModel):
    """API model for add document response."""
    document_id: str = Field(..., description="Document ID")
    chunk_ids: List[str] = Field(..., description="Chunk IDs")
    success: bool = Field(..., description="Success status")
    error: Optional[str] = Field(None, description="Error message if any")


class BulkDocumentRequest(BaseModel):
    """API model for bulk document operations."""
    documents: List[DocumentModel] = Field(..., description="List of documents")


class BulkDocumentResponse(BaseModel):
    """API model for bulk document operation response."""
    results: List[Dict[str, Any]] = Field(..., description="Operation results")
    success_count: int = Field(..., description="Number of successful operations")
    error_count: int = Field(..., description="Number of failed operations")


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


@router.patch("/documents/{document_id}")
async def patch_document(
    document_id: str,
    patch_data: Dict[str, Any],
    orchestrator: OrchestratorAgent = Depends(get_orchestrator)
):
    """Partially update a document in the knowledge base.
    
    Args:
        document_id: The document ID.
        patch_data: The partial update data.
        orchestrator: The orchestrator agent.
        
    Returns:
        The result of patching the document.
    """
    # Add the document ID to the patch data
    patch_data["id"] = document_id
    
    response = await orchestrator.receive_request(
        source="api",
        request_type="patch_document",
        payload={
            "document_id": document_id,
            "patch_data": patch_data
        }
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


@router.post("/documents/bulk", response_model=BulkDocumentResponse)
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


@router.delete("/documents/bulk")
async def bulk_delete_documents(
    document_ids: List[str] = Query(..., description="List of document IDs to delete"),
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