"""
Monitoring configuration for the unified knowledge base system.

This module extends the core configuration with monitoring settings.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union, Set

@dataclass
class MonitoringConfig:
    """Monitoring configuration."""
    enabled: bool = True
    interval: int = 60  # seconds
    
    # Health check thresholds
    cpu_threshold: float = 80.0  # percentage
    memory_threshold: float = 80.0  # percentage
    disk_threshold: float = 80.0  # percentage
    error_threshold: float = 5.0  # percentage
    response_time_threshold: float = 1.0  # seconds
    
    # Logging configuration
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: Optional[str] = None
    log_max_size: int = 10485760  # 10 MB
    log_backup_count: int = 5
    log_to_console: bool = True
    log_to_file: bool = False
    
    # Metrics configuration
    metrics_enabled: bool = True
    metrics_retention_days: int = 7
    
    # Alerting configuration
    alerts_enabled: bool = True
    alert_interval: int = 3600  # seconds
    
    # Notification configuration
    notifications_enabled: bool = False
    email_notifications_enabled: bool = False
    webhook_notifications_enabled: bool = False
    email_recipients: List[str] = field(default_factory=list)
    webhook_url: Optional[str] = None
    
    # Prometheus integration
    prometheus_enabled: bool = False
    prometheus_port: int = 9090
    
    # Healthcheck endpoints
    healthcheck_enabled: bool = True
    healthcheck_path: str = "/health"
    detailed_healthcheck_path: str = "/health/detailed"