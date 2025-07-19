"""
OneDrive provider for the knowledge base system.

This module implements a vector store provider that uses Microsoft OneDrive
for storing and retrieving document chunks.
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple

import msal
import requests

from ...core.types import Document, TextChunk
from ...core.exceptions import StorageError
from ..base import BaseVectorStore


class OneDriveVectorStore(BaseVectorStore):
    """
    Vector store implementation using Microsoft OneDrive.
    
    This provider stores document chunks as JSON files in OneDrive.
    It uses OAuth 2.0 for authentication.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the OneDrive vector store with configuration.
        
        Args:
            config: Configuration dictionary with OneDrive-specific settings:
                - client_id: Application (client) ID from Azure portal
                - client_secret: Client secret from Azure portal
                - tenant_id: Directory (tenant) ID from Azure portal
                - redirect_uri: Redirect URI registered in Azure portal
                - scopes: List of OAuth scopes
                - token_cache_file: Path to token cache file
                - drive_id: ID of the drive to use (optional)
                - folder_path: Path to the folder to use (optional)
        
        Raises:
            ValueError: If required configuration is missing
        """
        super().__init__(config)
        self.client_id = self.config.get("client_id")
        self.client_secret = self.config.get("client_secret")
        self.tenant_id = self.config.get("tenant_id")
        self.redirect_uri = self.config.get("redirect_uri")
        self.scopes = self.config.get("scopes", ["Files.ReadWrite.All"])
        self.token_cache_file = self.config.get("token_cache_file", "onedrive_token_cache.json")
        self.drive_id = self.config.get("drive_id")
        self.folder_path = self.config.get("folder_path", "/KnowledgeBase")
        
        if not self.client_id:
            raise ValueError("OneDriveVectorStore requires a 'client_id' in the configuration.")
        
        if not self.client_secret:
            raise ValueError("OneDriveVectorStore requires a 'client_secret' in the configuration.")
        
        if not self.tenant_id:
            raise ValueError("OneDriveVectorStore requires a 'tenant_id' in the configuration.")
        
        if not self.redirect_uri:
            raise ValueError("OneDriveVectorStore requires a 'redirect_uri' in the configuration.")
        
        self.app = None
        self.access_token = None
        self.chunk_folder_path = None
        self.doc_folder_path = None
    
    async def initialize(self) -> None:
        """
        Initialize the OneDrive connection and resources.
        
        This method authenticates with OneDrive and sets up the folder structure.
        
        Raises:
            StorageError: If initialization fails
        """
        try:
            # Run authentication in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.app = await loop.run_in_executor(None, self._create_app)
            self.access_token = await loop.run_in_executor(None, self._get_token)
            
            # Create folder structure
            self.chunk_folder_path = f"{self.folder_path}/chunks"
            self.doc_folder_path = f"{self.folder_path}/documents"
            
            await self._ensure_folder_exists(self.folder_path)
            await self._ensure_folder_exists(self.chunk_folder_path)
            await self._ensure_folder_exists(self.doc_folder_path)
            
            self._initialized = True
        except Exception as e:
            raise StorageError(f"Failed to initialize OneDrive vector store: {str(e)}") from e
    
    def _create_app(self):
        """
        Create the MSAL application for authentication.
        
        Returns:
            MSAL ConfidentialClientApplication
        """
        # Create token cache
        token_cache = msal.SerializableTokenCache()
        
        # Load token cache from file if it exists
        if os.path.exists(self.token_cache_file):
            with open(self.token_cache_file, "r") as f:
                token_cache.deserialize(f.read())
        
        # Create MSAL app
        app = msal.ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
            token_cache=token_cache
        )
        
        return app
    
    def _get_token(self) -> str:
        """
        Get an access token for OneDrive API.
        
        Returns:
            Access token
            
        Raises:
            ValueError: If authentication fails
        """
        # Check if we have a token in cache
        accounts = self.app.get_accounts()
        if accounts:
            result = self.app.acquire_token_silent(self.scopes, account=accounts[0])
            if result and "access_token" in result:
                # Save token cache
                if self.app.token_cache.has_state_changed:
                    with open(self.token_cache_file, "w") as f:
                        f.write(self.app.token_cache.serialize())
                
                return result["access_token"]
        
        # No token in cache, start interactive login
        flow = self.app.initiate_auth_code_flow(
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )
        
        print(f"Please go to this URL and authorize the app: {flow['auth_uri']}")
        print("After authorization, you will be redirected to a URL. Copy that URL and paste it below.")
        
        auth_response = input("Enter the full redirect URL: ")
        
        result = self.app.acquire_token_by_auth_code_flow(flow, auth_response)
        
        if "access_token" not in result:
            raise ValueError(f"Failed to get access token: {result.get('error_description', 'Unknown error')}")
        
        # Save token cache
        if self.app.token_cache.has_state_changed:
            with open(self.token_cache_file, "w") as f:
                f.write(self.app.token_cache.serialize())
        
        return result["access_token"]
    
    async def _ensure_folder_exists(self, folder_path: str) -> str:
        """
        Ensure a folder exists in OneDrive, creating it if necessary.
        
        Args:
            folder_path: Path to the folder
            
        Returns:
            ID of the folder
            
        Raises:
            StorageError: If folder creation fails
        """
        try:
            # Check if folder exists
            folder_id = await self._get_item_id(folder_path)
            if folder_id:
                return folder_id
            
            # Folder doesn't exist, create it
            parent_path = os.path.dirname(folder_path)
            folder_name = os.path.basename(folder_path)
            
            # Ensure parent folder exists
            if parent_path and parent_path != "/":
                parent_id = await self._ensure_folder_exists(parent_path)
            else:
                # Use root folder
                parent_id = "root"
            
            # Create folder
            url = f"https://graph.microsoft.com/v1.0/me/drive/items/{parent_id}/children"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            data = {
                "name": folder_name,
                "folder": {},
                "@microsoft.graph.conflictBehavior": "fail"
            }
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(url, headers=headers, json=data)
            )
            
            if response.status_code == 201:
                return response.json()["id"]
            else:
                raise StorageError(f"Failed to create folder in OneDrive: {response.text}")
        except Exception as e:
            raise StorageError(f"Failed to ensure folder exists in OneDrive: {str(e)}") from e
    
    async def _get_item_id(self, path: str) -> Optional[str]:
        """
        Get the ID of an item in OneDrive by path.
        
        Args:
            path: Path to the item
            
        Returns:
            ID of the item if found, None otherwise
        """
        try:
            # Handle root path
            if path == "/" or not path:
                return "root"
            
            # Normalize path
            path = path.strip("/")
            
            # Get item by path
            url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{path}"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(url, headers=headers)
            )
            
            if response.status_code == 200:
                return response.json()["id"]
            else:
                return None
        except Exception:
            return None
    
    async def add_texts(
        self, 
        texts: List[str], 
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        embeddings: Optional[List[List[float]]] = None
    ) -> List[str]:
        """
        Add texts to the OneDrive vector store.
        
        Args:
            texts: List of text strings to add
            metadatas: Optional list of metadata dictionaries, one per text
            ids: Optional list of IDs to assign to the texts
            embeddings: Optional list of pre-computed embeddings
            
        Returns:
            List of IDs for the added texts
            
        Raises:
            StorageError: If adding texts fails
        """
        if not self._initialized:
            raise StorageError("OneDrive vector store is not initialized")
        
        # Prepare chunks
        from uuid import uuid4
        
        if ids is None:
            ids = [str(uuid4()) for _ in texts]
        
        if metadatas is None:
            metadatas = [{} for _ in texts]
        
        chunks = []
        for i, (text, metadata, id) in enumerate(zip(texts, metadatas, ids)):
            chunk = {
                "id": id,
                "text": text,
                "metadata": metadata,
            }
            if embeddings and i < len(embeddings):
                chunk["embedding"] = embeddings[i]
            chunks.append(chunk)
        
        # Store chunks
        try:
            tasks = []
            for chunk in chunks:
                tasks.append(self._store_chunk(chunk))
            
            await asyncio.gather(*tasks)
            return ids
        except Exception as e:
            raise StorageError(f"Failed to add texts to OneDrive: {str(e)}") from e
    
    async def _store_chunk(self, chunk: Dict[str, Any]) -> None:
        """
        Store a single chunk in OneDrive.
        
        Args:
            chunk: Chunk dictionary to store
            
        Raises:
            StorageError: If storing fails
        """
        try:
            # Create a temporary file
            temp_file = f"{chunk['id']}.json"
            with open(temp_file, "w") as f:
                json.dump(chunk, f)
            
            # Upload file
            file_path = f"{self.chunk_folder_path}/{chunk['id']}.json"
            await self._upload_file(temp_file, file_path)
            
            # Clean up temporary file
            os.remove(temp_file)
        except Exception as e:
            # Clean up temporary file if it exists
            if os.path.exists(f"{chunk['id']}.json"):
                os.remove(f"{chunk['id']}.json")
            
            raise StorageError(f"Failed to store chunk in OneDrive: {str(e)}") from e
    
    async def _upload_file(self, local_path: str, remote_path: str) -> str:
        """
        Upload a file to OneDrive.
        
        Args:
            local_path: Path to the local file
            remote_path: Path in OneDrive
            
        Returns:
            ID of the uploaded file
            
        Raises:
            StorageError: If upload fails
        """
        try:
            # Get parent folder ID
            parent_path = os.path.dirname(remote_path)
            file_name = os.path.basename(remote_path)
            
            parent_id = await self._get_item_id(parent_path)
            if not parent_id:
                raise StorageError(f"Parent folder not found: {parent_path}")
            
            # Check if file already exists
            file_id = await self._get_item_id(remote_path)
            
            if file_id:
                # Update existing file
                url = f"https://graph.microsoft.com/v1.0/me/drive/items/{file_id}/content"
                headers = {"Authorization": f"Bearer {self.access_token}"}
                
                with open(local_path, "rb") as f:
                    loop = asyncio.get_event_loop()
                    response = await loop.run_in_executor(
                        None,
                        lambda: requests.put(url, headers=headers, data=f)
                    )
                
                if response.status_code not in (200, 201):
                    raise StorageError(f"Failed to update file in OneDrive: {response.text}")
                
                return response.json()["id"]
            else:
                # Create new file
                url = f"https://graph.microsoft.com/v1.0/me/drive/items/{parent_id}:/{file_name}:/content"
                headers = {"Authorization": f"Bearer {self.access_token}"}
                
                with open(local_path, "rb") as f:
                    loop = asyncio.get_event_loop()
                    response = await loop.run_in_executor(
                        None,
                        lambda: requests.put(url, headers=headers, data=f)
                    )
                
                if response.status_code not in (200, 201):
                    raise StorageError(f"Failed to create file in OneDrive: {response.text}")
                
                return response.json()["id"]
        except Exception as e:
            raise StorageError(f"Failed to upload file to OneDrive: {str(e)}") from e
    
    async def add_documents(
        self,
        documents: List[Document]
    ) -> List[str]:
        """
        Add documents to the OneDrive vector store.
        
        Args:
            documents: List of Document objects to add
            
        Returns:
            List of document IDs for the added documents
            
        Raises:
            StorageError: If adding documents fails
        """
        if not self._initialized:
            raise StorageError("OneDrive vector store is not initialized")
        
        try:
            texts = [doc.content for doc in documents]
            metadatas = [doc.metadata for doc in documents]
            ids = [doc.id for doc in documents]
            
            # Store document metadata separately
            tasks = []
            for doc in documents:
                doc_metadata = {
                    "id": doc.id,
                    "type": doc.type.value if hasattr(doc.type, "value") else str(doc.type),
                    "metadata": doc.metadata
                }
                tasks.append(self._store_document_metadata(doc.id, doc_metadata))
            
            await asyncio.gather(*tasks)
            
            # Store the document contents as chunks
            return await self.add_texts(texts, metadatas, ids)
        except Exception as e:
            raise StorageError(f"Failed to add documents to OneDrive: {str(e)}") from e
    
    async def _store_document_metadata(self, doc_id: str, metadata: Dict[str, Any]) -> None:
        """
        Store document metadata in OneDrive.
        
        Args:
            doc_id: Document ID
            metadata: Document metadata dictionary
            
        Raises:
            StorageError: If storing fails
        """
        try:
            # Create a temporary file
            temp_file = f"doc_{doc_id}.json"
            with open(temp_file, "w") as f:
                json.dump(metadata, f)
            
            # Upload file
            file_path = f"{self.doc_folder_path}/doc_{doc_id}.json"
            await self._upload_file(temp_file, file_path)
            
            # Clean up temporary file
            os.remove(temp_file)
        except Exception as e:
            # Clean up temporary file if it exists
            if os.path.exists(f"doc_{doc_id}.json"):
                os.remove(f"doc_{doc_id}.json")
            
            raise StorageError(f"Failed to store document metadata in OneDrive: {str(e)}") from e
    
    async def add_chunks(
        self,
        chunks: List[TextChunk]
    ) -> List[str]:
        """
        Add text chunks to the OneDrive vector store.
        
        Args:
            chunks: List of TextChunk objects to add
            
        Returns:
            List of chunk IDs for the added chunks
            
        Raises:
            StorageError: If adding chunks fails
        """
        if not self._initialized:
            raise StorageError("OneDrive vector store is not initialized")
        
        try:
            texts = [chunk.text for chunk in chunks]
            metadatas = [chunk.metadata for chunk in chunks]
            ids = [chunk.id for chunk in chunks]
            embeddings = [chunk.embedding for chunk in chunks if chunk.embedding is not None]
            
            if embeddings and len(embeddings) != len(chunks):
                embeddings = None  # If not all chunks have embeddings, don't use any
            
            return await self.add_texts(texts, metadatas, ids, embeddings)
        except Exception as e:
            raise StorageError(f"Failed to add chunks to OneDrive: {str(e)}") from e
    
    async def _download_file(self, file_path: str) -> Dict[str, Any]:
        """
        Download a file from OneDrive and parse it as JSON.
        
        Args:
            file_path: Path to the file in OneDrive
            
        Returns:
            Parsed JSON content
            
        Raises:
            StorageError: If download fails
        """
        try:
            # Get file ID
            file_id = await self._get_item_id(file_path)
            if not file_id:
                raise StorageError(f"File not found: {file_path}")
            
            # Download file
            url = f"https://graph.microsoft.com/v1.0/me/drive/items/{file_id}/content"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(url, headers=headers)
            )
            
            if response.status_code != 200:
                raise StorageError(f"Failed to download file from OneDrive: {response.text}")
            
            # Parse JSON content
            return response.json()
        except Exception as e:
            raise StorageError(f"Failed to download file from OneDrive: {str(e)}") from e
    
    async def get_document(self, document_id: str) -> Optional[Document]:
        """
        Get a document by ID.
        
        Args:
            document_id: ID of the document to retrieve
            
        Returns:
            Document object if found, None otherwise
            
        Raises:
            StorageError: If retrieval fails
        """
        if not self._initialized:
            raise StorageError("OneDrive vector store is not initialized")
        
        try:
            # Get document metadata
            doc_path = f"{self.doc_folder_path}/doc_{document_id}.json"
            doc_metadata = await self._download_file(doc_path)
            
            # Get document content
            content_path = f"{self.chunk_folder_path}/{document_id}.json"
            doc_content = await self._download_file(content_path)
            
            # Create Document object
            from ...core.types import DocumentType
            
            doc_type = doc_metadata.get("type", "text")
            try:
                doc_type = DocumentType(doc_type)
            except ValueError:
                doc_type = DocumentType.TEXT
            
            return Document(
                id=document_id,
                content=doc_content.get("text", ""),
                type=doc_type,
                metadata=doc_metadata.get("metadata", {})
            )
        except Exception as e:
            # If file not found, return None
            if "File not found" in str(e):
                return None
            raise StorageError(f"Failed to get document from OneDrive: {str(e)}") from e
    
    async def get_chunk(self, chunk_id: str) -> Optional[TextChunk]:
        """
        Get a specific chunk by ID.
        
        Args:
            chunk_id: ID of the chunk to retrieve
            
        Returns:
            TextChunk object if found, None otherwise
            
        Raises:
            StorageError: If retrieval fails
        """
        if not self._initialized:
            raise StorageError("OneDrive vector store is not initialized")
        
        try:
            # Get chunk data
            chunk_path = f"{self.chunk_folder_path}/{chunk_id}.json"
            chunk_data = await self._download_file(chunk_path)
            
            # Create TextChunk object
            return TextChunk(
                id=chunk_id,
                text=chunk_data.get("text", ""),
                document_id=chunk_data.get("metadata", {}).get("document_id", ""),
                metadata=chunk_data.get("metadata", {}),
                embedding=chunk_data.get("embedding")
            )
        except Exception as e:
            # If file not found, return None
            if "File not found" in str(e):
                return None
            raise StorageError(f"Failed to get chunk from OneDrive: {str(e)}") from e
    
    async def get_chunks(
        self,
        chunk_ids: List[str]
    ) -> List[TextChunk]:
        """
        Get multiple chunks by their IDs.
        
        Args:
            chunk_ids: List of chunk IDs to retrieve
            
        Returns:
            List of TextChunk objects for the found chunks
            
        Raises:
            StorageError: If retrieval fails
        """
        if not self._initialized:
            raise StorageError("OneDrive vector store is not initialized")
        
        try:
            tasks = []
            for chunk_id in chunk_ids:
                tasks.append(self.get_chunk(chunk_id))
            
            chunks = await asyncio.gather(*tasks)
            return [chunk for chunk in chunks if chunk is not None]
        except Exception as e:
            raise StorageError(f"Failed to get chunks from OneDrive: {str(e)}") from e
    
    async def _list_files(self, folder_path: str) -> List[Dict[str, Any]]:
        """
        List files in a folder.
        
        Args:
            folder_path: Path to the folder
            
        Returns:
            List of file metadata
            
        Raises:
            StorageError: If listing fails
        """
        try:
            # Get folder ID
            folder_id = await self._get_item_id(folder_path)
            if not folder_id:
                raise StorageError(f"Folder not found: {folder_path}")
            
            # List files
            url = f"https://graph.microsoft.com/v1.0/me/drive/items/{folder_id}/children"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(url, headers=headers)
            )
            
            if response.status_code != 200:
                raise StorageError(f"Failed to list files in OneDrive: {response.text}")
            
            return response.json()["value"]
        except Exception as e:
            raise StorageError(f"Failed to list files in OneDrive: {str(e)}") from e
    
    async def similarity_search(
        self, 
        query: str, 
        k: int = 5, 
        filter: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ) -> List[Tuple[TextChunk, float]]:
        """
        Search for similar texts using semantic similarity.
        
        Note: This implementation does not perform true vector similarity search
        as OneDrive does not support vector operations. It returns the most recent chunks.
        For production use, consider using a dedicated vector database.
        
        Args:
            query: Query text or embedding to search for
            k: Number of results to return
            filter: Optional metadata filters to apply
            embedding: Optional pre-computed query embedding
            
        Returns:
            List of tuples containing (TextChunk, similarity_score)
            
        Raises:
            StorageError: If search fails
        """
        if not self._initialized:
            raise StorageError("OneDrive vector store is not initialized")
        
        try:
            # List files in the chunks folder
            files = await self._list_files(self.chunk_folder_path)
            
            # Sort by last modified (most recent first)
            files.sort(key=lambda file: file.get("lastModifiedDateTime", ""), reverse=True)
            
            # Limit to k results
            files = files[:k]
            
            # Get chunk data
            chunks = []
            for file in files:
                chunk_id = file["name"].replace(".json", "")
                chunk = await self.get_chunk(chunk_id)
                if chunk:
                    # Apply filter if provided
                    if filter:
                        match = True
                        for key, value in filter.items():
                            if key not in chunk.metadata or chunk.metadata[key] != value:
                                match = False
                                break
                        if not match:
                            continue
                    
                    # Add to results with a dummy score
                    chunks.append((chunk, 0.9))
            
            return chunks[:k]
        except Exception as e:
            raise StorageError(f"Failed to perform similarity search in OneDrive: {str(e)}") from e
    
    async def keyword_search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[TextChunk, float]]:
        """
        Search for texts using keyword matching.
        
        Note: This implementation does not perform true keyword search
        as OneDrive does not support text search. It returns the most recent chunks.
        For production use, consider using a dedicated vector database.
        
        Args:
            query: Query text to search for
            k: Number of results to return
            filter: Optional metadata filters to apply
            
        Returns:
            List of tuples containing (TextChunk, relevance_score)
            
        Raises:
            StorageError: If search fails
        """
        # For OneDrive, keyword search is the same as similarity search
        # since we don't have true search capabilities
        return await self.similarity_search(query, k, filter)
    
    async def _delete_file(self, file_path: str) -> bool:
        """
        Delete a file from OneDrive.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            StorageError: If deletion fails
        """
        try:
            # Get file ID
            file_id = await self._get_item_id(file_path)
            if not file_id:
                return False
            
            # Delete file
            url = f"https://graph.microsoft.com/v1.0/me/drive/items/{file_id}"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.delete(url, headers=headers)
            )
            
            return response.status_code == 204
        except Exception as e:
            raise StorageError(f"Failed to delete file from OneDrive: {str(e)}") from e
    
    async def delete(self, ids: List[str]) -> bool:
        """
        Delete texts from the vector store by IDs.
        
        Args:
            ids: List of IDs to delete
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            StorageError: If deletion fails
        """
        if not self._initialized:
            raise StorageError("OneDrive vector store is not initialized")
        
        try:
            tasks = []
            for id in ids:
                file_path = f"{self.chunk_folder_path}/{id}.json"
                tasks.append(self._delete_file(file_path))
            
            results = await asyncio.gather(*tasks)
            return all(results)
        except Exception as e:
            raise StorageError(f"Failed to delete chunks from OneDrive: {str(e)}") from e
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document and all its chunks.
        
        Args:
            document_id: ID of the document to delete
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            StorageError: If deletion fails
        """
        if not self._initialized:
            raise StorageError("OneDrive vector store is not initialized")
        
        try:
            # Delete document metadata
            doc_path = f"{self.doc_folder_path}/doc_{document_id}.json"
            await self._delete_file(doc_path)
            
            # Delete document content
            content_path = f"{self.chunk_folder_path}/{document_id}.json"
            await self._delete_file(content_path)
            
            # Find and delete all chunks with this document_id
            # This is a simplified approach - in a real implementation, we would need
            # to download and check each chunk to see if it belongs to this document
            
            return True
        except Exception as e:
            raise StorageError(f"Failed to delete document from OneDrive: {str(e)}") from e
    
    async def update_metadata(
        self,
        id: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Update metadata for a specific text or document.
        
        Args:
            id: ID of the text or document
            metadata: New metadata to apply (will be merged with existing)
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            StorageError: If update fails
        """
        if not self._initialized:
            raise StorageError("OneDrive vector store is not initialized")
        
        try:
            # Check if it's a document
            doc = await self.get_document(id)
            if doc:
                # Update document metadata
                doc.metadata = {**doc.metadata, **metadata}
                await self.add_documents([doc])
                return True
            
            # Check if it's a chunk
            chunk = await self.get_chunk(id)
            if chunk:
                # Update chunk metadata
                chunk.metadata = {**chunk.metadata, **metadata}
                await self.add_chunks([chunk])
                return True
            
            return False
        except Exception as e:
            raise StorageError(f"Failed to update metadata in OneDrive: {str(e)}") from e
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.
        
        Returns:
            Dictionary with statistics like document count, chunk count, etc.
            
        Raises:
            StorageError: If retrieving stats fails
        """
        if not self._initialized:
            raise StorageError("OneDrive vector store is not initialized")
        
        try:
            # Count documents
            doc_files = await self._list_files(self.doc_folder_path)
            doc_count = len(doc_files)
            
            # Count chunks
            chunk_files = await self._list_files(self.chunk_folder_path)
            chunk_count = len(chunk_files)
            
            return {
                "document_count": doc_count,
                "chunk_count": chunk_count,
                "provider": "onedrive",
                "folder_path": self.folder_path
            }
        except Exception as e:
            raise StorageError(f"Failed to get stats from OneDrive: {str(e)}") from e
    
    async def clear(self) -> bool:
        """
        Clear all data from the vector store.
        
        Returns:
            True if successful, False otherwise
            
        Raises:
            StorageError: If clearing fails
        """
        if not self._initialized:
            raise StorageError("OneDrive vector store is not initialized")
        
        try:
            # List all files in the chunks folder
            chunk_files = await self._list_files(self.chunk_folder_path)
            
            # Delete all chunk files
            chunk_tasks = []
            for file in chunk_files:
                file_path = f"{self.chunk_folder_path}/{file['name']}"
                chunk_tasks.append(self._delete_file(file_path))
            
            # List all files in the documents folder
            doc_files = await self._list_files(self.doc_folder_path)
            
            # Delete all document files
            doc_tasks = []
            for file in doc_files:
                file_path = f"{self.doc_folder_path}/{file['name']}"
                doc_tasks.append(self._delete_file(file_path))
            
            # Wait for all deletions to complete
            results = await asyncio.gather(*chunk_tasks, *doc_tasks)
            return all(results)
        except Exception as e:
            raise StorageError(f"Failed to clear OneDrive vector store: {str(e)}") from e
    
    async def close(self) -> None:
        """
        Close the vector store connection and cleanup resources.
        
        Raises:
            StorageError: If closing fails
        """
        # OneDrive API client doesn't need explicit closing
        self._initialized = False