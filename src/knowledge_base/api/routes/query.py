"""
Query routes for the knowledge base API.

This module provides routes for querying the knowledge base.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.knowledge_base.core.config import Config
from src.knowledge_base.agents.orchestrator import OrchestratorAgent

from ..server import get_config, get_orchestrator

router = APIRouter(prefix="/query", tags=["Query"])


class QueryModel(BaseModel):
    """API model for a query."""
    query: str = Field(..., description="Query text")
    filter: Optional[Dict[str, Any]] = Field(None, description="Filter criteria")
    top_k: Optional[int] = Field(None, description="Number of results to return")
    stream: Optional[bool] = Field(None, description="Whether to stream the response")


class ChunkModel(BaseModel):
    """API model for a chunk."""
    id: str = Field(..., description="Chunk ID")
    text: str = Field(..., description="Chunk text")
    document_id: str = Field(..., description="Document ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")
    score: Optional[float] = Field(None, description="Relevance score")


class QueryResponseModel(BaseModel):
    """API model for a query response."""
    query: str = Field(..., description="Original query")
    answer: str = Field(..., description="Generated answer")
    chunks: List[ChunkModel] = Field(..., description="Retrieved chunks")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")


@router.post("", response_model=QueryResponseModel)
async def query_knowledge_base(
    query_request: QueryModel,
    orchestrator: OrchestratorAgent = Depends(get_orchestrator)
):
    """Query the knowledge base.
    
    Args:
        query_request: The query request.
        orchestrator: The orchestrator agent.
        
    Returns:
        The query response.
    """
    # Check if streaming is requested
    if query_request.stream:
        return await stream_query_response(query_request, orchestrator)
    
    # Regular synchronous query
    response = await orchestrator.receive_request(
        source="api",
        request_type="query",
        payload={
            "query": query_request.query,
            "filter": query_request.filter,
            "top_k": query_request.top_k,
            "stream": False
        }
    )
    
    if response.get("status") == "error":
        raise HTTPException(status_code=500, detail=response.get("error", "Unknown error"))
    
    return response


async def stream_query_response(
    query_request: QueryModel,
    orchestrator: OrchestratorAgent
):
    """Stream a query response.
    
    Args:
        query_request: The query request.
        orchestrator: The orchestrator agent.
        
    Returns:
        A streaming response.
    """
    async def generate_stream():
        """Generate the streaming response."""
        async for chunk in orchestrator.receive_request_stream(
            source="api",
            request_type="query",
            payload={
                "query": query_request.query,
                "filter": query_request.filter,
                "top_k": query_request.top_k,
                "stream": True
            }
        ):
            yield f"data: {chunk}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream"
    )


@router.post("/batch", tags=["Query"])
async def batch_query(
    queries: List[QueryModel],
    background_tasks: BackgroundTasks,
    orchestrator: OrchestratorAgent = Depends(get_orchestrator)
):
    """Perform a batch query.
    
    Args:
        queries: The list of queries.
        background_tasks: FastAPI background tasks.
        orchestrator: The orchestrator agent.
        
    Returns:
        The batch query ID.
    """
    # Start batch query in background
    batch_id = await orchestrator.receive_request(
        source="api",
        request_type="batch_query",
        payload={
            "queries": [
                {
                    "query": q.query,
                    "filter": q.filter,
                    "top_k": q.top_k
                }
                for q in queries
            ]
        }
    )
    
    if isinstance(batch_id, dict) and batch_id.get("status") == "error":
        raise HTTPException(status_code=500, detail=batch_id.get("error", "Unknown error"))
    
    return {"batch_id": batch_id}


@router.get("/batch/{batch_id}")
async def get_batch_results(
    batch_id: str,
    orchestrator: OrchestratorAgent = Depends(get_orchestrator)
):
    """Get batch query results.
    
    Args:
        batch_id: The batch query ID.
        orchestrator: The orchestrator agent.
        
    Returns:
        The batch query results.
    """
    response = await orchestrator.receive_request(
        source="api",
        request_type="get_batch_results",
        payload={"batch_id": batch_id}
    )
    
    if response.get("status") == "error":
        if "not found" in response.get("error", "").lower():
            raise HTTPException(status_code=404, detail=f"Batch query {batch_id} not found")
        raise HTTPException(status_code=500, detail=response.get("error", "Unknown error"))
    
    return response


class SimilaritySearchRequest(BaseModel):
    """API model for a similarity search request."""
    text: str = Field(..., description="Text to find similar chunks for")
    filter: Optional[Dict[str, Any]] = Field(None, description="Filter criteria")
    top_k: Optional[int] = Field(None, description="Number of results to return")


@router.post("/similarity", response_model=List[ChunkModel])
async def similarity_search(
    request: SimilaritySearchRequest,
    orchestrator: OrchestratorAgent = Depends(get_orchestrator)
):
    """Find chunks similar to the provided text.
    
    Args:
        request: The similarity search request.
        orchestrator: The orchestrator agent.
        
    Returns:
        The list of similar chunks.
    """
    response = await orchestrator.receive_request(
        source="api",
        request_type="similarity_search",
        payload={
            "text": request.text,
            "filter": request.filter,
            "top_k": request.top_k
        }
    )
    
    if response.get("status") == "error":
        raise HTTPException(status_code=500, detail=response.get("error", "Unknown error"))
    
    return response.get("chunks", [])


class FilteredQueryRequest(BaseModel):
    """API model for a filtered query request."""
    query: str = Field(..., description="Query text")
    metadata_filters: Dict[str, Any] = Field(..., description="Metadata filters")
    content_filters: Optional[List[str]] = Field(None, description="Content filters (keywords)")
    date_range: Optional[Dict[str, str]] = Field(None, description="Date range filter")
    top_k: Optional[int] = Field(None, description="Number of results to return")


@router.post("/filtered", response_model=QueryResponseModel)
async def filtered_query(
    request: FilteredQueryRequest,
    orchestrator: OrchestratorAgent = Depends(get_orchestrator)
):
    """Query the knowledge base with advanced filtering.
    
    Args:
        request: The filtered query request.
        orchestrator: The orchestrator agent.
        
    Returns:
        The query response.
    """
    # Combine all filters into a single filter object
    combined_filter = {
        "metadata": request.metadata_filters
    }
    
    if request.content_filters:
        combined_filter["content"] = request.content_filters
    
    if request.date_range:
        combined_filter["date_range"] = request.date_range
    
    response = await orchestrator.receive_request(
        source="api",
        request_type="query",
        payload={
            "query": request.query,
            "filter": combined_filter,
            "top_k": request.top_k,
            "stream": False
        }
    )
    
    if response.get("status") == "error":
        raise HTTPException(status_code=500, detail=response.get("error", "Unknown error"))
    
    return response


@router.get("/suggest")
async def suggest_queries(
    prefix: str = Query(..., description="Query prefix to get suggestions for"),
    limit: int = Query(5, ge=1, le=20, description="Maximum number of suggestions"),
    orchestrator: OrchestratorAgent = Depends(get_orchestrator)
):
    """Get query suggestions based on a prefix.
    
    Args:
        prefix: The query prefix.
        limit: Maximum number of suggestions to return.
        orchestrator: The orchestrator agent.
        
    Returns:
        The list of query suggestions.
    """
    response = await orchestrator.receive_request(
        source="api",
        request_type="suggest_queries",
        payload={
            "prefix": prefix,
            "limit": limit
        }
    )
    
    if response.get("status") == "error":
        raise HTTPException(status_code=500, detail=response.get("error", "Unknown error"))
    
    return response.get("suggestions", [])