"""
Unit tests for the monitoring system.
"""

import pytest
import time
from unittest.mock import MagicMock, patch

from src.knowledge_base.core.config import Config
from src.knowledge_base.core.monitoring import MonitoringSystem, MetricType, HealthStatus


@pytest.fixture
def config():
    """Create a test configuration."""
    config = Config()
    config.monitoring.enabled = True
    config.monitoring.interval = 1
    config.monitoring.cpu_threshold = 80.0
    config.monitoring.memory_threshold = 80.0
    config.monitoring.disk_threshold = 80.0
    config.monitoring.error_threshold = 5.0
    return config


@pytest.fixture
def monitoring_system(config):
    """Create a test monitoring system."""
    with patch('src.knowledge_base.core.monitoring.threading.Thread'):
        monitoring = MonitoringSystem(config)
        # Mock system metrics update to avoid actual system calls
        monitoring._update_system_metrics = MagicMock()
        return monitoring


def test_register_metric(monitoring_system):
    """Test registering a metric."""
    monitoring_system.register_metric("test.metric", MetricType.COUNTER, "Test metric")
    assert "test.metric" in monitoring_system.metrics
    assert monitoring_system.metrics["test.metric"]["type"] == MetricType.COUNTER
    assert monitoring_system.metrics["test.metric"]["description"] == "Test metric"
    assert monitoring_system.metrics["test.metric"]["value"] == 0


def test_update_counter_metric(monitoring_system):
    """Test updating a counter metric."""
    monitoring_system.register_metric("test.counter", MetricType.COUNTER, "Test counter")
    monitoring_system.update_metric("test.counter", 5)
    assert monitoring_system.get_metric_value("test.counter") == 5
    monitoring_system.update_metric("test.counter", 3)
    assert monitoring_system.get_metric_value("test.counter") == 8


def test_update_gauge_metric(monitoring_system):
    """Test updating a gauge metric."""
    monitoring_system.register_metric("test.gauge", MetricType.GAUGE, "Test gauge")
    monitoring_system.update_metric("test.gauge", 5)
    assert monitoring_system.get_metric_value("test.gauge") == 5
    monitoring_system.update_metric("test.gauge", 3)
    assert monitoring_system.get_metric_value("test.gauge") == 3


def test_update_histogram_metric(monitoring_system):
    """Test updating a histogram metric."""
    monitoring_system.register_metric("test.histogram", MetricType.HISTOGRAM, "Test histogram")
    monitoring_system.update_metric("test.histogram", 5)
    monitoring_system.update_metric("test.histogram", 3)
    assert monitoring_system.get_metric_value("test.histogram") == [5, 3]


def test_register_health_check(monitoring_system):
    """Test registering a health check."""
    def test_check():
        return {"status": HealthStatus.OK, "message": "Test OK"}
    
    monitoring_system.register_health_check("test", test_check)
    assert "test" in monitoring_system.health_checks
    result = monitoring_system.run_health_check("test")
    assert result["status"] == HealthStatus.OK
    assert result["message"] == "Test OK"


def test_run_all_health_checks(monitoring_system):
    """Test running all health checks."""
    def test_check1():
        return {"status": HealthStatus.OK, "message": "Test 1 OK"}
    
    def test_check2():
        return {"status": HealthStatus.WARNING, "message": "Test 2 Warning"}
    
    monitoring_system.register_health_check("test1", test_check1)
    monitoring_system.register_health_check("test2", test_check2)
    
    results = monitoring_system.run_all_health_checks()
    assert results["test1"]["status"] == HealthStatus.OK
    assert results["test2"]["status"] == HealthStatus.WARNING
    assert results["overall"]["status"] == HealthStatus.WARNING


def test_register_alert(monitoring_system):
    """Test registering an alert."""
    condition = lambda: True
    monitoring_system.register_alert("test_alert", "Test alert", condition)
    assert "test_alert" in monitoring_system.alerts
    assert monitoring_system.alerts["test_alert"]["message"] == "Test alert"


def test_trigger_alert(monitoring_system):
    """Test triggering an alert."""
    condition = lambda: True
    monitoring_system.register_alert("test_alert", "Test alert", condition)
    monitoring_system._trigger_alert("test_alert")
    alerts = monitoring_system.get_alerts()
    assert len(alerts) == 1
    assert alerts[0]["id"] == "test_alert"
    assert alerts[0]["message"] == "Test alert"


def test_calculate_error_rate(monitoring_system):
    """Test calculating error rate."""
    monitoring_system.register_metric("api.requests_total", MetricType.COUNTER, "Total requests")
    monitoring_system.register_metric("api.errors_total", MetricType.COUNTER, "Total errors")
    
    monitoring_system.update_metric("api.requests_total", 100)
    monitoring_system.update_metric("api.errors_total", 5)
    
    error_rate = monitoring_system._calculate_error_rate("api")
    assert error_rate == 5.0