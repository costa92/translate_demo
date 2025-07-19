"""
Orchestrator agent module for the knowledge base system.

This module implements the orchestrator agent that coordinates
the workflow between specialized agents.
"""

import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional, Set, AsyncIterator

from src.knowledge_base.core.config import Config
from src.knowledge_base.core.exceptions import AgentError

from .base import BaseAgent
from .message import AgentMessage
from .registry import create_agent

logger = logging.getLogger(__name__)


class OrchestratorAgent(BaseAgent):
    """Coordinates the workflow between agents.
    
    The orchestrator agent is responsible for:
    1. Task planning and distribution
    2. Result aggregation
    3. Error handling and recovery
    
    It acts as the central coordinator for the multi-agent system,
    receiving requests from external sources and delegating tasks
    to specialized agents.
    """
    
    def __init__(self, config: Config, agent_id: str = "orchestrator"):
        """Initialize the orchestrator agent.
        
        Args:
            config: The system configuration.
            agent_id: Unique identifier for this agent.
        """
        super().__init__(config, agent_id)
        self.agents: Dict[str, BaseAgent] = {}
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.task_results: Dict[str, Dict[str, Any]] = {}
        
        # Register message handlers
        self.register_handler("request", self.handle_request)
        self.register_handler("api_request", self.handle_api_request)
        self.register_handler("task_complete", self.handle_task_complete)
        self.register_handler("task_error", self.handle_task_error)
        self.register_handler("agent_status", self.handle_agent_status)
        
        # Subscribe to relevant message types
        self.subscribe("task_complete")
        self.subscribe("task_error")
        self.subscribe("agent_status")
        
        # Initialize specialized agents
        self._initialize_agents()
    
    def _initialize_agents(self) -> None:
        """Initialize all required specialized agents.
        
        This method creates instances of all specialized agents
        that the orchestrator will coordinate.
        """
        agent_configs = self.config.agents.specialized_agents
        
        for agent_type, enabled in agent_configs.items():
            if not enabled:
                continue
            
            try:
                agent_id = f"{agent_type}_agent"
                agent = create_agent(f"{agent_type.capitalize()}Agent", self.config, agent_id)
                self.agents[agent_type] = agent
                logger.info(f"Initialized {agent_type} agent with ID {agent_id}")
            except Exception as e:
                logger.error(f"Failed to initialize {agent_type} agent: {e}")
    
    async def start(self) -> None:
        """Start the orchestrator and all specialized agents."""
        await super().start()
        
        # Start all specialized agents
        for agent_type, agent in self.agents.items():
            try:
                await agent.start()
            except Exception as e:
                logger.error(f"Failed to start {agent_type} agent: {e}")
    
    async def stop(self) -> None:
        """Stop the orchestrator and all specialized agents."""
        # Stop all specialized agents
        for agent_type, agent in self.agents.items():
            try:
                await agent.stop()
            except Exception as e:
                logger.error(f"Failed to stop {agent_type} agent: {e}")
        
        await super().stop()
    
    async def handle_api_request(self, message: AgentMessage) -> None:
        """Handle an incoming API request.
        
        This method processes incoming API requests and creates a response
        with a processing status.
        
        Args:
            message: The API request message.
        """
        # Create a standardized internal request
        internal_request = AgentMessage(
            source=message.source,
            destination=self.agent_id,
            message_type="request",
            payload=message.payload
        )
        
        # Store the original message for response routing
        self.active_tasks[internal_request.id] = {
            "original_request": message,
            "status": "pending"
        }
        
        # Send an immediate response indicating processing
        response = message.create_response({
            "status": "processing",
            "message": "Request is being processed",
            "request_id": internal_request.id
        })
        
        await self.dispatch_message(response)
        
        # Process the internal request
        await self.send_message(internal_request)
    
    async def handle_request(self, message: AgentMessage) -> None:
        """Handle an incoming request.
        
        This method processes incoming requests and creates a task plan
        to fulfill the request using specialized agents.
        
        Args:
            message: The request message.
        """
        request_type = message.payload.get("request_type")
        if not request_type:
            error_msg = "Missing request_type in request payload"
            await self.dispatch_message(message.create_error_response(error_msg))
            return
        
        try:
            # Create a task plan based on the request type
            task_plan = await self._create_task_plan(request_type, message.payload)
            
            # Create a task context to track progress
            task_id = message.id
            self.active_tasks[task_id] = {
                "request": message,
                "plan": task_plan,
                "current_step": 0,
                "results": {},
                "errors": [],
                "status": "in_progress"
            }
            
            # Start executing the task plan
            await self._execute_next_task(task_id)
            
        except Exception as e:
            logger.error(f"Error creating task plan for request {message.id}: {e}")
            error_msg = f"Failed to process request: {str(e)}"
            await self.dispatch_message(message.create_error_response(error_msg))
    
    async def handle_task_complete(self, message: AgentMessage) -> None:
        """Handle a task completion message.
        
        This method processes task completion messages from specialized agents
        and updates the task context accordingly.
        
        Args:
            message: The task completion message.
        """
        task_id = message.payload.get("task_id")
        if not task_id or task_id not in self.active_tasks:
            logger.warning(f"Received task_complete for unknown task: {task_id}")
            return
        
        # Update task context with results
        task_context = self.active_tasks[task_id]
        agent_type = message.source.split("_")[0]  # Extract agent type from agent_id
        task_context["results"][agent_type] = message.payload.get("result", {})
        
        # Move to the next task in the plan
        task_context["current_step"] += 1
        
        if task_context["current_step"] >= len(task_context["plan"]):
            # All tasks completed, finalize the request
            await self._finalize_request(task_id)
        else:
            # Execute the next task in the plan
            await self._execute_next_task(task_id)
    
    async def handle_task_error(self, message: AgentMessage) -> None:
        """Handle a task error message.
        
        This method processes task error messages from specialized agents
        and implements error handling and recovery strategies.
        
        Args:
            message: The task error message.
        """
        task_id = message.payload.get("task_id")
        if not task_id or task_id not in self.active_tasks:
            logger.warning(f"Received task_error for unknown task: {task_id}")
            return
        
        # Update task context with error
        task_context = self.active_tasks[task_id]
        error = message.payload.get("error", "Unknown error")
        agent_type = message.source.split("_")[0]  # Extract agent type from agent_id
        
        task_context["errors"].append({
            "agent": agent_type,
            "step": task_context["current_step"],
            "error": error
        })
        
        # Implement recovery strategy based on the error
        recovery_successful = await self._attempt_recovery(task_id, agent_type, error)
        
        if not recovery_successful:
            # Recovery failed, finalize the request with error
            task_context["status"] = "failed"
            await self._finalize_request(task_id)
    
    async def handle_agent_status(self, message: AgentMessage) -> None:
        """Handle an agent status message.
        
        This method processes status updates from specialized agents.
        
        Args:
            message: The agent status message.
        """
        agent_id = message.source
        status = message.payload.get("status")
        
        if status == "error":
            # Agent is in error state, log and potentially restart
            error = message.payload.get("error", "Unknown error")
            logger.error(f"Agent {agent_id} reported error: {error}")
            
            # Attempt to restart the agent
            agent_type = agent_id.split("_")[0]  # Extract agent type from agent_id
            if agent_type in self.agents:
                try:
                    await self.agents[agent_type].stop()
                    await asyncio.sleep(1)  # Brief delay before restart
                    await self.agents[agent_type].start()
                    logger.info(f"Restarted agent {agent_id} after error")
                except Exception as e:
                    logger.error(f"Failed to restart agent {agent_id}: {e}")
    
    async def process_message(self, message: AgentMessage) -> AgentMessage:
        """Process a message and return a response.
        
        This method is the main entry point for processing messages
        in the orchestrator agent.
        
        Args:
            message: The message to process.
            
        Returns:
            The response message.
        """
        # For direct API requests, convert to internal request format
        if message.source.startswith("api"):
            request_type = message.payload.get("request_type", "query")
            
            # Create a standardized internal request
            internal_request = AgentMessage(
                source=message.source,
                destination=self.agent_id,
                message_type="request",
                payload={
                    "request_type": request_type,
                    **message.payload
                }
            )
            
            # Store the original message for response routing
            self.active_tasks[internal_request.id] = {
                "original_request": message,
                "status": "pending"
            }
            
            # Process the internal request
            await self.send_message(internal_request)
            
            # Create a placeholder response
            return message.create_response({
                "status": "processing",
                "message": "Request is being processed",
                "request_id": internal_request.id
            })
        
        # For internal messages, use the handler system
        return message.create_response({
            "status": "acknowledged",
            "message": "Message received"
        })
    
    async def receive_request(
        self, 
        source: str, 
        request_type: str, 
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Receive and process a request from an external source.
        
        This method is the main entry point for external systems
        to interact with the agent system.
        
        Args:
            source: The source of the request.
            request_type: The type of request.
            payload: The request payload.
            
        Returns:
            The response payload.
        """
        # Create a message from the request
        message = AgentMessage(
            source=source,
            destination=self.agent_id,
            message_type="request",
            payload={
                "request_type": request_type,
                **payload
            }
        )
        
        # Process the message
        response = await self.process_message(message)
        
        # If the response indicates processing, wait for completion
        if response.payload.get("status") == "processing":
            request_id = response.payload.get("request_id")
            if request_id:
                # Wait for the task to complete
                max_wait = 60  # Maximum wait time in seconds
                wait_interval = 0.5  # Check interval in seconds
                
                for _ in range(int(max_wait / wait_interval)):
                    if request_id not in self.active_tasks:
                        # Task completed and was removed
                        if request_id in self.task_results:
                            return self.task_results.pop(request_id)
                        break
                    
                    if self.active_tasks[request_id].get("status") in ["completed", "failed"]:
                        # Task completed or failed
                        result = self.active_tasks.pop(request_id)
                        if "result" in result:
                            return result["result"]
                        elif "error" in result:
                            return {"status": "error", "error": result["error"]}
                    
                    await asyncio.sleep(wait_interval)
                
                # Timeout reached
                return {
                    "status": "timeout",
                    "message": "Request processing timed out"
                }
        
        return response.payload
        
    async def receive_request_stream(
        self, 
        source: str, 
        request_type: str, 
        payload: Dict[str, Any]
    ) -> AsyncIterator[str]:
        """Receive and process a streaming request from an external source.
        
        This method is similar to receive_request but returns an async iterator
        for streaming responses.
        
        Args:
            source: The source of the request.
            request_type: The type of request.
            payload: The request payload.
            
        Yields:
            Chunks of the streaming response.
        """
        # Ensure streaming is enabled in the payload
        payload = {**payload, "stream": True}
        
        if request_type == "query":
            # For query requests, first retrieve chunks
            retrieval_response = await self.receive_request(
                source=source,
                request_type="retrieve",
                payload={
                    "query": payload.get("query"),
                    "filter": payload.get("filter"),
                    "top_k": payload.get("top_k", 5)
                }
            )
            
            # Then generate streaming response using the retrieved chunks
            chunks = retrieval_response.get("chunks", [])
            
            # Use the RAG agent directly for streaming generation
            if "rag" in self.agents:
                rag_agent = self.agents["rag"]
                
                # Create a task message for the RAG agent
                task_id = str(uuid.uuid4())
                task_message = AgentMessage(
                    source=self.agent_id,
                    destination=rag_agent.agent_id,
                    message_type="task",
                    payload={
                        "task_id": task_id,
                        "task": "generate_stream",
                        "params": {
                            "query": payload.get("query"),
                            "chunks": chunks,
                            "stream": True
                        }
                    }
                )
                
                # Send the message and get the stream
                async for chunk in rag_agent.generate_stream(task_message):
                    yield chunk
            else:
                # Fallback if RAG agent is not available
                yield "RAG agent not available for streaming generation."
                
        elif request_type == "generate":
            # For direct generate requests, use the provided chunks
            if "rag" in self.agents:
                rag_agent = self.agents["rag"]
                
                # Create a task message for the RAG agent
                task_id = str(uuid.uuid4())
                task_message = AgentMessage(
                    source=self.agent_id,
                    destination=rag_agent.agent_id,
                    message_type="task",
                    payload={
                        "task_id": task_id,
                        "task": "generate_stream",
                        "params": {
                            "query": payload.get("query"),
                            "chunks": payload.get("chunks", []),
                            "stream": True
                        }
                    }
                )
                
                # Send the message and get the stream
                async for chunk in rag_agent.generate_stream(task_message):
                    yield chunk
            else:
                # Fallback if RAG agent is not available
                yield "RAG agent not available for streaming generation."
        else:
            # Unsupported request type for streaming
            yield f"Streaming not supported for request type: {request_type}"
    
    async def _create_task_plan(self, request_type: str, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create a task plan for a request.
        
        This method analyzes the request and creates a sequence of tasks
        to be executed by specialized agents.
        
        Args:
            request_type: The type of request.
            payload: The request payload.
            
        Returns:
            A list of task steps, each containing the agent type and task details.
            
        Raises:
            AgentError: If the request type is not supported.
        """
        # Define task plans for different request types
        if request_type == "query":
            # Plan for query requests: retrieval -> generation
            return [
                {
                    "agent": "retrieval",
                    "task": "retrieve",
                    "params": {
                        "query": payload.get("query"),
                        "filter": payload.get("filter"),
                        "top_k": payload.get("top_k", 5)
                    }
                },
                {
                    "agent": "rag",
                    "task": "generate",
                    "params": {
                        "query": payload.get("query"),
                        "stream": payload.get("stream", False)
                    }
                }
            ]
        
        elif request_type == "add_document":
            # Plan for adding documents: processing -> storage
            return [
                {
                    "agent": "processing",
                    "task": "process_document",
                    "params": {
                        "document": payload.get("document"),
                        "metadata": payload.get("metadata", {})
                    }
                },
                {
                    "agent": "storage",
                    "task": "store_chunks",
                    "params": {}  # Will be populated with chunks from previous step
                }
            ]
        
        elif request_type == "collect_data":
            # Plan for data collection: collection -> processing -> storage
            return [
                {
                    "agent": "collection",
                    "task": "collect",
                    "params": {
                        "source": payload.get("source"),
                        "source_type": payload.get("source_type"),
                        "options": payload.get("options", {})
                    }
                },
                {
                    "agent": "processing",
                    "task": "process_documents",
                    "params": {}  # Will be populated with documents from previous step
                },
                {
                    "agent": "storage",
                    "task": "store_chunks",
                    "params": {}  # Will be populated with chunks from previous step
                }
            ]
        
        elif request_type == "maintenance":
            # Plan for maintenance tasks
            return [
                {
                    "agent": "maintenance",
                    "task": payload.get("maintenance_task", "check_integrity"),
                    "params": payload.get("params", {})
                }
            ]
        
        else:
            raise AgentError(f"Unsupported request type: {request_type}")
    
    async def _execute_next_task(self, task_id: str) -> None:
        """Execute the next task in the plan.
        
        This method sends a task message to the appropriate specialized agent
        based on the current step in the task plan.
        
        Args:
            task_id: The ID of the task context.
        """
        if task_id not in self.active_tasks:
            logger.warning(f"Task {task_id} not found in active tasks")
            return
        
        task_context = self.active_tasks[task_id]
        current_step = task_context["current_step"]
        
        if current_step >= len(task_context["plan"]):
            # No more tasks to execute
            await self._finalize_request(task_id)
            return
        
        # Get the current task step
        task_step = task_context["plan"][current_step]
        agent_type = task_step["agent"]
        task_name = task_step["task"]
        params = task_step["params"].copy()
        
        # Update parameters with results from previous steps if needed
        for prev_agent, prev_results in task_context["results"].items():
            if prev_agent in params and isinstance(params[prev_agent], dict):
                params[prev_agent].update(prev_results)
            else:
                params[prev_agent] = prev_results
        
        # Check if the required agent is available
        if agent_type not in self.agents:
            error_msg = f"Required agent '{agent_type}' not available"
            logger.error(error_msg)
            task_context["errors"].append({
                "agent": "orchestrator",
                "step": current_step,
                "error": error_msg
            })
            task_context["status"] = "failed"
            await self._finalize_request(task_id)
            return
        
        # Send task message to the agent
        agent = self.agents[agent_type]
        task_message = AgentMessage(
            source=self.agent_id,
            destination=agent.agent_id,
            message_type="task",
            payload={
                "task_id": task_id,
                "task": task_name,
                "params": params
            }
        )
        
        try:
            await self.dispatch_message(task_message)
            logger.info(f"Dispatched task '{task_name}' to {agent_type} agent for request {task_id}")
        except Exception as e:
            logger.error(f"Error dispatching task to {agent_type} agent: {e}")
            task_context["errors"].append({
                "agent": "orchestrator",
                "step": current_step,
                "error": f"Failed to dispatch task: {str(e)}"
            })
            task_context["status"] = "failed"
            await self._finalize_request(task_id)
    
    async def _finalize_request(self, task_id: str) -> None:
        """Finalize a request by aggregating results and sending a response.
        
        This method is called when all tasks in a plan have been completed
        or when an unrecoverable error occurs.
        
        Args:
            task_id: The ID of the task context.
        """
        if task_id not in self.active_tasks:
            logger.warning(f"Task {task_id} not found in active tasks")
            return
        
        task_context = self.active_tasks[task_id]
        original_request = task_context.get("original_request") or task_context["request"]
        
        if task_context["status"] == "failed" or task_context["errors"]:
            # Request failed, send error response
            error_details = task_context["errors"]
            error_msg = error_details[-1]["error"] if error_details else "Unknown error"
            
            response = original_request.create_error_response(
                error_msg,
                {"errors": error_details}
            )
            
            # Store the result for potential retrieval
            self.task_results[task_id] = {
                "status": "error",
                "error": error_msg,
                "details": error_details
            }
        else:
            # Request succeeded, aggregate results
            aggregated_result = await self._aggregate_results(task_context)
            
            response = original_request.create_response({
                "status": "success",
                "result": aggregated_result
            })
            
            # Store the result for potential retrieval
            self.task_results[task_id] = {
                "status": "success",
                "result": aggregated_result
            }
        
        # Send the response
        await self.dispatch_message(response)
        
        # Clean up task context after a delay
        asyncio.create_task(self._cleanup_task(task_id))
    
    async def _aggregate_results(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate results from all tasks in a plan.
        
        This method combines the results from all tasks in a plan
        into a single coherent response.
        
        Args:
            task_context: The task context containing results.
            
        Returns:
            The aggregated result.
        """
        results = task_context["results"]
        request = task_context["request"]
        request_type = request.payload.get("request_type")
        
        # Different aggregation strategies based on request type
        if request_type == "query":
            # For query requests, use the RAG agent's result
            if "rag" in results:
                return results["rag"]
            elif "retrieval" in results:
                # Fallback to retrieval results if RAG failed
                return {
                    "query": request.payload.get("query"),
                    "chunks": results["retrieval"].get("chunks", []),
                    "answer": "No answer generated."
                }
        
        elif request_type == "add_document":
            # For add_document requests, return storage result
            if "storage" in results:
                return results["storage"]
            elif "processing" in results:
                # Fallback to processing results if storage failed
                return {
                    "document_id": results["processing"].get("document_id"),
                    "chunks": len(results["processing"].get("chunks", [])),
                    "status": "processed_but_not_stored"
                }
        
        elif request_type == "collect_data":
            # For collect_data requests, combine results from all steps
            return {
                "collected": results.get("collection", {}).get("documents_collected", 0),
                "processed": results.get("processing", {}).get("chunks_created", 0),
                "stored": results.get("storage", {}).get("chunks_stored", 0),
                "status": "completed"
            }
        
        elif request_type == "maintenance":
            # For maintenance requests, return maintenance result
            if "maintenance" in results:
                return results["maintenance"]
        
        # Default aggregation: combine all results
        return {agent_type: result for agent_type, result in results.items()}
    
    async def _attempt_recovery(self, task_id: str, agent_type: str, error: str) -> bool:
        """Attempt to recover from a task error.
        
        This method implements recovery strategies for different types of errors.
        
        Args:
            task_id: The ID of the task context.
            agent_type: The type of agent that encountered an error.
            error: The error message.
            
        Returns:
            True if recovery was successful, False otherwise.
        """
        if task_id not in self.active_tasks:
            return False
        
        task_context = self.active_tasks[task_id]
        current_step = task_context["current_step"]
        
        # Check if we've already tried recovery for this step
        recovery_attempts = sum(
            1 for e in task_context["errors"] 
            if e["agent"] == agent_type and e["step"] == current_step
        )
        
        if recovery_attempts > 3:
            # Too many recovery attempts, give up
            logger.warning(f"Too many recovery attempts for task {task_id}, step {current_step}")
            return False
        
        # Implement different recovery strategies based on the error and agent type
        if "connection" in error.lower() or "timeout" in error.lower():
            # Connection issues, retry after a delay
            await asyncio.sleep(2 ** recovery_attempts)  # Exponential backoff
            
            # Retry the current task
            await self._execute_next_task(task_id)
            return True
        
        elif "not found" in error.lower() and agent_type == "retrieval":
            # Document not found in retrieval, try with relaxed parameters
            task_step = task_context["plan"][current_step]
            params = task_step["params"]
            
            # Modify parameters for retry
            if "top_k" in params:
                params["top_k"] = min(20, params["top_k"] * 2)  # Increase top_k
            
            if "filter" in params:
                params["filter"] = {}  # Remove filters
            
            # Retry with modified parameters
            await self._execute_next_task(task_id)
            return True
        
        elif agent_type == "rag" and "generation" in error.lower():
            # Generation error in RAG agent, try with a different provider
            task_step = task_context["plan"][current_step]
            params = task_step["params"]
            
            # Add fallback provider parameter
            providers = ["openai", "deepseek", "siliconflow", "ollama"]
            current_provider = params.get("provider", "openai")
            
            # Find the next provider in the list
            try:
                current_idx = providers.index(current_provider)
                next_idx = (current_idx + 1) % len(providers)
                params["provider"] = providers[next_idx]
            except ValueError:
                params["provider"] = "openai"  # Default fallback
            
            # Retry with different provider
            await self._execute_next_task(task_id)
            return True
        
        # No recovery strategy available
        return False
    
    async def _cleanup_task(self, task_id: str) -> None:
        """Clean up task context after a delay.
        
        This method removes completed task contexts after a delay
        to allow for result retrieval.
        
        Args:
            task_id: The ID of the task context.
        """
        # Wait for a while before cleanup
        await asyncio.sleep(300)  # 5 minutes
        
        # Remove task context and results
        self.active_tasks.pop(task_id, None)
        self.task_results.pop(task_id, None)