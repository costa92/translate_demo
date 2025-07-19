"""
Admin routes for the knowledge base API.

This module provides routes for administrative tasks.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

from src.knowledge_base.core.config import Config
from src.knowledge_base.agents.orchestrator import OrchestratorAgent

from ..dependencies import get_config, get_orchestrator

router = APIRouter(prefix="/admin", tags=["Administration"])


@router.get("/health")
async def health_check(
    config: Config = Depends(get_config),
    orchestrator: OrchestratorAgent = Depends(get_orchestrator)
):
    """Health check endpoint.
    
    Args:
        config: The configuration instance.
        orchestrator: The orchestrator agent.
        
    Returns:
        The health status.
    """
    # Check if orchestrator is running
    orchestrator_status = "ok" if orchestrator.is_running else "not_running"
    
    # Check if specialized agents are running
    agent_status = {}
    for agent_type, agent in orchestrator.agents.items():
        agent_status[agent_type] = "ok" if agent.is_running else "not_running"
    
    return {
        "status": "ok",
        "orchestrator": orchestrator_status,
        "agents": agent_status,
        "version": "1.0.0"
    }


@router.get("/status")
async def system_status(
    orchestrator: OrchestratorAgent = Depends(get_orchestrator)
):
    """Get system status.
    
    Args:
        orchestrator: The orchestrator agent.
        
    Returns:
        The system status.
    """
    response = await orchestrator.receive_request(
        source="api",
        request_type="system_status",
        payload={}
    )
    
    if response.get("status") == "error":
        raise HTTPException(status_code=500, detail=response.get("error", "Unknown error"))
    
    return response


@router.post("/maintenance")
async def run_maintenance(
    maintenance_type: str = Query("full", description="Type of maintenance to run"),
    background_tasks: BackgroundTasks = None,
    orchestrator: OrchestratorAgent = Depends(get_orchestrator)
):
    """Run maintenance tasks.
    
    Args:
        maintenance_type: The type of maintenance to run.
        background_tasks: FastAPI background tasks.
        orchestrator: The orchestrator agent.
        
    Returns:
        The maintenance task ID.
    """
    # Start maintenance in background
    task_id = await orchestrator.receive_request(
        source="api",
        request_type="maintenance",
        payload={
            "maintenance_task": maintenance_type,
            "params": {}
        }
    )
    
    if isinstance(task_id, dict) and task_id.get("status") == "error":
        raise HTTPException(status_code=500, detail=task_id.get("error", "Unknown error"))
    
    return {"task_id": task_id}


@router.get("/maintenance/{task_id}")
async def get_maintenance_status(
    task_id: str,
    orchestrator: OrchestratorAgent = Depends(get_orchestrator)
):
    """Get maintenance task status.
    
    Args:
        task_id: The maintenance task ID.
        orchestrator: The orchestrator agent.
        
    Returns:
        The maintenance task status.
    """
    response = await orchestrator.receive_request(
        source="api",
        request_type="maintenance_status",
        payload={"task_id": task_id}
    )
    
    if response.get("status") == "error":
        if "not found" in response.get("error", "").lower():
            raise HTTPException(status_code=404, detail=f"Maintenance task {task_id} not found")
        raise HTTPException(status_code=500, detail=response.get("error", "Unknown error"))
    
    return response


@router.get("/config")
async def get_configuration(
    config: Config = Depends(get_config)
):
    """Get system configuration.
    
    Args:
        config: The configuration instance.
        
    Returns:
        The system configuration.
    """
    # Return a sanitized version of the configuration (without sensitive information)
    sanitized_config = {
        "system": {
            "debug": config.system.debug,
            "log_level": config.system.log_level,
            "cache_enabled": config.system.cache_enabled,
            "cache_ttl": config.system.cache_ttl,
            "max_workers": config.system.max_workers
        },
        "storage": {
            "provider": config.storage.provider,
            "collection_name": config.storage.collection_name,
            "batch_size": config.storage.batch_size,
            "max_connections": config.storage.max_connections,
            "connection_timeout": config.storage.connection_timeout,
            "retry_attempts": config.storage.retry_attempts,
            "retry_delay": config.storage.retry_delay
        },
        "embedding": {
            "provider": config.embedding.provider,
            "model": config.embedding.model,
            "dimensions": config.embedding.dimensions,
            "max_length": config.embedding.max_length,
            "batch_size": config.embedding.batch_size,
            "device": config.embedding.device,
            "cache_enabled": config.embedding.cache_enabled,
            "cache_size": config.embedding.cache_size,
            "timeout": config.embedding.timeout,
            "retry_attempts": config.embedding.retry_attempts,
            "retry_delay": config.embedding.retry_delay
        },
        "chunking": {
            "strategy": config.chunking.strategy,
            "chunk_size": config.chunking.chunk_size,
            "chunk_overlap": config.chunking.chunk_overlap,
            "language": config.chunking.language,
            "respect_sentence_boundary": config.chunking.respect_sentence_boundary,
            "min_chunk_size": config.chunking.min_chunk_size,
            "max_chunk_size": config.chunking.max_chunk_size,
            "chunk_by_tokens": config.chunking.chunk_by_tokens,
            "extract_metadata": config.chunking.extract_metadata,
            "generate_automatic_metadata": config.chunking.generate_automatic_metadata,
            "index_metadata": config.chunking.index_metadata
        },
        "retrieval": {
            "strategy": config.retrieval.strategy,
            "top_k": config.retrieval.top_k,
            "min_score": config.retrieval.min_score,
            "semantic_weight": config.retrieval.semantic_weight,
            "keyword_weight": config.retrieval.keyword_weight,
            "enable_reranking": config.retrieval.enable_reranking,
            "rerank_top_k": config.retrieval.rerank_top_k,
            "max_context_length": config.retrieval.max_context_length,
            "context_window": config.retrieval.context_window,
            "cache_enabled": config.retrieval.cache_enabled,
            "cache_ttl": config.retrieval.cache_ttl,
            "cache_size": config.retrieval.cache_size
        },
        "generation": {
            "provider": config.generation.provider,
            "model": config.generation.model,
            "temperature": config.generation.temperature,
            "max_tokens": config.generation.max_tokens,
            "top_p": config.generation.top_p,
            "frequency_penalty": config.generation.frequency_penalty,
            "include_sources": config.generation.include_sources,
            "language": config.generation.language,
            "template_id": config.generation.template_id,
            "stream": config.generation.stream,
            "filter_content": config.generation.filter_content,
            "validate_answers": config.generation.validate_answers,
            "filter_level": config.generation.filter_level,
            "quality_assessor": config.generation.quality_assessor,
            "quality_threshold": config.generation.quality_threshold,
            "improve_answers": config.generation.improve_answers
        },
        "agents": {
            "orchestrator_enabled": config.agents.orchestrator_enabled,
            "data_collection_enabled": config.agents.data_collection_enabled,
            "knowledge_processing_enabled": config.agents.knowledge_processing_enabled,
            "knowledge_storage_enabled": config.agents.knowledge_storage_enabled,
            "knowledge_retrieval_enabled": config.agents.knowledge_retrieval_enabled,
            "knowledge_maintenance_enabled": config.agents.knowledge_maintenance_enabled,
            "rag_enabled": config.agents.rag_enabled,
            "message_queue_size": config.agents.message_queue_size,
            "message_timeout": config.agents.message_timeout,
            "max_retries": config.agents.max_retries,
            "retry_delay": config.agents.retry_delay,
            "maintenance_interval": config.agents.maintenance_interval,
            "maintenance_time": config.agents.maintenance_time,
            "specialized_agents": config.agents.specialized_agents
        },
        "api": {
            "host": config.api.host,
            "port": config.api.port,
            "debug": config.api.debug,
            "cors_origins": config.api.cors_origins,
            "cors_allow_credentials": config.api.cors_allow_credentials,
            "cors_allow_methods": config.api.cors_allow_methods,
            "cors_allow_headers": config.api.cors_allow_headers,
            "auth_enabled": config.api.auth_enabled,
            "auth_provider": config.api.auth_provider,
            "rate_limit_enabled": config.api.rate_limit_enabled,
            "rate_limit_requests": config.api.rate_limit_requests,
            "rate_limit_period": config.api.rate_limit_period,
            "docs_enabled": config.api.docs_enabled,
            "docs_url": config.api.docs_url,
            "redoc_url": config.api.redoc_url
        }
    }
    
    return sanitized_config
class ConfigUpdateRequest(BaseModel):
    """API model for configuration update request."""
    section: str = Field(..., description="Configuration section to update")
    key: str = Field(..., description="Configuration key to update")
    value: Any = Field(..., description="New value for the configuration key")


@router.patch("/config")
async def update_configuration(
    request: ConfigUpdateRequest,
    config: Config = Depends(get_config),
    orchestrator: OrchestratorAgent = Depends(get_orchestrator)
):
    """Update system configuration.
    
    Args:
        request: The configuration update request.
        config: The configuration instance.
        orchestrator: The orchestrator agent.
        
    Returns:
        The updated configuration.
    """
    # Validate section and key
    if not hasattr(config, request.section):
        raise HTTPException(status_code=400, detail=f"Invalid configuration section: {request.section}")
    
    section = getattr(config, request.section)
    if not hasattr(section, request.key):
        raise HTTPException(status_code=400, detail=f"Invalid configuration key: {request.key}")
    
    # Update configuration
    try:
        setattr(section, request.key, request.value)
        
        # Notify orchestrator of configuration change
        await orchestrator.receive_request(
            source="api",
            request_type="config_updated",
            payload={
                "section": request.section,
                "key": request.key,
                "value": request.value
            }
        )
        
        return {
            "status": "success",
            "message": f"Updated {request.section}.{request.key} to {request.value}",
            "updated_config": {
                request.section: {
                    request.key: request.value
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")


@router.get("/metrics")
async def get_system_metrics(
    orchestrator: OrchestratorAgent = Depends(get_orchestrator)
):
    """Get system performance metrics.
    
    Args:
        orchestrator: The orchestrator agent.
        
    Returns:
        The system metrics.
    """
    response = await orchestrator.receive_request(
        source="api",
        request_type="get_metrics",
        payload={}
    )
    
    if response.get("status") == "error":
        raise HTTPException(status_code=500, detail=response.get("error", "Unknown error"))
    
    return response


@router.get("/logs")
async def get_system_logs(
    level: str = Query("info", description="Minimum log level"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of log entries"),
    start_time: Optional[str] = Query(None, description="Start time for logs (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time for logs (ISO format)"),
    orchestrator: OrchestratorAgent = Depends(get_orchestrator)
):
    """Get system logs.
    
    Args:
        level: Minimum log level.
        limit: Maximum number of log entries.
        start_time: Start time for logs (ISO format).
        end_time: End time for logs (ISO format).
        orchestrator: The orchestrator agent.
        
    Returns:
        The system logs.
    """
    response = await orchestrator.receive_request(
        source="api",
        request_type="get_logs",
        payload={
            "level": level,
            "limit": limit,
            "start_time": start_time,
            "end_time": end_time
        }
    )
    
    if response.get("status") == "error":
        raise HTTPException(status_code=500, detail=response.get("error", "Unknown error"))
    
    return response


@router.post("/backup")
async def create_backup(
    orchestrator: OrchestratorAgent = Depends(get_orchestrator)
):
    """Create a system backup.
    
    Args:
        orchestrator: The orchestrator agent.
        
    Returns:
        The backup information.
    """
    response = await orchestrator.receive_request(
        source="api",
        request_type="create_backup",
        payload={}
    )
    
    if response.get("status") == "error":
        raise HTTPException(status_code=500, detail=response.get("error", "Unknown error"))
    
    return response


@router.post("/restore")
async def restore_backup(
    backup_id: str = Query(..., description="Backup ID to restore"),
    orchestrator: OrchestratorAgent = Depends(get_orchestrator)
):
    """Restore from a backup.
    
    Args:
        backup_id: The backup ID to restore.
        orchestrator: The orchestrator agent.
        
    Returns:
        The restore operation result.
    """
    response = await orchestrator.receive_request(
        source="api",
        request_type="restore_backup",
        payload={
            "backup_id": backup_id
        }
    )
    
    if response.get("status") == "error":
        raise HTTPException(status_code=500, detail=response.get("error", "Unknown error"))
    
    return response


@router.get("/backups")
async def list_backups(
    orchestrator: OrchestratorAgent = Depends(get_orchestrator)
):
    """List available backups.
    
    Args:
        orchestrator: The orchestrator agent.
        
    Returns:
        The list of available backups.
    """
    response = await orchestrator.receive_request(
        source="api",
        request_type="list_backups",
        payload={}
    )
    
    if response.get("status") == "error":
        raise HTTPException(status_code=500, detail=response.get("error", "Unknown error"))
    
    return response


@router.post("/restart")
async def restart_system(
    component: str = Query("all", description="Component to restart (all, orchestrator, or agent name)"),
    orchestrator: OrchestratorAgent = Depends(get_orchestrator)
):
    """Restart system components.
    
    Args:
        component: The component to restart.
        orchestrator: The orchestrator agent.
        
    Returns:
        The restart operation result.
    """
    response = await orchestrator.receive_request(
        source="api",
        request_type="restart",
        payload={
            "component": component
        }
    )
    
    if response.get("status") == "error":
        raise HTTPException(status_code=500, detail=response.get("error", "Unknown error"))
    
    return response