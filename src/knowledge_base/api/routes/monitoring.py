"""
Monitoring routes for the knowledge base API.

This module provides routes for monitoring the system health and performance.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel

from src.knowledge_base.core.config import Config
from src.knowledge_base.core.monitoring import get_monitoring_system, MonitoringSystem
from src.knowledge_base.agents.orchestrator import OrchestratorAgent

from ..server import get_config, get_orchestrator

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.get("/health")
async def health_check(
    config: Config = Depends(get_config),
    monitoring: MonitoringSystem = Depends(get_monitoring_system)
):
    """Basic health check endpoint.
    
    Returns:
        The basic health status.
    """
    health_status = monitoring.run_health_check("system")
    
    # Set appropriate status code based on health status
    if health_status["status"] == "error":
        return Response(
            status_code=500,
            content={"status": "error", "message": health_status["message"]}
        )
    elif health_status["status"] == "warning":
        return Response(
            status_code=200,
            content={"status": "warning", "message": health_status["message"]}
        )
    else:
        return {"status": "ok", "version": "1.0.0"}


@router.get("/health/detailed")
async def detailed_health_check(
    config: Config = Depends(get_config),
    monitoring: MonitoringSystem = Depends(get_monitoring_system)
):
    """Detailed health check endpoint.
    
    Returns:
        Detailed health status for all components.
    """
    health_status = monitoring.run_all_health_checks()
    
    # Set appropriate status code based on overall health status
    if health_status["overall"]["status"] == "error":
        return Response(
            status_code=500,
            content=health_status
        )
    else:
        return health_status


@router.get("/metrics")
async def get_metrics(
    component: Optional[str] = Query(None, description="Filter metrics by component"),
    config: Config = Depends(get_config),
    monitoring: MonitoringSystem = Depends(get_monitoring_system)
):
    """Get system metrics.
    
    Args:
        component: Filter metrics by component (e.g., system, api, storage).
        
    Returns:
        The system metrics.
    """
    metrics = monitoring.get_metrics()
    
    # Filter metrics by component if specified
    if component:
        filtered_metrics = {}
        for name, metric in metrics.items():
            if name.startswith(f"{component}."):
                filtered_metrics[name] = metric
        return filtered_metrics
    
    return metrics


@router.get("/metrics/prometheus")
async def prometheus_metrics(
    config: Config = Depends(get_config),
    monitoring: MonitoringSystem = Depends(get_monitoring_system)
):
    """Get metrics in Prometheus format.
    
    Returns:
        Metrics in Prometheus format.
    """
    if not config.monitoring.prometheus_enabled:
        raise HTTPException(status_code=404, detail="Prometheus metrics are not enabled")
    
    metrics = monitoring.get_metrics()
    prometheus_output = []
    
    for name, metric in metrics.items():
        # Add metric help and type
        prometheus_output.append(f"# HELP {name} {metric['description']}")
        prometheus_output.append(f"# TYPE {name} {metric['type']}")
        
        # Add metric value
        if metric["type"] in ["counter", "gauge"]:
            prometheus_output.append(f"{name} {metric['value']}")
        elif metric["type"] in ["histogram", "summary"] and metric.get("count", 0) > 0:
            prometheus_output.append(f"{name}_count {metric['count']}")
            prometheus_output.append(f"{name}_sum {metric['sum']}")
            prometheus_output.append(f"{name}_min {metric['min']}")
            prometheus_output.append(f"{name}_max {metric['max']}")
            prometheus_output.append(f"{name}_avg {metric['mean']}")
            prometheus_output.append(f"{name}_p95 {metric['p95']}")
            prometheus_output.append(f"{name}_p99 {metric['p99']}")
    
    return Response(content="\n".join(prometheus_output), media_type="text/plain")


@router.get("/alerts")
async def get_alerts(
    config: Config = Depends(get_config),
    monitoring: MonitoringSystem = Depends(get_monitoring_system)
):
    """Get triggered alerts.
    
    Returns:
        The triggered alerts.
    """
    return {"alerts": monitoring.get_alerts()}


@router.get("/logs")
async def get_logs(
    level: str = Query("info", description="Minimum log level"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of log entries"),
    start_time: Optional[str] = Query(None, description="Start time for logs (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time for logs (ISO format)"),
    source: Optional[str] = Query(None, description="Log source filter"),
    orchestrator: OrchestratorAgent = Depends(get_orchestrator)
):
    """Get system logs.
    
    Args:
        level: Minimum log level.
        limit: Maximum number of log entries.
        start_time: Start time for logs (ISO format).
        end_time: End time for logs (ISO format).
        source: Log source filter.
        
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
            "end_time": end_time,
            "source": source
        }
    )
    
    if response.get("status") == "error":
        raise HTTPException(status_code=500, detail=response.get("error", "Unknown error"))
    
    return response