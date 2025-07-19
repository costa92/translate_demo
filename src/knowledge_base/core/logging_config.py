"""
Logging configuration for the unified knowledge base system.

This module provides utilities for configuring logging.
"""

import os
import logging
import logging.handlers
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

from .config import Config


def configure_logging(config: Config) -> None:
    """Configure logging based on configuration.
    
    Args:
        config: The configuration instance.
    """
    # Create logs directory if it doesn't exist
    log_dir = Path(config.monitoring.log_file).parent if config.monitoring.log_file else Path("logs")
    log_dir.mkdir(exist_ok=True, parents=True)
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.monitoring.log_level))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(config.monitoring.log_format)
    
    # Add console handler if enabled
    if config.monitoring.log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Add file handler if enabled
    if config.monitoring.log_to_file and config.monitoring.log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            config.monitoring.log_file,
            maxBytes=config.monitoring.log_max_size,
            backupCount=config.monitoring.log_backup_count
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Configure audit logger
    audit_logger = logging.getLogger("audit")
    audit_logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in audit_logger.handlers[:]:
        audit_logger.removeHandler(handler)
    
    # Add audit file handler
    audit_log_file = log_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.log"
    audit_handler = logging.FileHandler(audit_log_file)
    audit_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    audit_logger.addHandler(audit_handler)
    
    # Configure JSON logger for structured logging
    json_logger = logging.getLogger("json")
    json_logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in json_logger.handlers[:]:
        json_logger.removeHandler(handler)
    
    # Add JSON file handler
    json_log_file = log_dir / f"json_{datetime.now().strftime('%Y%m%d')}.log"
    json_handler = logging.FileHandler(json_log_file)
    json_handler.setFormatter(JsonFormatter())
    json_logger.addHandler(json_handler)
    
    # Set library loggers to WARNING level to reduce noise
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    
    # Log configuration
    logging.info(f"Logging configured with level {config.monitoring.log_level}")
    if config.monitoring.log_to_file and config.monitoring.log_file:
        logging.info(f"Logging to file: {config.monitoring.log_file}")


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as JSON.
        
        Args:
            record: The log record.
            
        Returns:
            The formatted log record as JSON.
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "thread_name": record.threadName
        }
        
        # Add exception info if available
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        # Add extra fields
        if hasattr(record, "extra"):
            log_data["extra"] = record.extra
        
        return json.dumps(log_data)


def get_logs(
    level: str = "info",
    limit: int = 100,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    source: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get logs from the log file.
    
    Args:
        level: Minimum log level.
        limit: Maximum number of log entries.
        start_time: Start time for logs (ISO format).
        end_time: End time for logs (ISO format).
        source: Log source filter.
        
    Returns:
        A list of log entries.
    """
    # This is a placeholder implementation
    # In a real implementation, this would read and parse log files
    return [
        {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "INFO",
            "message": "This is a placeholder log entry",
            "source": "system"
        }
    ]