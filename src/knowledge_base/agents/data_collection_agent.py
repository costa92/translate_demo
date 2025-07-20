"""
Data collection agent module for the knowledge base system.

This module implements the data collection agent that is responsible for
collecting data from various sources like files, web pages, and APIs.
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
import urllib.parse
import urllib.request
import mimetypes
import json

from knowledge_base.core.config import Config
from knowledge_base.core.exceptions import AgentError
from knowledge_base.core.types import Document, DocumentType

from .base import BaseAgent
from .message import AgentMessage

logger = logging.getLogger(__name__)


class DataCollectionAgent(BaseAgent):
    """Agent responsible for collecting data from various sources.
    
    The data collection agent is responsible for:
    1. Processing local files and directories
    2. Scraping web content
    3. Connecting to external APIs
    4. Extracting data from various formats
    
    It acts as the entry point for bringing external data into the
    knowledge base system.
    """
    
    def __init__(self, config: Config, agent_id: str = "collection_agent"):
        """Initialize the data collection agent.
        
        Args:
            config: The system configuration.
            agent_id: Unique identifier for this agent.
        """
        super().__init__(config, agent_id)
        
        # Register message handlers
        self.register_handler("task", self.handle_task)
        
        # Initialize supported source types
        self.supported_source_types = {
            "file": self._collect_from_file,
            "directory": self._collect_from_directory,
            "url": self._collect_from_url,
            "api": self._collect_from_api,
        }
        
        # Initialize supported file extensions
        self.supported_extensions = {
            ".txt": DocumentType.TEXT,
            ".md": DocumentType.MARKDOWN,
            ".pdf": DocumentType.PDF,
            ".docx": DocumentType.DOCX,
            ".html": DocumentType.HTML,
            ".htm": DocumentType.HTML,
            ".json": DocumentType.TEXT,
            ".csv": DocumentType.TEXT,
            ".xml": DocumentType.TEXT,
        }
    
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
            if task == "collect":
                # Collect data from the specified source
                source = params.get("source")
                source_type = params.get("source_type")
                options = params.get("options", {})
                
                if not source:
                    raise AgentError("Missing source parameter")
                
                # Auto-detect source type if not specified
                if not source_type:
                    source_type = self._detect_source_type(source)
                
                # Check if the source type is supported
                if source_type not in self.supported_source_types:
                    raise AgentError(f"Unsupported source type: {source_type}")
                
                # Collect data from the source
                documents = await self.supported_source_types[source_type](source, options)
                
                # Send task completion message
                completion_message = AgentMessage(
                    source=self.agent_id,
                    destination=message.source,
                    message_type="task_complete",
                    payload={
                        "task_id": task_id,
                        "result": {
                            "documents": [doc.id for doc in documents],
                            "documents_collected": len(documents),
                            "source": source,
                            "source_type": source_type,
                        }
                    }
                )
                
                await self.dispatch_message(completion_message)
            else:
                raise AgentError(f"Unsupported task: {task}")
        except Exception as e:
            logger.error(f"Error handling task {task} in data collection agent: {e}")
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
    
    def _detect_source_type(self, source: str) -> str:
        """Detect the type of a source.
        
        Args:
            source: The source to detect.
            
        Returns:
            The detected source type.
        """
        # Check if it's a URL
        if source.startswith(("http://", "https://")):
            return "url"
        
        # Check if it's a local file or directory
        path = Path(source)
        if path.exists():
            if path.is_dir():
                return "directory"
            else:
                return "file"
        
        # Check if it looks like an API endpoint
        if "api" in source.lower() or "endpoint" in source.lower():
            return "api"
        
        # Default to file
        return "file"
    
    def _get_document_type(self, file_path: str) -> DocumentType:
        """Get the document type for a file.
        
        Args:
            file_path: The path to the file.
            
        Returns:
            The document type.
        """
        ext = os.path.splitext(file_path)[1].lower()
        return self.supported_extensions.get(ext, DocumentType.TEXT)
    
    async def _collect_from_file(self, file_path: str, options: Dict[str, Any]) -> List[Document]:
        """Collect data from a file.
        
        Args:
            file_path: The path to the file.
            options: Collection options.
            
        Returns:
            A list of documents.
            
        Raises:
            AgentError: If the file cannot be read.
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise AgentError(f"File not found: {file_path}")
            
            document_type = self._get_document_type(file_path)
            
            # Read the file content
            if document_type == DocumentType.PDF:
                # For PDF files, we need to use a PDF parser
                # This is a placeholder for actual PDF parsing
                content = f"PDF content from {file_path}"
            elif document_type == DocumentType.DOCX:
                # For DOCX files, we need to use a DOCX parser
                # This is a placeholder for actual DOCX parsing
                content = f"DOCX content from {file_path}"
            else:
                # For text-based files, read directly
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            
            # Create a document
            document = Document(
                id=f"doc_{os.path.basename(file_path)}_{hash(file_path)}",
                content=content,
                type=document_type,
                metadata={
                    "source": file_path,
                    "source_type": "file",
                    "filename": os.path.basename(file_path),
                    "extension": os.path.splitext(file_path)[1],
                    "size": os.path.getsize(file_path),
                    "created": os.path.getctime(file_path),
                    "modified": os.path.getmtime(file_path),
                    **options.get("metadata", {})
                }
            )
            
            return [document]
        except Exception as e:
            raise AgentError(f"Error collecting from file {file_path}: {e}")
    
    async def _collect_from_directory(self, directory_path: str, options: Dict[str, Any]) -> List[Document]:
        """Collect data from a directory.
        
        Args:
            directory_path: The path to the directory.
            options: Collection options.
            
        Returns:
            A list of documents.
            
        Raises:
            AgentError: If the directory cannot be read.
        """
        try:
            path = Path(directory_path)
            if not path.exists() or not path.is_dir():
                raise AgentError(f"Directory not found: {directory_path}")
            
            documents = []
            recursive = options.get("recursive", True)
            
            # Get file extensions to include
            include_extensions = options.get("include_extensions", list(self.supported_extensions.keys()))
            
            # Walk through the directory
            for root, _, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    ext = os.path.splitext(file_path)[1].lower()
                    
                    # Skip files with unsupported extensions
                    if ext not in include_extensions:
                        continue
                    
                    # Collect from the file
                    file_documents = await self._collect_from_file(file_path, options)
                    documents.extend(file_documents)
                
                # Stop recursion if not recursive
                if not recursive:
                    break
            
            return documents
        except Exception as e:
            raise AgentError(f"Error collecting from directory {directory_path}: {e}")
    
    async def _collect_from_url(self, url: str, options: Dict[str, Any]) -> List[Document]:
        """Collect data from a URL.
        
        Args:
            url: The URL to collect from.
            options: Collection options.
            
        Returns:
            A list of documents.
            
        Raises:
            AgentError: If the URL cannot be accessed.
        """
        try:
            # Parse the URL
            parsed_url = urllib.parse.urlparse(url)
            
            # Create a request
            headers = options.get("headers", {})
            req = urllib.request.Request(url, headers=headers)
            
            # Send the request
            with urllib.request.urlopen(req) as response:
                content = response.read().decode("utf-8")
                content_type = response.info().get_content_type()
            
            # Determine document type based on content type
            if content_type == "text/html":
                document_type = DocumentType.HTML
            elif content_type == "application/pdf":
                document_type = DocumentType.PDF
            elif content_type == "application/json":
                document_type = DocumentType.TEXT
                # Parse JSON for better structure
                try:
                    json_content = json.loads(content)
                    content = json.dumps(json_content, indent=2)
                except:
                    pass
            else:
                document_type = DocumentType.TEXT
            
            # Create a document
            document = Document(
                id=f"doc_url_{hash(url)}",
                content=content,
                type=document_type,
                metadata={
                    "source": url,
                    "source_type": "url",
                    "domain": parsed_url.netloc,
                    "path": parsed_url.path,
                    "content_type": content_type,
                    **options.get("metadata", {})
                }
            )
            
            return [document]
        except Exception as e:
            raise AgentError(f"Error collecting from URL {url}: {e}")
    
    async def _collect_from_api(self, api_endpoint: str, options: Dict[str, Any]) -> List[Document]:
        """Collect data from an API.
        
        Args:
            api_endpoint: The API endpoint to collect from.
            options: Collection options.
            
        Returns:
            A list of documents.
            
        Raises:
            AgentError: If the API cannot be accessed.
        """
        try:
            # Parse the API endpoint
            parsed_url = urllib.parse.urlparse(api_endpoint)
            
            # Get request parameters
            method = options.get("method", "GET")
            headers = options.get("headers", {})
            params = options.get("params", {})
            body = options.get("body")
            
            # Build the URL with query parameters
            if params and method == "GET":
                query = urllib.parse.urlencode(params)
                api_endpoint = f"{api_endpoint}?{query}"
            
            # Create a request
            req = urllib.request.Request(
                api_endpoint,
                data=json.dumps(body).encode("utf-8") if body else None,
                headers=headers,
                method=method
            )
            
            # Send the request
            with urllib.request.urlopen(req) as response:
                content = response.read().decode("utf-8")
            
            # Parse JSON response
            try:
                json_content = json.loads(content)
                content = json.dumps(json_content, indent=2)
            except:
                pass
            
            # Create a document
            document = Document(
                id=f"doc_api_{hash(api_endpoint)}",
                content=content,
                type=DocumentType.TEXT,
                metadata={
                    "source": api_endpoint,
                    "source_type": "api",
                    "method": method,
                    "domain": parsed_url.netloc,
                    "path": parsed_url.path,
                    **options.get("metadata", {})
                }
            )
            
            return [document]
        except Exception as e:
            raise AgentError(f"Error collecting from API {api_endpoint}: {e}")