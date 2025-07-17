"""
Notion storage provider for the unified knowledge base system.

This module implements a vector store that uses Notion as the backend storage.
It stores documents and text chunks as pages in a Notion database, with embeddings
stored as JSON strings in rich text properties.

Optimizations included:
- Connection pooling for efficient HTTP connections
- Caching mechanisms for frequently accessed data
- Retry logic with exponential backoff
- Batch operations for improved performance
"""

import logging
import json
import uuid
import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from functools import wraps

import httpx
from cachetools import TTLCache

from ..base import BaseVectorStore
from ...core.types import Document, TextChunk, DocumentType
from ...core.exceptions import (
    StorageError, 
    StorageConnectionError, 
    DocumentNotFoundError, 
    ChunkNotFoundError,
    MissingConfigurationError
)

logger = logging.getLogger(__name__)


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
    """
    Decorator for retrying operations with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except (httpx.RequestError, httpx.HTTPStatusError) as e:
                    last_exception = e
                    if attempt == max_retries:
                        break
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                except Exception as e:
                    # Don't retry for non-network errors
                    raise e
            
            # If we get here, all retries failed
            raise StorageError(f"Operation failed after {max_retries} retries: {last_exception}")
        
        return wrapper
    return decorator


class NotionVectorStore(BaseVectorStore):
    """
    Notion-based vector store implementation.
    
    This provider stores documents and text chunks as pages in a Notion database.
    Vector embeddings are stored as JSON strings in rich text properties.
    
    Required configuration:
    - notion_api_key: Notion integration API key
    - notion_database_id: ID of the Notion database to use
    
    Optional configuration:
    - timeout: HTTP request timeout in seconds (default: 30)
    - max_text_length: Maximum text length for Notion properties (default: 2000)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Notion vector store with optimizations."""
        super().__init__(config)
        
        # Extract configuration
        self.api_key = config.get("notion_api_key")
        self.database_id = config.get("notion_database_id")
        self.timeout = config.get("timeout", 30.0)
        self.max_text_length = config.get("max_text_length", 2000)
        self.base_url = "https://api.notion.com/v1"
        
        # Optimization settings
        self.max_retries = config.get("max_retries", 3)
        self.base_delay = config.get("base_delay", 1.0)
        self.max_delay = config.get("max_delay", 60.0)
        self.cache_ttl = config.get("cache_ttl", 300)  # 5 minutes
        self.cache_maxsize = config.get("cache_maxsize", 1000)
        self.batch_size = config.get("batch_size", 10)
        
        # Connection pool settings
        self.max_connections = config.get("max_connections", 10)
        self.max_keepalive_connections = config.get("max_keepalive_connections", 5)
        
        # Validate required configuration
        if not self.api_key:
            raise MissingConfigurationError("notion_api_key")
        if not self.database_id:
            raise MissingConfigurationError("notion_database_id")
        
        # HTTP client with connection pooling
        self._client = None
        
        # Caching mechanisms
        self._page_cache = TTLCache(maxsize=self.cache_maxsize, ttl=self.cache_ttl)
        self._query_cache = TTLCache(maxsize=self.cache_maxsize, ttl=self.cache_ttl)
        
        logger.info(f"NotionVectorStore initialized with database: {self.database_id}")
        logger.info(f"Optimizations: retries={self.max_retries}, cache_ttl={self.cache_ttl}, batch_size={self.batch_size}")
    
    async def initialize(self) -> None:
        """Initialize Notion client and verify database access."""
        if self._initialized:
            return
        
        try:
            # Initialize HTTP client
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Notion-Version": "2022-06-28"
                },
                timeout=self.timeout
            )
            
            # Verify database access
            await self._verify_database()
            
            self._initialized = True
            logger.info("NotionVectorStore initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize NotionVectorStore: {e}")
            if isinstance(e, StorageError):
                raise
            raise StorageConnectionError("notion", str(e))
    
    async def _verify_database(self) -> None:
        """Verify that the database exists and is accessible."""
        try:
            response = await self._client.get(f"/databases/{self.database_id}")
            
            if response.status_code != 200:
                raise StorageConnectionError(
                    "notion", 
                    f"Cannot access database: {response.status_code} - {response.text}"
                )
            
            db_info = response.json()
            db_title = "Unknown"
            if db_info.get("title") and len(db_info["title"]) > 0:
                db_title = db_info["title"][0].get("plain_text", "Unknown")
            
            logger.info(f"Connected to Notion database: {db_title}")
            
        except httpx.RequestError as e:
            raise StorageConnectionError("notion", f"Network error: {e}")
    
    async def add_texts(
        self, 
        texts: List[str], 
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        embeddings: Optional[List[List[float]]] = None
    ) -> List[str]:
        """Add texts to the vector store."""
        if not self._initialized:
            await self.initialize()
        
        if not texts:
            return []
        
        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]
        
        # Ensure metadatas list has correct length
        if metadatas is None:
            metadatas = [{} for _ in texts]
        elif len(metadatas) != len(texts):
            raise ValueError("metadatas length must match texts length")
        
        # Ensure embeddings list has correct length if provided
        if embeddings is not None and len(embeddings) != len(texts):
            raise ValueError("embeddings length must match texts length")
        
        try:
            added_ids = []
            for i, text in enumerate(texts):
                text_id = ids[i]
                metadata = metadatas[i]
                embedding = embeddings[i] if embeddings else None
                
                # Create text chunk
                chunk = TextChunk(
                    id=text_id,
                    text=text,
                    document_id=metadata.get("document_id", "unknown"),
                    metadata=metadata,
                    embedding=embedding,
                    start_index=metadata.get("start_index", 0),
                    end_index=metadata.get("end_index", len(text))
                )
                
                await self._add_single_chunk(chunk)
                added_ids.append(text_id)
            
            logger.info(f"Successfully added {len(added_ids)} texts to Notion")
            return added_ids
            
        except Exception as e:
            logger.error(f"Failed to add texts to Notion: {e}")
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to add texts: {e}", operation="add_texts", provider="notion")
    
    async def add_documents(self, documents: List[Document]) -> List[str]:
        """Add documents to the vector store."""
        if not self._initialized:
            await self.initialize()
        
        if not documents:
            return []
        
        try:
            added_ids = []
            for document in documents:
                await self._add_single_document(document)
                added_ids.append(document.id)
            
            logger.info(f"Successfully added {len(added_ids)} documents to Notion")
            return added_ids
            
        except Exception as e:
            logger.error(f"Failed to add documents to Notion: {e}")
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to add documents: {e}", operation="add_documents", provider="notion")
    
    async def add_chunks(self, chunks: List[TextChunk]) -> List[str]:
        """Add text chunks to the vector store."""
        if not self._initialized:
            await self.initialize()
        
        if not chunks:
            return []
        
        try:
            added_ids = []
            for chunk in chunks:
                await self._add_single_chunk(chunk)
                added_ids.append(chunk.id)
            
            logger.info(f"Successfully added {len(added_ids)} chunks to Notion")
            return added_ids
            
        except Exception as e:
            logger.error(f"Failed to add chunks to Notion: {e}")
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to add chunks: {e}", operation="add_chunks", provider="notion")
    
    async def _add_single_document(self, document: Document) -> None:
        """Add a single document to Notion database."""
        # Prepare page properties for document
        properties = {
            "ID": {
                "title": [{"text": {"content": document.id}}]
            },
            "Type": {
                "select": {"name": "document"}
            },
            "Content": {
                "rich_text": [{"text": {"content": document.content[:self.max_text_length]}}]
            },
            "Document Type": {
                "select": {"name": document.type.value if isinstance(document.type, DocumentType) else str(document.type)}
            },
            "Source": {
                "rich_text": [{"text": {"content": document.source or ""}}]
            },
            "Created At": {
                "date": {"start": document.created_at.isoformat()}
            }
        }
        
        # Add metadata
        if document.metadata:
            properties["Metadata"] = {
                "rich_text": [{"text": {"content": json.dumps(document.metadata)[:self.max_text_length]}}]
            }
        
        await self._create_page(properties)
    
    async def _add_single_chunk(self, chunk: TextChunk) -> None:
        """Add a single chunk to Notion database."""
        # Prepare page properties for chunk
        properties = {
            "ID": {
                "title": [{"text": {"content": chunk.id}}]
            },
            "Type": {
                "select": {"name": "chunk"}
            },
            "Content": {
                "rich_text": [{"text": {"content": chunk.text[:self.max_text_length]}}]
            },
            "Document ID": {
                "rich_text": [{"text": {"content": chunk.document_id}}]
            },
            "Start Index": {
                "number": chunk.start_index
            },
            "End Index": {
                "number": chunk.end_index
            },
            "Created At": {
                "date": {"start": datetime.now().isoformat()}
            }
        }
        
        # Add embedding if available
        if chunk.embedding:
            embedding_json = json.dumps(chunk.embedding)
            if len(embedding_json) <= self.max_text_length:
                properties["Embedding"] = {
                    "rich_text": [{"text": {"content": embedding_json}}]
                }
            else:
                logger.warning(f"Embedding too large for chunk {chunk.id}, skipping")
        
        # Add metadata
        if chunk.metadata:
            metadata_json = json.dumps(chunk.metadata)
            if len(metadata_json) <= self.max_text_length:
                properties["Metadata"] = {
                    "rich_text": [{"text": {"content": metadata_json}}]
                }
            else:
                logger.warning(f"Metadata too large for chunk {chunk.id}, truncating")
                properties["Metadata"] = {
                    "rich_text": [{"text": {"content": metadata_json[:self.max_text_length]}}]
                }
        
        await self._create_page(properties)
    
    async def _create_page(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Create a page in the Notion database."""
        page_data = {
            "parent": {"database_id": self.database_id},
            "properties": properties
        }
        
        response = await self._client.post("/pages", json=page_data)
        
        if response.status_code != 200:
            raise StorageError(
                f"Failed to create Notion page: {response.status_code} - {response.text}",
                operation="create_page",
                provider="notion"
            )
        
        return response.json()
        
    @retry_with_backoff()
    async def get_document(self, document_id: str) -> Optional[Document]:
        """Get a document by ID."""
        if not self._initialized:
            await self.initialize()
        
        # Check cache first
        cache_key = f"document:{document_id}"
        if cache_key in self._page_cache:
            logger.debug(f"Cache hit for document {document_id}")
            return self._page_cache[cache_key]
        
        try:
            # Query for specific document
            query_data = {
                "filter": {
                    "and": [
                        {
                            "property": "ID",
                            "title": {"equals": document_id}
                        },
                        {
                            "property": "Type",
                            "select": {"equals": "document"}
                        }
                    ]
                }
            }
            
            response = await self._client.post(
                f"/databases/{self.database_id}/query",
                json=query_data
            )
            
            if response.status_code != 200:
                raise StorageError(
                    f"Failed to query Notion database: {response.status_code} - {response.text}",
                    operation="get_document",
                    provider="notion"
                )
            
            results = response.json().get("results", [])
            if not results:
                return None
            
            # Parse document from Notion page
            page = results[0]
            props = page.get("properties", {})
            
            # Extract document properties
            content = self._extract_rich_text_property(props, "Content")
            doc_type_str = self._extract_select_property(props, "Document Type")
            source = self._extract_rich_text_property(props, "Source")
            metadata_str = self._extract_rich_text_property(props, "Metadata")
            created_at_str = self._extract_date_property(props, "Created At")
            
            # Parse document type
            try:
                doc_type = DocumentType(doc_type_str) if doc_type_str else DocumentType.TEXT
            except ValueError:
                doc_type = DocumentType.TEXT
            
            # Parse metadata
            metadata = {}
            if metadata_str:
                try:
                    metadata = json.loads(metadata_str)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse metadata for document {document_id}")
            
            # Parse created_at
            created_at = datetime.now()
            if created_at_str:
                try:
                    created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                except ValueError:
                    logger.warning(f"Failed to parse created_at for document {document_id}")
            
            # Create document object
            document = Document(
                id=document_id,
                content=content or "",
                type=doc_type,
                source=source,
                metadata=metadata,
                created_at=created_at
            )
            
            # Cache the document
            self._page_cache[cache_key] = document
            
            return document
            
        except Exception as e:
            logger.error(f"Failed to get document from Notion: {e}")
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to get document: {e}", operation="get_document", provider="notion")
    
    @retry_with_backoff()
    async def get_chunk(self, chunk_id: str) -> Optional[TextChunk]:
        """Get a specific chunk by ID."""
        if not self._initialized:
            await self.initialize()
        
        # Check cache first
        cache_key = f"chunk:{chunk_id}"
        if cache_key in self._page_cache:
            logger.debug(f"Cache hit for chunk {chunk_id}")
            return self._page_cache[cache_key]
        
        try:
            # Query for specific chunk
            query_data = {
                "filter": {
                    "and": [
                        {
                            "property": "ID",
                            "title": {"equals": chunk_id}
                        },
                        {
                            "property": "Type",
                            "select": {"equals": "chunk"}
                        }
                    ]
                }
            }
            
            response = await self._client.post(
                f"/databases/{self.database_id}/query",
                json=query_data
            )
            
            if response.status_code != 200:
                raise StorageError(
                    f"Failed to query Notion database: {response.status_code} - {response.text}",
                    operation="get_chunk",
                    provider="notion"
                )
            
            results = response.json().get("results", [])
            if not results:
                return None
            
            # Parse chunk from Notion page
            page = results[0]
            props = page.get("properties", {})
            
            # Extract chunk properties
            text = self._extract_rich_text_property(props, "Content")
            document_id = self._extract_rich_text_property(props, "Document ID")
            start_index = self._extract_number_property(props, "Start Index")
            end_index = self._extract_number_property(props, "End Index")
            embedding_str = self._extract_rich_text_property(props, "Embedding")
            metadata_str = self._extract_rich_text_property(props, "Metadata")
            
            # Parse embedding
            embedding = None
            if embedding_str:
                try:
                    embedding = json.loads(embedding_str)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse embedding for chunk {chunk_id}")
            
            # Parse metadata
            metadata = {}
            if metadata_str:
                try:
                    metadata = json.loads(metadata_str)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse metadata for chunk {chunk_id}")
            
            # Create chunk object
            chunk = TextChunk(
                id=chunk_id,
                text=text or "",
                document_id=document_id or "unknown",
                metadata=metadata,
                embedding=embedding,
                start_index=start_index or 0,
                end_index=end_index or (len(text) if text else 0)
            )
            
            # Cache the chunk
            self._page_cache[cache_key] = chunk
            
            return chunk
            
        except Exception as e:
            logger.error(f"Failed to get chunk from Notion: {e}")
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to get chunk: {e}", operation="get_chunk", provider="notion")
    
    @retry_with_backoff()
    async def get_chunks(self, chunk_ids: List[str]) -> List[TextChunk]:
        """Get multiple chunks by their IDs."""
        if not self._initialized:
            await self.initialize()
        
        if not chunk_ids:
            return []
        
        try:
            chunks = []
            # Process in batches for better performance
            for i in range(0, len(chunk_ids), self.batch_size):
                batch_ids = chunk_ids[i:i+self.batch_size]
                batch_chunks = await self._get_chunks_batch(batch_ids)
                chunks.extend(batch_chunks)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to get chunks from Notion: {e}")
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to get chunks: {e}", operation="get_chunks", provider="notion")
    
    async def _get_chunks_batch(self, chunk_ids: List[str]) -> List[TextChunk]:
        """Get a batch of chunks by their IDs."""
        chunks = []
        
        # Check cache first for each chunk
        missing_ids = []
        for chunk_id in chunk_ids:
            cache_key = f"chunk:{chunk_id}"
            if cache_key in self._page_cache:
                logger.debug(f"Cache hit for chunk {chunk_id}")
                chunks.append(self._page_cache[cache_key])
            else:
                missing_ids.append(chunk_id)
        
        if not missing_ids:
            return chunks
        
        # Query for missing chunks
        query_data = {
            "filter": {
                "and": [
                    {
                        "property": "Type",
                        "select": {"equals": "chunk"}
                    },
                    {
                        "or": [
                            {"property": "ID", "title": {"equals": chunk_id}}
                            for chunk_id in missing_ids
                        ]
                    }
                ]
            }
        }
        
        response = await self._client.post(
            f"/databases/{self.database_id}/query",
            json=query_data
        )
        
        if response.status_code != 200:
            raise StorageError(
                f"Failed to query Notion database: {response.status_code} - {response.text}",
                operation="get_chunks_batch",
                provider="notion"
            )
        
        results = response.json().get("results", [])
        
        # Parse chunks from Notion pages
        for page in results:
            props = page.get("properties", {})
            
            # Extract chunk ID
            chunk_id = self._extract_title_property(props, "ID")
            if not chunk_id:
                continue
            
            # Extract chunk properties
            text = self._extract_rich_text_property(props, "Content")
            document_id = self._extract_rich_text_property(props, "Document ID")
            start_index = self._extract_number_property(props, "Start Index")
            end_index = self._extract_number_property(props, "End Index")
            embedding_str = self._extract_rich_text_property(props, "Embedding")
            metadata_str = self._extract_rich_text_property(props, "Metadata")
            
            # Parse embedding
            embedding = None
            if embedding_str:
                try:
                    embedding = json.loads(embedding_str)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse embedding for chunk {chunk_id}")
            
            # Parse metadata
            metadata = {}
            if metadata_str:
                try:
                    metadata = json.loads(metadata_str)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse metadata for chunk {chunk_id}")
            
            # Create chunk object
            chunk = TextChunk(
                id=chunk_id,
                text=text or "",
                document_id=document_id or "unknown",
                metadata=metadata,
                embedding=embedding,
                start_index=start_index or 0,
                end_index=end_index or (len(text) if text else 0)
            )
            
            # Cache the chunk
            cache_key = f"chunk:{chunk_id}"
            self._page_cache[cache_key] = chunk
            
            chunks.append(chunk)
        
        return chunks
    
    @retry_with_backoff()
    async def similarity_search(
        self, 
        query: str, 
        k: int = 5, 
        filter: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ) -> List[Tuple[TextChunk, float]]:
        """
        Search for similar texts using semantic similarity.
        
        Note: This implementation performs a basic search since Notion doesn't have
        native vector search capabilities. For production use, consider using a
        dedicated vector database alongside Notion.
        """
        if not self._initialized:
            await self.initialize()
        
        # Generate cache key
        cache_key = f"similarity:{query}:{k}:{json.dumps(filter) if filter else 'none'}"
        if cache_key in self._query_cache:
            logger.debug(f"Cache hit for similarity search: {query}")
            return self._query_cache[cache_key]
        
        try:
            # Since Notion doesn't support vector search natively,
            # we'll retrieve chunks and perform similarity calculation in memory
            
            # First, get all chunks (with filter if provided)
            chunks = await self._get_filtered_chunks(filter)
            
            # If no chunks found, return empty list
            if not chunks:
                return []
            
            # If embedding is provided, use it directly
            # Otherwise, we'd need an embedding model to convert query to vector
            # For this implementation, we'll use a simple text matching as fallback
            if embedding:
                # Calculate similarity scores
                results = []
                for chunk in chunks:
                    if chunk.embedding:
                        # Calculate cosine similarity
                        similarity = self._cosine_similarity(embedding, chunk.embedding)
                        results.append((chunk, similarity))
                
                # Sort by similarity (descending)
                results.sort(key=lambda x: x[1], reverse=True)
                
                # Return top k results
                top_results = results[:k]
                
                # Cache results
                self._query_cache[cache_key] = top_results
                
                return top_results
            else:
                # Fallback to keyword search if no embedding provided
                return await self.keyword_search(query, k, filter)
            
        except Exception as e:
            logger.error(f"Failed to perform similarity search: {e}")
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to perform similarity search: {e}", operation="similarity_search", provider="notion")
    
    @retry_with_backoff()
    async def keyword_search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[TextChunk, float]]:
        """Search for texts using keyword matching."""
        if not self._initialized:
            await self.initialize()
        
        # Generate cache key
        cache_key = f"keyword:{query}:{k}:{json.dumps(filter) if filter else 'none'}"
        if cache_key in self._query_cache:
            logger.debug(f"Cache hit for keyword search: {query}")
            return self._query_cache[cache_key]
        
        try:
            # Prepare Notion search query
            search_data = {
                "query": query,
                "filter": {
                    "property": "object",
                    "value": "page"
                },
                "sort": {
                    "direction": "descending",
                    "timestamp": "last_edited_time"
                }
            }
            
            # Add database filter
            search_data["filter"] = {
                "value": "page",
                "property": "object"
            }
            
            response = await self._client.post(
                "/search",
                json=search_data
            )
            
            if response.status_code != 200:
                raise StorageError(
                    f"Failed to search Notion: {response.status_code} - {response.text}",
                    operation="keyword_search",
                    provider="notion"
                )
            
            results = response.json().get("results", [])
            
            # Filter results to only include pages from our database
            filtered_results = [
                page for page in results 
                if page.get("parent", {}).get("database_id") == self.database_id
                and page.get("properties", {}).get("Type", {}).get("select", {}).get("name") == "chunk"
            ]
            
            # Apply additional filters if provided
            if filter:
                filtered_results = self._apply_filters(filtered_results, filter)
            
            # Parse chunks from search results
            chunks_with_scores = []
            for page in filtered_results[:k]:
                props = page.get("properties", {})
                
                # Extract chunk ID
                chunk_id = self._extract_title_property(props, "ID")
                if not chunk_id:
                    continue
                
                # Get the chunk (this will use cache if available)
                chunk = await self.get_chunk(chunk_id)
                if chunk:
                    # Calculate a simple relevance score based on position in results
                    score = 1.0 - (filtered_results.index(page) / len(filtered_results))
                    chunks_with_scores.append((chunk, score))
            
            # Cache results
            self._query_cache[cache_key] = chunks_with_scores
            
            return chunks_with_scores
            
        except Exception as e:
            logger.error(f"Failed to perform keyword search: {e}")
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to perform keyword search: {e}", operation="keyword_search", provider="notion")
    
    @retry_with_backoff()
    async def delete(self, ids: List[str]) -> bool:
        """Delete texts from the vector store by IDs."""
        if not self._initialized:
            await self.initialize()
        
        if not ids:
            return True
        
        try:
            success = True
            for id in ids:
                # Find the page with this ID
                page_id = await self._find_page_id_by_content_id(id)
                if page_id:
                    # Delete the page
                    success = success and await self._delete_page(page_id)
                    
                    # Remove from cache if present
                    doc_cache_key = f"document:{id}"
                    chunk_cache_key = f"chunk:{id}"
                    if doc_cache_key in self._page_cache:
                        del self._page_cache[doc_cache_key]
                    if chunk_cache_key in self._page_cache:
                        del self._page_cache[chunk_cache_key]
            
            # Invalidate query cache since content has changed
            self._query_cache.clear()
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete items from Notion: {e}")
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to delete items: {e}", operation="delete", provider="notion")
    
    @retry_with_backoff()
    async def delete_document(self, document_id: str) -> bool:
        """Delete a document and all its chunks."""
        if not self._initialized:
            await self.initialize()
        
        try:
            # First, find and delete the document page
            doc_page_id = await self._find_page_id_by_content_id(document_id, "document")
            doc_deleted = False
            if doc_page_id:
                doc_deleted = await self._delete_page(doc_page_id)
                
                # Remove from cache if present
                doc_cache_key = f"document:{document_id}"
                if doc_cache_key in self._page_cache:
                    del self._page_cache[doc_cache_key]
            
            # Next, find and delete all chunks for this document
            query_data = {
                "filter": {
                    "and": [
                        {
                            "property": "Type",
                            "select": {"equals": "chunk"}
                        },
                        {
                            "property": "Document ID",
                            "rich_text": {"equals": document_id}
                        }
                    ]
                }
            }
            
            response = await self._client.post(
                f"/databases/{self.database_id}/query",
                json=query_data
            )
            
            if response.status_code != 200:
                raise StorageError(
                    f"Failed to query Notion database: {response.status_code} - {response.text}",
                    operation="delete_document",
                    provider="notion"
                )
            
            results = response.json().get("results", [])
            
            # Delete each chunk page
            chunks_deleted = True
            for page in results:
                page_id = page.get("id")
                if page_id:
                    chunk_deleted = await self._delete_page(page_id)
                    chunks_deleted = chunks_deleted and chunk_deleted
                    
                    # Extract chunk ID to remove from cache
                    props = page.get("properties", {})
                    chunk_id = self._extract_title_property(props, "ID")
                    if chunk_id:
                        chunk_cache_key = f"chunk:{chunk_id}"
                        if chunk_cache_key in self._page_cache:
                            del self._page_cache[chunk_cache_key]
            
            # Invalidate query cache since content has changed
            self._query_cache.clear()
            
            return doc_deleted and chunks_deleted
            
        except Exception as e:
            logger.error(f"Failed to delete document from Notion: {e}")
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to delete document: {e}", operation="delete_document", provider="notion")
    
    @retry_with_backoff()
    async def update_metadata(self, id: str, metadata: Dict[str, Any]) -> bool:
        """Update metadata for a specific text or document."""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Find the page with this ID
            page_id = await self._find_page_id_by_content_id(id)
            if not page_id:
                return False
            
            # Get current page to determine if it's a document or chunk
            response = await self._client.get(f"/pages/{page_id}")
            
            if response.status_code != 200:
                raise StorageError(
                    f"Failed to get Notion page: {response.status_code} - {response.text}",
                    operation="update_metadata",
                    provider="notion"
                )
            
            page = response.json()
            props = page.get("properties", {})
            page_type = self._extract_select_property(props, "Type")
            
            # Get current metadata
            current_metadata_str = self._extract_rich_text_property(props, "Metadata")
            current_metadata = {}
            if current_metadata_str:
                try:
                    current_metadata = json.loads(current_metadata_str)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse metadata for {id}")
            
            # Merge with new metadata
            merged_metadata = {**current_metadata, **metadata}
            metadata_json = json.dumps(merged_metadata)
            
            # Update page properties
            update_data = {
                "properties": {
                    "Metadata": {
                        "rich_text": [{"text": {"content": metadata_json[:self.max_text_length]}}]
                    }
                }
            }
            
            update_response = await self._client.patch(
                f"/pages/{page_id}",
                json=update_data
            )
            
            if update_response.status_code != 200:
                raise StorageError(
                    f"Failed to update Notion page: {update_response.status_code} - {update_response.text}",
                    operation="update_metadata",
                    provider="notion"
                )
            
            # Update cache if present
            cache_key = f"{page_type.lower()}:{id}" if page_type else f"chunk:{id}"
            if cache_key in self._page_cache:
                item = self._page_cache[cache_key]
                if hasattr(item, "metadata"):
                    item.metadata = merged_metadata
                    self._page_cache[cache_key] = item
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update metadata in Notion: {e}")
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to update metadata: {e}", operation="update_metadata", provider="notion")
    
    @retry_with_backoff()
    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        if not self._initialized:
            await self.initialize()
        
        try:
            stats = {
                "document_count": 0,
                "chunk_count": 0,
                "last_updated": datetime.now().isoformat()
            }
            
            # Count documents
            doc_query = {
                "filter": {
                    "property": "Type",
                    "select": {"equals": "document"}
                }
            }
            
            doc_response = await self._client.post(
                f"/databases/{self.database_id}/query",
                json=doc_query
            )
            
            if doc_response.status_code == 200:
                stats["document_count"] = len(doc_response.json().get("results", []))
            
            # Count chunks
            chunk_query = {
                "filter": {
                    "property": "Type",
                    "select": {"equals": "chunk"}
                }
            }
            
            chunk_response = await self._client.post(
                f"/databases/{self.database_id}/query",
                json=chunk_query
            )
            
            if chunk_response.status_code == 200:
                stats["chunk_count"] = len(chunk_response.json().get("results", []))
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get stats from Notion: {e}")
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to get stats: {e}", operation="get_stats", provider="notion")
    
    @retry_with_backoff()
    async def clear(self) -> bool:
        """Clear all data from the vector store."""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Query all pages in the database
            response = await self._client.post(
                f"/databases/{self.database_id}/query",
                json={}
            )
            
            if response.status_code != 200:
                raise StorageError(
                    f"Failed to query Notion database: {response.status_code} - {response.text}",
                    operation="clear",
                    provider="notion"
                )
            
            results = response.json().get("results", [])
            
            # Delete each page
            success = True
            for page in results:
                page_id = page.get("id")
                if page_id:
                    page_deleted = await self._delete_page(page_id)
                    success = success and page_deleted
            
            # Clear caches
            self._page_cache.clear()
            self._query_cache.clear()
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to clear Notion database: {e}")
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to clear database: {e}", operation="clear", provider="notion")
    
    async def close(self) -> None:
        """Close the vector store connection and cleanup resources."""
        if self._client:
            await self._client.aclose()
            self._client = None
        
        self._initialized = False
        logger.info("NotionVectorStore connection closed")
    
    # Helper methods
    
    async def _find_page_id_by_content_id(self, content_id: str, content_type: Optional[str] = None) -> Optional[str]:
        """Find a Notion page ID by content ID."""
        query_filters = [
            {
                "property": "ID",
                "title": {"equals": content_id}
            }
        ]
        
        if content_type:
            query_filters.append({
                "property": "Type",
                "select": {"equals": content_type}
            })
        
        query_data = {
            "filter": {
                "and": query_filters
            }
        }
        
        response = await self._client.post(
            f"/databases/{self.database_id}/query",
            json=query_data
        )
        
        if response.status_code != 200:
            raise StorageError(
                f"Failed to query Notion database: {response.status_code} - {response.text}",
                operation="find_page_id",
                provider="notion"
            )
        
        results = response.json().get("results", [])
        if not results:
            return None
        
        return results[0].get("id")
    
    async def _delete_page(self, page_id: str) -> bool:
        """Delete a Notion page by ID."""
        # Notion API uses "archive" instead of delete
        update_data = {
            "archived": True
        }
        
        response = await self._client.patch(
            f"/pages/{page_id}",
            json=update_data
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to delete Notion page: {response.status_code} - {response.text}")
            return False
        
        return True
    
    async def _get_filtered_chunks(self, filter: Optional[Dict[str, Any]] = None) -> List[TextChunk]:
        """Get chunks with optional filtering."""
        query_data = {
            "filter": {
                "property": "Type",
                "select": {"equals": "chunk"}
            }
        }
        
        # Add additional filters if provided
        if filter:
            notion_filter = self._convert_filter_to_notion(filter)
            if notion_filter:
                query_data["filter"] = {
                    "and": [
                        query_data["filter"],
                        notion_filter
                    ]
                }
        
        response = await self._client.post(
            f"/databases/{self.database_id}/query",
            json=query_data
        )
        
        if response.status_code != 200:
            raise StorageError(
                f"Failed to query Notion database: {response.status_code} - {response.text}",
                operation="get_filtered_chunks",
                provider="notion"
            )
        
        results = response.json().get("results", [])
        
        # Parse chunks from results
        chunks = []
        for page in results:
            props = page.get("properties", {})
            
            # Extract chunk ID
            chunk_id = self._extract_title_property(props, "ID")
            if not chunk_id:
                continue
            
            # Get the chunk (this will use cache if available)
            chunk = await self.get_chunk(chunk_id)
            if chunk:
                chunks.append(chunk)
        
        return chunks
    
    def _convert_filter_to_notion(self, filter: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a generic filter to Notion filter format."""
        # This is a simplified implementation
        # In a real implementation, you would handle more complex filters
        notion_filter = {}
        
        if "document_id" in filter:
            notion_filter = {
                "property": "Document ID",
                "rich_text": {"equals": filter["document_id"]}
            }
        
        # Add more filter conversions as needed
        
        return notion_filter
    
    def _apply_filters(self, results: List[Dict[str, Any]], filter: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply filters to search results."""
        filtered_results = results
        
        # Filter by document_id if provided
        if "document_id" in filter:
            filtered_results = [
                page for page in filtered_results
                if self._extract_rich_text_property(page.get("properties", {}), "Document ID") == filter["document_id"]
            ]
        
        # Add more filters as needed
        
        return filtered_results
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        
        if magnitude1 * magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    # Property extraction helpers
    
    def _extract_title_property(self, props: Dict[str, Any], name: str) -> Optional[str]:
        """Extract a title property from Notion page properties."""
        if name not in props:
            return None
        
        title = props[name].get("title", [])
        if not title:
            return None
        
        return title[0].get("text", {}).get("content")
    
    def _extract_rich_text_property(self, props: Dict[str, Any], name: str) -> Optional[str]:
        """Extract a rich text property from Notion page properties."""
        if name not in props:
            return None
        
        rich_text = props[name].get("rich_text", [])
        if not rich_text:
            return None
        
        return rich_text[0].get("text", {}).get("content")
    
    def _extract_select_property(self, props: Dict[str, Any], name: str) -> Optional[str]:
        """Extract a select property from Notion page properties."""
        if name not in props:
            return None
        
        select = props[name].get("select")
        if not select:
            return None
        
        return select.get("name")
    
    def _extract_number_property(self, props: Dict[str, Any], name: str) -> Optional[int]:
        """Extract a number property from Notion page properties."""
        if name not in props:
            return None
        
        return props[name].get("number")
    
    def _extract_date_property(self, props: Dict[str, Any], name: str) -> Optional[str]:
        """Extract a date property from Notion page properties."""
        if name not in props:
            return None
        
        date = props[name].get("date")
        if not date:
            return None
        
        return date.get("start")