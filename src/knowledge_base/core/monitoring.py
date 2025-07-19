"""
Monitoring system for the unified knowledge base system.

This module provides monitoring capabilities including:
- Health checks
- Performance metrics
- Logging configuration
- Alerting mechanisms
"""

import os
import time
import logging
import json
import psutil
import socket
import threading
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Union, Set
from pathlib import Path
from collections import deque

from .config import Config
from .exceptions import MonitoringError

logger = logging.getLogger(__name__)


class HealthStatus:
    """Health status constants."""
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    UNKNOWN = "unknown"


class MetricType:
    """Metric type constants."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class MonitoringSystem:
    """Monitoring system for the knowledge base."""
    
    def __init__(self, config: Config):
        """Initialize the monitoring system.
        
        Args:
            config: The configuration instance.
        """
        self.config = config
        self.start_time = time.time()
        self.metrics = {}
        self.health_checks = {}
        self.alerts = {}
        self.alert_history = deque(maxlen=100)
        
        # Initialize metrics
        self._init_metrics()
        
        # Initialize health checks
        self._init_health_checks()
        
        # Initialize alerts
        self._init_alerts()
        
        # Start background monitoring if enabled
        if self.config.monitoring.enabled:
            self._start_background_monitoring()
    
    def _init_metrics(self) -> None:
        """Initialize metrics."""
        # System metrics
        self.register_metric("system.cpu_usage", MetricType.GAUGE, "CPU usage percentage")
        self.register_metric("system.memory_usage", MetricType.GAUGE, "Memory usage percentage")
        self.register_metric("system.disk_usage", MetricType.GAUGE, "Disk usage percentage")
        
        # API metrics
        self.register_metric("api.requests_total", MetricType.COUNTER, "Total number of API requests")
        self.register_metric("api.requests_by_endpoint", MetricType.COUNTER, "Number of requests by endpoint")
        self.register_metric("api.errors_total", MetricType.COUNTER, "Total number of API errors")
        self.register_metric("api.response_time", MetricType.HISTOGRAM, "API response time in seconds")
        
        # Storage metrics
        self.register_metric("storage.operations_total", MetricType.COUNTER, "Total number of storage operations")
        self.register_metric("storage.operation_time", MetricType.HISTOGRAM, "Storage operation time in seconds")
        self.register_metric("storage.errors_total", MetricType.COUNTER, "Total number of storage errors")
        
        # Embedding metrics
        self.register_metric("embedding.operations_total", MetricType.COUNTER, "Total number of embedding operations")
        self.register_metric("embedding.operation_time", MetricType.HISTOGRAM, "Embedding operation time in seconds")
        self.register_metric("embedding.errors_total", MetricType.COUNTER, "Total number of embedding errors")
        
        # Retrieval metrics
        self.register_metric("retrieval.queries_total", MetricType.COUNTER, "Total number of retrieval queries")
        self.register_metric("retrieval.query_time", MetricType.HISTOGRAM, "Retrieval query time in seconds")
        self.register_metric("retrieval.errors_total", MetricType.COUNTER, "Total number of retrieval errors")
        
        # Generation metrics
        self.register_metric("generation.requests_total", MetricType.COUNTER, "Total number of generation requests")
        self.register_metric("generation.request_time", MetricType.HISTOGRAM, "Generation request time in seconds")
        self.register_metric("generation.errors_total", MetricType.COUNTER, "Total number of generation errors")
        
        # Agent metrics
        self.register_metric("agents.messages_total", MetricType.COUNTER, "Total number of agent messages")
        self.register_metric("agents.processing_time", MetricType.HISTOGRAM, "Agent message processing time in seconds")
        self.register_metric("agents.errors_total", MetricType.COUNTER, "Total number of agent errors")
    
    def _init_health_checks(self) -> None:
        """Initialize health checks."""
        # System health checks
        self.register_health_check("system", self._check_system_health)
        
        # API health checks
        self.register_health_check("api", self._check_api_health)
        
        # Storage health checks
        self.register_health_check("storage", self._check_storage_health)
        
        # Embedding health checks
        self.register_health_check("embedding", self._check_embedding_health)
        
        # Retrieval health checks
        self.register_health_check("retrieval", self._check_retrieval_health)
        
        # Generation health checks
        self.register_health_check("generation", self._check_generation_health)
        
        # Agent health checks
        self.register_health_check("agents", self._check_agents_health)
    
    def _init_alerts(self) -> None:
        """Initialize alerts."""
        # System alerts
        self.register_alert(
            "high_cpu_usage",
            "System CPU usage is high",
            lambda: self.get_metric_value("system.cpu_usage") > self.config.monitoring.cpu_threshold,
            self.config.monitoring.alert_interval
        )
        
        self.register_alert(
            "high_memory_usage",
            "System memory usage is high",
            lambda: self.get_metric_value("system.memory_usage") > self.config.monitoring.memory_threshold,
            self.config.monitoring.alert_interval
        )
        
        self.register_alert(
            "high_disk_usage",
            "System disk usage is high",
            lambda: self.get_metric_value("system.disk_usage") > self.config.monitoring.disk_threshold,
            self.config.monitoring.alert_interval
        )
        
        # API alerts
        self.register_alert(
            "high_error_rate",
            "API error rate is high",
            lambda: self._calculate_error_rate("api") > self.config.monitoring.error_threshold,
            self.config.monitoring.alert_interval
        )
        
        self.register_alert(
            "slow_response_time",
            "API response time is slow",
            lambda: self._calculate_avg_response_time() > self.config.monitoring.response_time_threshold,
            self.config.monitoring.alert_interval
        )
        
        # Storage alerts
        self.register_alert(
            "storage_errors",
            "Storage errors detected",
            lambda: self.get_metric_value("storage.errors_total") > 0,
            self.config.monitoring.alert_interval
        )
        
        # Embedding alerts
        self.register_alert(
            "embedding_errors",
            "Embedding errors detected",
            lambda: self.get_metric_value("embedding.errors_total") > 0,
            self.config.monitoring.alert_interval
        )
        
        # Retrieval alerts
        self.register_alert(
            "retrieval_errors",
            "Retrieval errors detected",
            lambda: self.get_metric_value("retrieval.errors_total") > 0,
            self.config.monitoring.alert_interval
        )
        
        # Generation alerts
        self.register_alert(
            "generation_errors",
            "Generation errors detected",
            lambda: self.get_metric_value("generation.errors_total") > 0,
            self.config.monitoring.alert_interval
        )
        
        # Agent alerts
        self.register_alert(
            "agent_errors",
            "Agent errors detected",
            lambda: self.get_metric_value("agents.errors_total") > 0,
            self.config.monitoring.alert_interval
        )
    
    def _start_background_monitoring(self) -> None:
        """Start background monitoring thread."""
        self.monitoring_thread = threading.Thread(
            target=self._background_monitoring_loop,
            daemon=True
        )
        self.monitoring_thread.start()
    
    def _background_monitoring_loop(self) -> None:
        """Background monitoring loop."""
        while True:
            try:
                # Update system metrics
                self._update_system_metrics()
                
                # Check alerts
                self._check_alerts()
                
                # Sleep for the monitoring interval
                time.sleep(self.config.monitoring.interval)
            except Exception as e:
                logger.error(f"Error in background monitoring: {e}")
                time.sleep(10)  # Sleep for a short time before retrying
    
    def _update_system_metrics(self) -> None:
        """Update system metrics."""
        try:
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            self.update_metric("system.cpu_usage", cpu_usage)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.update_metric("system.memory_usage", memory.percent)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.update_metric("system.disk_usage", disk.percent)
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")
    
    def _check_alerts(self) -> None:
        """Check all registered alerts."""
        for alert_id, alert in self.alerts.items():
            try:
                # Skip if the alert was triggered recently
                if alert.get("last_triggered") and time.time() - alert["last_triggered"] < alert["interval"]:
                    continue
                
                # Check if the alert condition is met
                if alert["condition"]():
                    # Trigger the alert
                    self._trigger_alert(alert_id)
            except Exception as e:
                logger.error(f"Error checking alert {alert_id}: {e}")
    
    def _trigger_alert(self, alert_id: str) -> None:
        """Trigger an alert.
        
        Args:
            alert_id: The alert ID.
        """
        if alert_id not in self.alerts:
            logger.warning(f"Unknown alert ID: {alert_id}")
            return
        
        alert = self.alerts[alert_id]
        
        # Update last triggered time
        alert["last_triggered"] = time.time()
        
        # Create alert record
        alert_record = {
            "id": alert_id,
            "message": alert["message"],
            "timestamp": datetime.utcnow().isoformat(),
            "severity": alert.get("severity", "warning")
        }
        
        # Add to alert history
        self.alert_history.append(alert_record)
        
        # Log the alert
        log_level = logging.WARNING if alert_record["severity"] == "warning" else logging.ERROR
        logger.log(log_level, f"Alert triggered: {alert_record['message']}")
        
        # Send notifications if configured
        self._send_alert_notifications(alert_record)
    
    def _send_alert_notifications(self, alert_record: Dict[str, Any]) -> None:
        """Send alert notifications.
        
        Args:
            alert_record: The alert record.
        """
        # Check if notifications are enabled
        if not self.config.monitoring.notifications_enabled:
            return
        
        # Send email notification if configured
        if self.config.monitoring.email_notifications_enabled:
            self._send_email_notification(alert_record)
        
        # Send webhook notification if configured
        if self.config.monitoring.webhook_notifications_enabled:
            self._send_webhook_notification(alert_record)
    
    def _send_email_notification(self, alert_record: Dict[str, Any]) -> None:
        """Send email notification.
        
        Args:
            alert_record: The alert record.
        """
        # This is a placeholder for email notification implementation
        # In a real implementation, this would use an email library to send the notification
        logger.info(f"Would send email notification for alert: {alert_record['message']}")
    
    def _send_webhook_notification(self, alert_record: Dict[str, Any]) -> None:
        """Send webhook notification.
        
        Args:
            alert_record: The alert record.
        """
        # This is a placeholder for webhook notification implementation
        # In a real implementation, this would use a HTTP client to send the notification
        logger.info(f"Would send webhook notification for alert: {alert_record['message']}")
    
    def register_metric(self, name: str, metric_type: str, description: str) -> None:
        """Register a new metric.
        
        Args:
            name: The metric name.
            metric_type: The metric type (counter, gauge, histogram, summary).
            description: The metric description.
        """
        if name in self.metrics:
            logger.warning(f"Metric {name} already registered, overwriting")
        
        self.metrics[name] = {
            "type": metric_type,
            "description": description,
            "value": 0 if metric_type in [MetricType.COUNTER, MetricType.GAUGE] else [],
            "created_at": time.time(),
            "updated_at": time.time()
        }
    
    def update_metric(self, name: str, value: Union[int, float, List[float]]) -> None:
        """Update a metric value.
        
        Args:
            name: The metric name.
            value: The metric value.
        
        Raises:
            MonitoringError: If the metric is not registered.
        """
        if name not in self.metrics:
            raise MonitoringError(f"Metric {name} not registered")
        
        metric = self.metrics[name]
        
        if metric["type"] == MetricType.COUNTER:
            # Counters can only increase
            if isinstance(value, (int, float)) and value >= 0:
                metric["value"] += value
            else:
                raise MonitoringError(f"Invalid value for counter metric {name}: {value}")
        elif metric["type"] == MetricType.GAUGE:
            # Gauges can be set to any value
            if isinstance(value, (int, float)):
                metric["value"] = value
            else:
                raise MonitoringError(f"Invalid value for gauge metric {name}: {value}")
        elif metric["type"] == MetricType.HISTOGRAM or metric["type"] == MetricType.SUMMARY:
            # Histograms and summaries collect observations
            if isinstance(value, (int, float)):
                metric["value"].append(value)
                # Limit the number of observations to prevent memory issues
                if len(metric["value"]) > 1000:
                    metric["value"] = metric["value"][-1000:]
            else:
                raise MonitoringError(f"Invalid value for {metric['type']} metric {name}: {value}")
        
        metric["updated_at"] = time.time()
    
    def get_metric_value(self, name: str) -> Union[int, float, List[float]]:
        """Get a metric value.
        
        Args:
            name: The metric name.
            
        Returns:
            The metric value.
            
        Raises:
            MonitoringError: If the metric is not registered.
        """
        if name not in self.metrics:
            raise MonitoringError(f"Metric {name} not registered")
        
        return self.metrics[name]["value"]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics.
        
        Returns:
            A dictionary of all metrics.
        """
        result = {}
        
        for name, metric in self.metrics.items():
            result[name] = {
                "type": metric["type"],
                "description": metric["description"],
                "value": metric["value"],
                "created_at": metric["created_at"],
                "updated_at": metric["updated_at"]
            }
            
            # Add derived values for histograms and summaries
            if metric["type"] in [MetricType.HISTOGRAM, MetricType.SUMMARY] and metric["value"]:
                values = sorted(metric["value"])
                result[name]["count"] = len(values)
                result[name]["sum"] = sum(values)
                result[name]["min"] = min(values)
                result[name]["max"] = max(values)
                result[name]["mean"] = sum(values) / len(values)
                result[name]["median"] = values[len(values) // 2]
                result[name]["p95"] = values[int(len(values) * 0.95)]
                result[name]["p99"] = values[int(len(values) * 0.99)]
        
        return result
    
    def register_health_check(self, name: str, check_func: Callable[[], Dict[str, Any]]) -> None:
        """Register a health check.
        
        Args:
            name: The health check name.
            check_func: The health check function.
        """
        if name in self.health_checks:
            logger.warning(f"Health check {name} already registered, overwriting")
        
        self.health_checks[name] = check_func
    
    def run_health_check(self, name: str) -> Dict[str, Any]:
        """Run a health check.
        
        Args:
            name: The health check name.
            
        Returns:
            The health check result.
            
        Raises:
            MonitoringError: If the health check is not registered.
        """
        if name not in self.health_checks:
            raise MonitoringError(f"Health check {name} not registered")
        
        try:
            return self.health_checks[name]()
        except Exception as e:
            logger.error(f"Error running health check {name}: {e}")
            return {
                "status": HealthStatus.ERROR,
                "message": f"Error running health check: {str(e)}"
            }
    
    def run_all_health_checks(self) -> Dict[str, Dict[str, Any]]:
        """Run all health checks.
        
        Returns:
            A dictionary of health check results.
        """
        results = {}
        overall_status = HealthStatus.OK
        
        for name in self.health_checks:
            result = self.run_health_check(name)
            results[name] = result
            
            # Update overall status
            if result["status"] == HealthStatus.ERROR:
                overall_status = HealthStatus.ERROR
            elif result["status"] == HealthStatus.WARNING and overall_status != HealthStatus.ERROR:
                overall_status = HealthStatus.WARNING
        
        # Add overall status
        results["overall"] = {
            "status": overall_status,
            "uptime": time.time() - self.start_time,
            "uptime_formatted": self._format_uptime(time.time() - self.start_time),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return results
    
    def register_alert(
        self,
        alert_id: str,
        message: str,
        condition: Callable[[], bool],
        interval: int = 3600,
        severity: str = "warning"
    ) -> None:
        """Register an alert.
        
        Args:
            alert_id: The alert ID.
            message: The alert message.
            condition: The alert condition function.
            interval: The minimum interval between alert triggers in seconds.
            severity: The alert severity (warning, error).
        """
        if alert_id in self.alerts:
            logger.warning(f"Alert {alert_id} already registered, overwriting")
        
        self.alerts[alert_id] = {
            "message": message,
            "condition": condition,
            "interval": interval,
            "severity": severity,
            "last_triggered": None
        }
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get all triggered alerts.
        
        Returns:
            A list of triggered alerts.
        """
        return list(self.alert_history)
    
    def _check_system_health(self) -> Dict[str, Any]:
        """Check system health.
        
        Returns:
            The health check result.
        """
        try:
            # Get system metrics
            cpu_usage = self.get_metric_value("system.cpu_usage")
            memory_usage = self.get_metric_value("system.memory_usage")
            disk_usage = self.get_metric_value("system.disk_usage")
            
            # Determine status
            status = HealthStatus.OK
            messages = []
            
            if cpu_usage > self.config.monitoring.cpu_threshold:
                status = HealthStatus.WARNING
                messages.append(f"CPU usage is high: {cpu_usage:.1f}%")
            
            if memory_usage > self.config.monitoring.memory_threshold:
                status = HealthStatus.WARNING
                messages.append(f"Memory usage is high: {memory_usage:.1f}%")
            
            if disk_usage > self.config.monitoring.disk_threshold:
                status = HealthStatus.WARNING
                messages.append(f"Disk usage is high: {disk_usage:.1f}%")
            
            return {
                "status": status,
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "disk_usage": disk_usage,
                "message": "; ".join(messages) if messages else "System is healthy"
            }
        except Exception as e:
            logger.error(f"Error checking system health: {e}")
            return {
                "status": HealthStatus.ERROR,
                "message": f"Error checking system health: {str(e)}"
            }
    
    def _check_api_health(self) -> Dict[str, Any]:
        """Check API health.
        
        Returns:
            The health check result.
        """
        try:
            # Get API metrics
            requests_total = self.get_metric_value("api.requests_total")
            errors_total = self.get_metric_value("api.errors_total")
            
            # Calculate error rate
            error_rate = self._calculate_error_rate("api")
            
            # Determine status
            status = HealthStatus.OK
            messages = []
            
            if error_rate > self.config.monitoring.error_threshold:
                status = HealthStatus.WARNING
                messages.append(f"API error rate is high: {error_rate:.2f}%")
            
            return {
                "status": status,
                "requests_total": requests_total,
                "errors_total": errors_total,
                "error_rate": error_rate,
                "message": "; ".join(messages) if messages else "API is healthy"
            }
        except Exception as e:
            logger.error(f"Error checking API health: {e}")
            return {
                "status": HealthStatus.ERROR,
                "message": f"Error checking API health: {str(e)}"
            }
    
    def _check_storage_health(self) -> Dict[str, Any]:
        """Check storage health.
        
        Returns:
            The health check result.
        """
        try:
            # Get storage metrics
            operations_total = self.get_metric_value("storage.operations_total")
            errors_total = self.get_metric_value("storage.errors_total")
            
            # Calculate error rate
            error_rate = self._calculate_error_rate("storage")
            
            # Determine status
            status = HealthStatus.OK
            messages = []
            
            if error_rate > self.config.monitoring.error_threshold:
                status = HealthStatus.WARNING
                messages.append(f"Storage error rate is high: {error_rate:.2f}%")
            
            return {
                "status": status,
                "operations_total": operations_total,
                "errors_total": errors_total,
                "error_rate": error_rate,
                "message": "; ".join(messages) if messages else "Storage is healthy"
            }
        except Exception as e:
            logger.error(f"Error checking storage health: {e}")
            return {
                "status": HealthStatus.ERROR,
                "message": f"Error checking storage health: {str(e)}"
            }
    
    def _check_embedding_health(self) -> Dict[str, Any]:
        """Check embedding health.
        
        Returns:
            The health check result.
        """
        try:
            # Get embedding metrics
            operations_total = self.get_metric_value("embedding.operations_total")
            errors_total = self.get_metric_value("embedding.errors_total")
            
            # Calculate error rate
            error_rate = self._calculate_error_rate("embedding")
            
            # Determine status
            status = HealthStatus.OK
            messages = []
            
            if error_rate > self.config.monitoring.error_threshold:
                status = HealthStatus.WARNING
                messages.append(f"Embedding error rate is high: {error_rate:.2f}%")
            
            return {
                "status": status,
                "operations_total": operations_total,
                "errors_total": errors_total,
                "error_rate": error_rate,
                "message": "; ".join(messages) if messages else "Embedding is healthy"
            }
        except Exception as e:
            logger.error(f"Error checking embedding health: {e}")
            return {
                "status": HealthStatus.ERROR,
                "message": f"Error checking embedding health: {str(e)}"
            }
    
    def _check_retrieval_health(self) -> Dict[str, Any]:
        """Check retrieval health.
        
        Returns:
            The health check result.
        """
        try:
            # Get retrieval metrics
            queries_total = self.get_metric_value("retrieval.queries_total")
            errors_total = self.get_metric_value("retrieval.errors_total")
            
            # Calculate error rate
            error_rate = self._calculate_error_rate("retrieval")
            
            # Determine status
            status = HealthStatus.OK
            messages = []
            
            if error_rate > self.config.monitoring.error_threshold:
                status = HealthStatus.WARNING
                messages.append(f"Retrieval error rate is high: {error_rate:.2f}%")
            
            return {
                "status": status,
                "queries_total": queries_total,
                "errors_total": errors_total,
                "error_rate": error_rate,
                "message": "; ".join(messages) if messages else "Retrieval is healthy"
            }
        except Exception as e:
            logger.error(f"Error checking retrieval health: {e}")
            return {
                "status": HealthStatus.ERROR,
                "message": f"Error checking retrieval health: {str(e)}"
            }
    
    def _check_generation_health(self) -> Dict[str, Any]:
        """Check generation health.
        
        Returns:
            The health check result.
        """
        try:
            # Get generation metrics
            requests_total = self.get_metric_value("generation.requests_total")
            errors_total = self.get_metric_value("generation.errors_total")
            
            # Calculate error rate
            error_rate = self._calculate_error_rate("generation")
            
            # Determine status
            status = HealthStatus.OK
            messages = []
            
            if error_rate > self.config.monitoring.error_threshold:
                status = HealthStatus.WARNING
                messages.append(f"Generation error rate is high: {error_rate:.2f}%")
            
            return {
                "status": status,
                "requests_total": requests_total,
                "errors_total": errors_total,
                "error_rate": error_rate,
                "message": "; ".join(messages) if messages else "Generation is healthy"
            }
        except Exception as e:
            logger.error(f"Error checking generation health: {e}")
            return {
                "status": HealthStatus.ERROR,
                "message": f"Error checking generation health: {str(e)}"
            }
    
    def _check_agents_health(self) -> Dict[str, Any]:
        """Check agents health.
        
        Returns:
            The health check result.
        """
        try:
            # Get agent metrics
            messages_total = self.get_metric_value("agents.messages_total")
            errors_total = self.get_metric_value("agents.errors_total")
            
            # Calculate error rate
            error_rate = self._calculate_error_rate("agents")
            
            # Determine status
            status = HealthStatus.OK
            messages = []
            
            if error_rate > self.config.monitoring.error_threshold:
                status = HealthStatus.WARNING
                messages.append(f"Agent error rate is high: {error_rate:.2f}%")
            
            return {
                "status": status,
                "messages_total": messages_total,
                "errors_total": errors_total,
                "error_rate": error_rate,
                "message": "; ".join(messages) if messages else "Agents are healthy"
            }
        except Exception as e:
            logger.error(f"Error checking agents health: {e}")
            return {
                "status": HealthStatus.ERROR,
                "message": f"Error checking agents health: {str(e)}"
            }
    
    def _calculate_error_rate(self, component: str) -> float:
        """Calculate error rate for a component.
        
        Args:
            component: The component name.
            
        Returns:
            The error rate as a percentage.
        """
        try:
            if component == "api":
                requests_total = self.get_metric_value("api.requests_total")
                errors_total = self.get_metric_value("api.errors_total")
            elif component == "storage":
                requests_total = self.get_metric_value("storage.operations_total")
                errors_total = self.get_metric_value("storage.errors_total")
            elif component == "embedding":
                requests_total = self.get_metric_value("embedding.operations_total")
                errors_total = self.get_metric_value("embedding.errors_total")
            elif component == "retrieval":
                requests_total = self.get_metric_value("retrieval.queries_total")
                errors_total = self.get_metric_value("retrieval.errors_total")
            elif component == "generation":
                requests_total = self.get_metric_value("generation.requests_total")
                errors_total = self.get_metric_value("generation.errors_total")
            elif component == "agents":
                requests_total = self.get_metric_value("agents.messages_total")
                errors_total = self.get_metric_value("agents.errors_total")
            else:
                return 0.0
            
            if requests_total == 0:
                return 0.0
            
            return (errors_total / requests_total) * 100.0
        except Exception:
            return 0.0
    
    def _calculate_avg_response_time(self) -> float:
        """Calculate average API response time.
        
        Returns:
            The average response time in seconds.
        """
        try:
            response_times = self.get_metric_value("api.response_time")
            if not response_times:
                return 0.0
            
            return sum(response_times) / len(response_times)
        except Exception:
            return 0.0
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in seconds to a human-readable string.
        
        Args:
            seconds: The uptime in seconds.
            
        Returns:
            A human-readable uptime string.
        """
        days, remainder = divmod(int(seconds), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0 or days > 0:
            parts.append(f"{hours}h")
        if minutes > 0 or hours > 0 or days > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        
        return " ".join(parts)


# Global monitoring instance
_monitoring_system = None


def get_monitoring_system(config: Optional[Config] = None) -> MonitoringSystem:
    """Get the monitoring system instance.
    
    Args:
        config: The configuration instance.
        
    Returns:
        The monitoring system instance.
    """
    global _monitoring_system
    
    if _monitoring_system is None:
        if config is None:
            from .config import Config
            config = Config()
        
        _monitoring_system = MonitoringSystem(config)
    
    return _monitoring_system