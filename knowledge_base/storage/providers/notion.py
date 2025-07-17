"""Notion storage provider for knowledge base."""

import logging
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx

from ..base import BaseVectorStore
from ...core.types import Chunk, Vector, Metadata
from ...core.exceptions import StorageError

logger = logging.getLogger(__name__)


class NotionVectorStore(BaseVectorStore):
    """
    Notion-based vector store implementation.
    
    This provider stores chunks and their metadata in Notion database,
    with vector embeddings stored as JSON in properties.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Notion vector store."""
        super().__init__(config)
        
        # Notion configuration
        self.api_key = config.get("notion_api_key")
        self.database_id = config.get("notion_database_id")
        self.base_url = "https://api.notion.com/v1"
        
        # HTTP client
        self._client = None
        
        # Validation
        if not self.api_key:
            raise StorageError("Notion API key is required")
        if not self.database_id:
            raise StorageError("Notion database ID is required")
        
        logger.info(f"NotionVectorStore initialized with database: {self.database_id}")
    
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
                timeout=30.0
            )
            
            # Verify database access
            await self._verify_database()
            
            self._initialized = True
            logger.info("NotionVectorStore initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize NotionVectorStore: {e}")
            raise StorageError(f"Notion initialization failed: {e}")
    
    async def _verify_database(self) -> None:
        """Verify that the database exists and is accessible."""
        try:
            response = await self._client.get(f"/databases/{self.database_id}")
            
            if response.status_code != 200:
                raise StorageError(f"Cannot access Notion database: {response.status_code} - {response.text}")
            
            db_info = response.json()
            logger.info(f"Connected to Notion database: {db_info.get('title', [{}])[0].get('plain_text', 'Unknown')}")
            
        except httpx.RequestError as e:
            raise StorageError(f"Network error accessing Notion database: {e}")
    
    async def add_chunks(self, chunks: List[Chunk]) -> bool:
        """Add chunks to Notion database."""
        if not self._initialized:
            await self.initialize()
        
        try:
            for chunk in chunks:
                await self._add_single_chunk(chunk)
            
            logger.info(f"Successfully added {len(chunks)} chunks to Notion")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add chunks to Notion: {e}")
            raise StorageError(f"Failed to add chunks: {e}")
    
    async def _add_single_chunk(self, chunk: Chunk) -> None:
        """Add a single chunk to Notion database."""
        # Prepare page properties
        properties = {
            "Chunk ID": {
                "title": [
                    {
                        "text": {
                            "content": chunk.id
                        }
                    }
                ]
            },
            "Document ID": {
                "rich_text": [
                    {
                        "text": {
                            "content": chunk.document_id
                        }
                    }
                ]
            },
            "Text": {
                "rich_text": [
                    {
                        "text": {
                            "content": chunk.text[:2000]  # Notion has text limits
                        }
                    }
                ]
            },
            "Start Index": {
                "number": chunk.start_index
            },
            "End Index": {
                "number": chunk.end_index
            },
            "Created": {
                "date": {
                    "start": datetime.now().isoformat()
                }
            }
        }
        
        # Add embedding if available
        if chunk.embedding:
            properties["Embedding"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": json.dumps(chunk.embedding)[:2000]  # Store as JSON string
                        }
                    }
                ]
            }
        
        # Add metadata
        if chunk.metadata:
            properties["Metadata"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": json.dumps(chunk.metadata)[:2000]
                        }
                    }
                ]
            }
        
        # Create page in database
        page_data = {
            "parent": {
                "database_id": self.database_id
            },
            "properties": properties
        }
        
        response = await self._client.post("/pages", json=page_data)
        
        if response.status_code != 200:
            raise StorageError(f"Failed to create Notion page: {response.status_code} - {response.text}")
    
    async def search_similar(
        self, 
        query_vector: Vector, 
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors in Notion database.
        
        Note: This is a simplified implementation that retrieves all chunks
        and computes similarity in memory. For production use, consider
        using a dedicated vector database alongside Notion for metadata.
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Retrieve all chunks from Notion
            all_chunks = await self._get_all_chunks()
            
            # Compute similarities
            results = []
            for chunk_data in all_chunks:
                chunk = chunk_data["chunk"]
                if chunk.embedding:
                    similarity = self._compute_cosine_similarity(query_vector, chunk.embedding)
                    
                    if similarity >= min_score:
                        results.append({
                            "chunk": chunk,
                            "score": similarity,
                            "metadata": chunk.metadata
                        })
            
            # Sort by similarity and return top_k
            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Failed to search similar chunks in Notion: {e}")
            raise StorageError(f"Search failed: {e}")
    
    async def _get_all_chunks(self) -> List[Dict[str, Any]]:
        """Retrieve all chunks from Notion database."""
        chunks = []
        has_more = True
        start_cursor = None
        
        while has_more:
            # Query database
            query_data = {
                "page_size": 100
            }
            
            if start_cursor:
                query_data["start_cursor"] = start_cursor
            
            response = await self._client.post(
                f"/databases/{self.database_id}/query",
                json=query_data
            )
            
            if response.status_code != 200:
                raise StorageError(f"Failed to query Notion database: {response.status_code} - {response.text}")
            
            data = response.json()
            
            # Process results
            for page in data.get("results", []):
                chunk = self._page_to_chunk(page)
                if chunk:
                    chunks.append({"chunk": chunk, "page_id": page["id"]})
            
            # Check for more pages
            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor")
        
        return chunks
    
    def _page_to_chunk(self, page: Dict[str, Any]) -> Optional[Chunk]:
        """Convert Notion page to Chunk object."""
        try:
            properties = page.get("properties", {})
            
            # Extract basic properties
            chunk_id = self._extract_text_property(properties.get("Chunk ID"))
            document_id = self._extract_text_property(properties.get("Document ID"))
            text = self._extract_text_property(properties.get("Text"))
            
            if not chunk_id or not document_id or not text:
                return None
            
            # Extract numeric properties
            start_index = properties.get("Start Index", {}).get("number", 0)
            end_index = properties.get("End Index", {}).get("number", 0)
            
            # Extract embedding
            embedding = None
            embedding_text = self._extract_text_property(properties.get("Embedding"))
            if embedding_text:
                try:
                    embedding = json.loads(embedding_text)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse embedding for chunk {chunk_id}")
            
            # Extract metadata
            metadata = {}
            metadata_text = self._extract_text_property(properties.get("Metadata"))
            if metadata_text:
                try:
                    metadata = json.loads(metadata_text)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse metadata for chunk {chunk_id}")
            
            return Chunk(
                id=chunk_id,
                document_id=document_id,
                text=text,
                embedding=embedding,
                metadata=metadata,
                start_index=start_index,
                end_index=end_index
            )
            
        except Exception as e:
            logger.error(f"Failed to convert Notion page to chunk: {e}")
            return None
    
    def _extract_text_property(self, prop: Optional[Dict[str, Any]]) -> Optional[str]:
        """Extract text content from Notion property."""
        if not prop:
            return None
        
        # Handle title properties
        if "title" in prop and prop["title"]:
            return prop["title"][0].get("text", {}).get("content")
        
        # Handle rich_text properties
        if "rich_text" in prop and prop["rich_text"]:
            return prop["rich_text"][0].get("text", {}).get("content")
        
        return None
    
    def _compute_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    async def get_chunk(self, chunk_id: str) -> Optional[Chunk]:
        """Get a specific chunk by ID."""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Query for specific chunk
            query_data = {
                "filter": {
                    "property": "Chunk ID",
                    "title": {
                        "equals": chunk_id
                    }
                }
            }
            
            response = await self._client.post(
                f"/databases/{self.database_id}/query",
                json=query_data
            )
            
            if response.status_code != 200:
                raise StorageError(f"Failed to query chunk: {response.status_code} - {response.text}")
            
            data = response.json()
            results = data.get("results", [])
            
            if results:
                return self._page_to_chunk(results[0])
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get chunk {chunk_id}: {e}")
            raise StorageError(f"Failed to get chunk: {e}")
    
    async def delete_chunks(self, chunk_ids: List[str]) -> bool:
        """Delete chunks by IDs."""
        if not self._initialized:
            await self.initialize()
        
        try:
            for chunk_id in chunk_ids:
                await self._delete_chunk_by_id(chunk_id)
            
            logger.info(f"Successfully deleted {len(chunk_ids)} chunks from Notion")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete chunks: {e}")
            raise StorageError(f"Failed to delete chunks: {e}")
    
    async def _delete_chunk_by_id(self, chunk_id: str) -> None:
        """Delete a single chunk by ID."""
        # First find the page
        query_data = {
            "filter": {
                "property": "Chunk ID",
                "title": {
                    "equals": chunk_id
                }
            }
        }
        
        response = await self._client.post(
            f"/databases/{self.database_id}/query",
            json=query_data
        )
        
        if response.status_code != 200:
            raise StorageError(f"Failed to find chunk for deletion: {response.status_code} - {response.text}")
        
        data = response.json()
        results = data.get("results", [])
        
        # Delete found pages
        for page in results:
            page_id = page["id"]
            
            # Archive the page (Notion's way of "deleting")
            update_data = {
                "archived": True
            }
            
            response = await self._client.patch(f"/pages/{page_id}", json=update_data)
            
            if response.status_code != 200:
                raise StorageError(f"Failed to delete page: {response.status_code} - {response.text}")
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete all chunks belonging to a document."""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Find all chunks for the document
            query_data = {
                "filter": {
                    "property": "Document ID",
                    "rich_text": {
                        "equals": document_id
                    }
                }
            }
            
            response = await self._client.post(
                f"/databases/{self.database_id}/query",
                json=query_data
            )
            
            if response.status_code != 200:
                raise StorageError(f"Failed to find document chunks: {response.status_code} - {response.text}")
            
            data = response.json()
            results = data.get("results", [])
            
            # Delete all found pages
            for page in results:
                page_id = page["id"]
                
                update_data = {
                    "archived": True
                }
                
                response = await self._client.patch(f"/pages/{page_id}", json=update_data)
                
                if response.status_code != 200:
                    logger.warning(f"Failed to delete page {page_id}: {response.status_code}")
            
            logger.info(f"Successfully deleted {len(results)} chunks for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            raise StorageError(f"Failed to delete document: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get total count
            response = await self._client.post(
                f"/databases/{self.database_id}/query",
                json={"page_size": 1}
            )
            
            if response.status_code != 200:
                raise StorageError(f"Failed to get stats: {response.status_code} - {response.text}")
            
            # Note: Notion doesn't provide total count directly
            # This is a simplified implementation
            return {
                "provider": "notion",
                "database_id": self.database_id,
                "status": "connected",
                "note": "Notion API doesn't provide total count efficiently"
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                "provider": "notion",
                "status": "error",
                "error": str(e)
            }
    
    async def clear(self) -> bool:
        """Clear all data from the database."""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get all pages and archive them
            all_chunks = await self._get_all_chunks()
            
            for chunk_data in all_chunks:
                page_id = chunk_data["page_id"]
                
                update_data = {
                    "archived": True
                }
                
                response = await self._client.patch(f"/pages/{page_id}", json=update_data)
                
                if response.status_code != 200:
                    logger.warning(f"Failed to archive page {page_id}: {response.status_code}")
            
            logger.info(f"Successfully cleared {len(all_chunks)} chunks from Notion database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear database: {e}")
            raise StorageError(f"Failed to clear database: {e}")
    
    async def close(self) -> None:
        """Close the Notion client."""
        if self._client:
            await self._client.aclose()
            self._client = None
        
        self._initialized = False
        logger.info("NotionVectorStore closed")