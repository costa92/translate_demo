"""
Knowledge maintenance agent module for the knowledge base system.

This module implements the knowledge maintenance agent that is responsible for
maintaining the health and quality of the knowledge base.
"""

import asyncio
import logging
import time
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Union

from src.knowledge_base.core.config import Config
from src.knowledge_base.core.exceptions import AgentError, MaintenanceError
from src.knowledge_base.core.types import MaintenanceTask, MaintenanceResult
from src.knowledge_base.storage.vector_store import VectorStore

from .base import BaseAgent
from .message import AgentMessage

logger = logging.getLogger(__name__)


class KnowledgeMaintenanceAgent(BaseAgent):
    """Agent responsible for maintaining the knowledge base.
    
    The knowledge maintenance agent is responsible for:
    1. Performing scheduled maintenance tasks
    2. Checking data integrity
    3. Optimizing storage performance
    4. Assessing knowledge quality
    5. Cleaning up outdated or irrelevant information
    
    It acts as the caretaker for the knowledge base system,
    ensuring that the knowledge base remains healthy and efficient.
    """
    
    def __init__(self, config: Config, agent_id: str = "maintenance_agent"):
        """Initialize the knowledge maintenance agent.
        
        Args:
            config: The system configuration.
            agent_id: Unique identifier for this agent.
        """
        super().__init__(config, agent_id)
        
        # Register message handlers
        self.register_handler("task", self.handle_task)
        
        # Initialize vector store
        self.vector_store = VectorStore(config)
        
        # Initialize maintenance settings
        self.scheduled_tasks = {}
        self.maintenance_history = []
        self.max_history_size = 100
        
        # Initialize maintenance schedule from config
        self._initialize_schedule()
    
    def _initialize_schedule(self) -> None:
        """Initialize the maintenance schedule from configuration."""
        if not hasattr(self.config, "maintenance"):
            return
        
        # Set up scheduled tasks
        if hasattr(self.config.maintenance, "scheduled_tasks"):
            for task_name, schedule in self.config.maintenance.scheduled_tasks.items():
                if isinstance(schedule, dict) and "interval" in schedule:
                    interval = schedule["interval"]
                    enabled = schedule.get("enabled", True)
                    if enabled:
                        self.scheduled_tasks[task_name] = {
                            "interval": interval,
                            "last_run": 0,
                            "enabled": True,
                            "params": schedule.get("params", {})
                        }
    
    async def start(self) -> None:
        """Start the agent and initialize the vector store."""
        await super().start()
        
        try:
            # Initialize the vector store
            await self.vector_store.initialize()
            logger.info(f"Knowledge maintenance agent {self.agent_id} started with initialized vector store")
            
            # Start maintenance scheduler
            asyncio.create_task(self._maintenance_scheduler())
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            # Send error status message
            error_message = AgentMessage(
                source=self.agent_id,
                destination="*",
                message_type="agent_status",
                payload={
                    "status": "error",
                    "error": f"Failed to initialize vector store: {e}"
                }
            )
            await self.dispatch_message(error_message)
    
    async def stop(self) -> None:
        """Stop the agent and close the vector store."""
        try:
            # Close the vector store
            await self.vector_store.close()
            logger.info(f"Vector store closed for agent {self.agent_id}")
        except Exception as e:
            logger.error(f"Error closing vector store: {e}")
        
        await super().stop()
    
    async def process_message(self, message: AgentMessage) -> AgentMessage:
        """Process a message and return a response.
        
        Args:
            message: The message to process.
            
        Returns:
            The response message.
        """
        if message.message_type == "task":
            # Handle task messages through the registered handler
            await self.handle_task(message)
            return message.create_response({"status": "processing"})
        else:
            # For other message types, return a simple acknowledgment
            return message.create_response({"status": "acknowledged"})
    
    async def handle_task(self, message: AgentMessage) -> None:
        """Handle a task message.
        
        Args:
            message: The task message.
        """
        task_id = message.payload.get("task_id")
        task = message.payload.get("task")
        params = message.payload.get("params", {})
        
        if not task_id or not task:
            error_msg = "Missing task_id or task in task message"
            await self.dispatch_message(message.create_error_response(error_msg))
            return
        
        try:
            # Check if the task is a maintenance task
            if task in ["check_integrity", "optimize_storage", "clean_outdated", "assess_quality", "run_all"]:
                # Run the maintenance task
                result = await self._run_maintenance_task(task, params)
                
                # Send task completion message
                completion_message = AgentMessage(
                    source=self.agent_id,
                    destination=message.source,
                    message_type="task_complete",
                    payload={
                        "task_id": task_id,
                        "result": result
                    }
                )
                
                await self.dispatch_message(completion_message)
                
            elif task == "get_maintenance_history":
                # Get maintenance history
                limit = params.get("limit", 10)
                history = self.maintenance_history[-limit:] if limit > 0 else self.maintenance_history
                
                # Send task completion message
                completion_message = AgentMessage(
                    source=self.agent_id,
                    destination=message.source,
                    message_type="task_complete",
                    payload={
                        "task_id": task_id,
                        "result": {
                            "history": history,
                            "count": len(history)
                        }
                    }
                )
                
                await self.dispatch_message(completion_message)
                
            elif task == "get_scheduled_tasks":
                # Get scheduled tasks
                tasks = {}
                for task_name, task_info in self.scheduled_tasks.items():
                    tasks[task_name] = {
                        "interval": task_info["interval"],
                        "last_run": task_info["last_run"],
                        "enabled": task_info["enabled"],
                        "next_run": task_info["last_run"] + task_info["interval"] if task_info["enabled"] else None
                    }
                
                # Send task completion message
                completion_message = AgentMessage(
                    source=self.agent_id,
                    destination=message.source,
                    message_type="task_complete",
                    payload={
                        "task_id": task_id,
                        "result": {
                            "tasks": tasks,
                            "count": len(tasks)
                        }
                    }
                )
                
                await self.dispatch_message(completion_message)
                
            elif task == "update_scheduled_task":
                # Update a scheduled task
                task_name = params.get("task_name")
                if not task_name:
                    raise AgentError("Missing task_name parameter")
                
                # Get task parameters
                interval = params.get("interval")
                enabled = params.get("enabled")
                task_params = params.get("params")
                
                # Update the task
                if task_name not in self.scheduled_tasks:
                    self.scheduled_tasks[task_name] = {
                        "interval": interval or 86400,  # Default to daily
                        "last_run": 0,
                        "enabled": enabled if enabled is not None else True,
                        "params": task_params or {}
                    }
                else:
                    if interval is not None:
                        self.scheduled_tasks[task_name]["interval"] = interval
                    if enabled is not None:
                        self.scheduled_tasks[task_name]["enabled"] = enabled
                    if task_params is not None:
                        self.scheduled_tasks[task_name]["params"] = task_params
                
                # Send task completion message
                completion_message = AgentMessage(
                    source=self.agent_id,
                    destination=message.source,
                    message_type="task_complete",
                    payload={
                        "task_id": task_id,
                        "result": {
                            "task_name": task_name,
                            "updated": True,
                            "task_info": self.scheduled_tasks[task_name]
                        }
                    }
                )
                
                await self.dispatch_message(completion_message)
                
            else:
                raise AgentError(f"Unsupported task: {task}")
                
        except Exception as e:
            logger.error(f"Error handling task {task} in knowledge maintenance agent: {e}")
            error_message = AgentMessage(
                source=self.agent_id,
                destination=message.source,
                message_type="task_error",
                payload={
                    "task_id": task_id,
                    "error": str(e),
                    "task": task
                }
            )
            await self.dispatch_message(error_message)
    
    async def _run_maintenance_task(self, task_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run a maintenance task.
        
        Args:
            task_name: The name of the task to run.
            params: Task parameters.
            
        Returns:
            Task result.
            
        Raises:
            MaintenanceError: If the task fails.
        """
        start_time = time.time()
        
        try:
            if task_name == "check_integrity":
                result = await self._check_integrity(params)
            elif task_name == "optimize_storage":
                result = await self._optimize_storage(params)
            elif task_name == "clean_outdated":
                result = await self._clean_outdated(params)
            elif task_name == "assess_quality":
                result = await self._assess_quality(params)
            elif task_name == "run_all":
                # Run all maintenance tasks
                integrity_result = await self._check_integrity(params)
                optimize_result = await self._optimize_storage(params)
                clean_result = await self._clean_outdated(params)
                quality_result = await self._assess_quality(params)
                
                # Combine results
                result = {
                    "integrity": integrity_result,
                    "optimize": optimize_result,
                    "clean": clean_result,
                    "quality": quality_result,
                    "all_successful": all([
                        integrity_result.get("success", False),
                        optimize_result.get("success", False),
                        clean_result.get("success", False),
                        quality_result.get("success", False)
                    ])
                }
            else:
                raise MaintenanceError(f"Unknown maintenance task: {task_name}")
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Add to maintenance history
            self._add_to_history(task_name, True, duration, result)
            
            # Update last run time if this is a scheduled task
            if task_name in self.scheduled_tasks:
                self.scheduled_tasks[task_name]["last_run"] = int(time.time())
            
            # Add success and duration to result
            result["success"] = True
            result["duration"] = duration
            
            return result
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Add to maintenance history
            self._add_to_history(task_name, False, duration, {"error": str(e)})
            
            # Update last run time if this is a scheduled task
            if task_name in self.scheduled_tasks:
                self.scheduled_tasks[task_name]["last_run"] = int(time.time())
            
            logger.error(f"Maintenance task {task_name} failed: {e}")
            raise MaintenanceError(f"Maintenance task {task_name} failed: {e}")
    
    async def _check_integrity(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Check the integrity of the knowledge base.
        
        Args:
            params: Task parameters.
            
        Returns:
            Task result.
        """
        # Get storage statistics
        stats = await self.vector_store.get_stats()
        
        # Check for any errors in the stats
        if "error" in stats:
            return {
                "status": "error",
                "error": stats["error"],
                "checks_passed": 0,
                "checks_failed": 1
            }
        
        # Perform basic integrity checks
        checks_passed = 0
        checks_failed = 0
        issues = []
        
        # Check if the vector store is initialized
        if stats.get("initialized", False):
            checks_passed += 1
        else:
            checks_failed += 1
            issues.append("Vector store is not initialized")
        
        # Check if there are any documents
        if stats.get("total_documents", 0) > 0:
            checks_passed += 1
        else:
            checks_failed += 1
            issues.append("No documents in the vector store")
        
        # Check if there are any chunks
        if stats.get("total_chunks", 0) > 0:
            checks_passed += 1
        else:
            checks_failed += 1
            issues.append("No chunks in the vector store")
        
        # Return the result
        return {
            "status": "ok" if checks_failed == 0 else "issues",
            "checks_passed": checks_passed,
            "checks_failed": checks_failed,
            "issues": issues,
            "stats": stats
        }
    
    async def _optimize_storage(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize the storage of the knowledge base.
        
        Args:
            params: Task parameters.
            
        Returns:
            Task result.
        """
        # This is a placeholder for actual storage optimization
        # In a real implementation, this would depend on the vector store provider
        
        # Get storage statistics before optimization
        stats_before = await self.vector_store.get_stats()
        
        # Simulate optimization
        await asyncio.sleep(0.5)
        
        # Get storage statistics after optimization
        stats_after = await self.vector_store.get_stats()
        
        # Return the result
        return {
            "status": "optimized",
            "stats_before": stats_before,
            "stats_after": stats_after,
            "improvements": {
                "size_reduction": "0%",  # Placeholder
                "query_speed_improvement": "0%"  # Placeholder
            }
        }
    
    async def _clean_outdated(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Clean outdated information from the knowledge base.
        
        Args:
            params: Task parameters.
            
        Returns:
            Task result.
        """
        # Get parameters
        max_age_days = params.get("max_age_days", 365)  # Default to 1 year
        
        # Calculate cutoff date
        cutoff_timestamp = time.time() - (max_age_days * 86400)
        
        # This is a placeholder for actual cleaning
        # In a real implementation, this would query and delete outdated documents
        
        # Simulate cleaning
        deleted_count = 0
        
        # Return the result
        return {
            "status": "cleaned",
            "deleted_count": deleted_count,
            "max_age_days": max_age_days,
            "cutoff_date": datetime.fromtimestamp(cutoff_timestamp).isoformat()
        }
    
    async def _assess_quality(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the quality of the knowledge base.
        
        Args:
            params: Task parameters.
            
        Returns:
            Task result.
        """
        # This is a placeholder for actual quality assessment
        # In a real implementation, this would analyze the content quality
        
        # Get storage statistics
        stats = await self.vector_store.get_stats()
        
        # Simulate quality assessment
        quality_metrics = {
            "coverage": 0.8,  # Placeholder
            "accuracy": 0.9,  # Placeholder
            "freshness": 0.7,  # Placeholder
            "overall": 0.8  # Placeholder
        }
        
        # Return the result
        return {
            "status": "assessed",
            "quality_metrics": quality_metrics,
            "recommendations": [
                "Add more recent information to improve freshness",
                "Consider expanding coverage in underrepresented areas"
            ],
            "stats": stats
        }
    
    def _add_to_history(self, task_name: str, success: bool, duration: float, result: Dict[str, Any]) -> None:
        """Add a task to the maintenance history.
        
        Args:
            task_name: The name of the task.
            success: Whether the task was successful.
            duration: The duration of the task in seconds.
            result: The task result.
        """
        # Create history entry
        entry = {
            "task": task_name,
            "timestamp": int(time.time()),
            "success": success,
            "duration": duration,
            "result": result
        }
        
        # Add to history
        self.maintenance_history.append(entry)
        
        # Trim history if needed
        if len(self.maintenance_history) > self.max_history_size:
            self.maintenance_history = self.maintenance_history[-self.max_history_size:]
    
    async def _maintenance_scheduler(self) -> None:
        """Scheduler for maintenance tasks."""
        while self._running:
            try:
                current_time = int(time.time())
                
                # Check for tasks that need to be run
                for task_name, task_info in self.scheduled_tasks.items():
                    if (task_info["enabled"] and 
                        current_time - task_info["last_run"] >= task_info["interval"]):
                        # Run the task
                        try:
                            logger.info(f"Running scheduled maintenance task: {task_name}")
                            await self._run_maintenance_task(task_name, task_info["params"])
                        except Exception as e:
                            logger.error(f"Error running scheduled maintenance task {task_name}: {e}")
                
                # Sleep for a while before checking again
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in maintenance scheduler: {e}")
                await asyncio.sleep(300)  # Sleep and try again later