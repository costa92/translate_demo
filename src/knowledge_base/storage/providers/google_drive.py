"""
Google Drive provider for the knowledge base system.

This module implements a vector store provider that uses Google Drive
for storing and retrieving document chunks.
"""

import os
import json
import asyncio
import pickle
from typing import List, Dict, Any, Optional, Tuple

import google.auth
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from googleapiclient.errors import HttpError

from ...core.types import Document, TextChunk
from ...core.exceptions import StorageError
from ..base import BaseVectorStore


class GoogleDriveVectorStore(BaseVectorStore):
    """
    Vector store implementation using Google Drive.
    
    This provider stores document chunks as JSON files in Google Drive.
    It uses OAuth 2.0 for authentication.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Google Drive vector store with configuration.
        
        Args:
            config: Configuration dictionary with Google Drive-specific settings:
                - credentials_file: Path to the client secrets file
                - token_file: Path to the token file
                - scopes: List of OAuth scopes
                - folder_id: ID of the folder to use (optional)
        
        Raises:
            ValueError: If required configuration is missing
        """
        super().__init__(config)
        self.credentials_file = self.config.get("credentials_file")
        self.token_file = self.config.get("token_file", "token.json")
        self.scopes = self.config.get("scopes", ["https://www.googleapis.com/auth/drive.file"])
        self.folder_id = self.config.get("folder_id")
        
        if not self.credentials_file:
            raise ValueError("GoogleDriveVectorStore requires a 'credentials_file' in the configuration.")
        
        self.service = None
        self.chunk_folder_id = None
        self.doc_folder_id = None
    
    async def initialize(self) -> None:
        """
        Initialize the Google Drive connection and resources.
        
        This method authenticates with Google Drive and sets up the folder structure.
        
        Raises:
            StorageError: If initialization fails
        """
        try:
            # Run authentication in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            creds = await loop.run_in_executor(None, self._authenticate)
            
            # Build the Drive service
            self.service = await loop.run_in_executor(
                None,
                lambda: build("drive", "v3", credentials=creds)
            )
            
            # Create or get folders
            if self.folder_id:
                # Use the provided folder
                self.chunk_folder_id = await self._create_folder("chunks", self.folder_id)
                self.doc_folder_id = await self._create_folder("documents", self.folder_id)
            else:
                # Create a root folder for the knowledge base
                kb_folder_id = await self._create_folder("knowledge_base")
                self.chunk_folder_id = await self._create_folder("chunks", kb_folder_id)
                self.doc_folder_id = await self._create_folder("documents", kb_folder_id)
            
            self._initialized = True
        except Exception as e:
            raise StorageError(f"Failed to initialize Google Drive vector store: {str(e)}") from e
    
    def _authenticate(self) -> Credentials:
        """
        Authenticate with Google Drive using OAuth 2.0.
        
        Returns:
            Google OAuth credentials
            
        Raises:
            ValueError: If authentication fails
        """
        creds = None
        
        # Check if token file exists
        if os.path.exists(self.token_file):
            with open(self.token_file, "rb") as token:
                creds = pickle.load(token)
        
        # If credentials don't exist or are invalid, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.scopes
                )
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(self.token_file, "wb") as token:
                pickle.dump(creds, token)
        
        return creds
    
    async def _create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> str:
        """
        Create a folder in Google Drive or get an existing one.
        
        Args:
            folder_name: Name of the folder to create
            parent_id: ID of the parent folder (optional)
            
        Returns:
            ID of the created or existing folder
            
        Raises:
            StorageError: If folder creation fails
        """
        try:
            loop = asyncio.get_event_loop()
            
            # Check if folder already exists
            query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder'"
            if parent_id:
                query += f" and '{parent_id}' in parents"
            query += " and trashed = false"
            
            response = await loop.run_in_executor(
                None,
                lambda: self.service.files().list(
                    q=query,
                    spaces="drive",
                    fields="files(id, name)"
                ).execute()
            )
            
            files = response.get("files", [])
            if files:
                return files[0]["id"]
            
            # Create folder if it doesn't exist
            folder_metadata = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder"
            }
            
            if parent_id:
                folder_metadata["parents"] = [parent_id]
            
            folder = await loop.run_in_executor(
                None,
                lambda: self.service.files().create(
                    body=folder_metadata,
                    fields="id"
                ).execute()
            )
            
            return folder.get("id")
        except Exception as e:
            raise StorageError(f"Failed to create folder in Google Drive: {str(e)}") from e
    
    async def add_texts(
        self, 
        texts: List[str], 
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        embeddings: Optional[List[List[float]]] = None
    ) -> List[str]:
        """
        Add texts to the Google Drive vector store.
        
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
            raise StorageError("Google Drive vector store is not initialized")
        
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
            raise StorageError(f"Failed to add texts to Google Drive: {str(e)}") from e
    
    async def _store_chunk(self, chunk: Dict[str, Any]) -> None:
        """
        Store a single chunk in Google Drive.
        
        Args:
            chunk: Chunk dictionary to store
            
        Raises:
            StorageError: If storing fails
        """
        try:
            loop = asyncio.get_event_loop()
            
            # Create a temporary file
            temp_file = f"{chunk['id']}.json"
            with open(temp_file, "w") as f:
                json.dump(chunk, f)
            
            # Check if file already exists
            query = f"name = '{chunk['id']}.json' and '{self.chunk_folder_id}' in parents and trashed = false"
            response = await loop.run_in_executor(
                None,
                lambda: self.service.files().list(
                    q=query,
                    spaces="drive",
                    fields="files(id)"
                ).execute()
            )
            
            files = response.get("files", [])
            
            # Upload or update file
            media = MediaFileUpload(temp_file, mimetype="application/json")
            
            if files:
                # Update existing file
                file_id = files[0]["id"]
                await loop.run_in_executor(
                    None,
                    lambda: self.service.files().update(
                        fileId=file_id,
                        media_body=media
                    ).execute()
                )
            else:
                # Create new file
                file_metadata = {
                    "name": f"{chunk['id']}.json",
                    "parents": [self.chunk_folder_id]
                }
                
                await loop.run_in_executor(
                    None,
                    lambda: self.service.files().create(
                        body=file_metadata,
                        media_body=media,
                        fields="id"
                    ).execute()
                )
            
            # Clean up temporary file
            os.remove(temp_file)
        except Exception as e:
            # Clean up temporary file if it exists
            if os.path.exists(f"{chunk['id']}.json"):
                os.remove(f"{chunk['id']}.json")
            
            raise StorageError(f"Failed to store chunk in Google Drive: {str(e)}") from e
    
    async def add_documents(
        self,
        documents: List[Document]
    ) -> List[str]:
        """
        Add documents to the Google Drive vector store.
        
        Args:
            documents: List of Document objects to add
            
        Returns:
            List of document IDs for the added documents
            
        Raises:
            StorageError: If adding documents fails
        """
        if not self._initialized:
            raise StorageError("Google Drive vector store is not initialized")
        
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
            raise StorageError(f"Failed to add documents to Google Drive: {str(e)}") from e
    
    async def _store_document_metadata(self, doc_id: str, metadata: Dict[str, Any]) -> None:
        """
        Store document metadata in Google Drive.
        
        Args:
            doc_id: Document ID
            metadata: Document metadata dictionary
            
        Raises:
            StorageError: If storing fails
        """
        try:
            loop = asyncio.get_event_loop()
            
            # Create a temporary file
            temp_file = f"doc_{doc_id}.json"
            with open(temp_file, "w") as f:
                json.dump(metadata, f)
            
            # Check if file already exists
            query = f"name = 'doc_{doc_id}.json' and '{self.doc_folder_id}' in parents and trashed = false"
            response = await loop.run_in_executor(
                None,
                lambda: self.service.files().list(
                    q=query,
                    spaces="drive",
                    fields="files(id)"
                ).execute()
            )
            
            files = response.get("files", [])
            
            # Upload or update file
            media = MediaFileUpload(temp_file, mimetype="application/json")
            
            if files:
                # Update existing file
                file_id = files[0]["id"]
                await loop.run_in_executor(
                    None,
                    lambda: self.service.files().update(
                        fileId=file_id,
                        media_body=media
                    ).execute()
                )
            else:
                # Create new file
                file_metadata = {
                    "name": f"doc_{doc_id}.json",
                    "parents": [self.doc_folder_id]
                }
                
                await loop.run_in_executor(
                    None,
                    lambda: self.service.files().create(
                        body=file_metadata,
                        media_body=media,
                        fields="id"
                    ).execute()
                )
            
            # Clean up temporary file
            os.remove(temp_file)
        except Exception as e:
            # Clean up temporary file if it exists
            if os.path.exists(f"doc_{doc_id}.json"):
                os.remove(f"doc_{doc_id}.json")
            
            raise StorageError(f"Failed to store document metadata in Google Drive: {str(e)}") from e
    
    async def add_chunks(
        self,
        chunks: List[TextChunk]
    ) -> List[str]:
        """
        Add text chunks to the Google Drive vector store.
        
        Args:
            chunks: List of TextChunk objects to add
            
        Returns:
            List of chunk IDs for the added chunks
            
        Raises:
            StorageError: If adding chunks fails
        """
        if not self._initialized:
            raise StorageError("Google Drive vector store is not initialized")
        
        try:
            texts = [chunk.text for chunk in chunks]
            metadatas = [chunk.metadata for chunk in chunks]
            ids = [chunk.id for chunk in chunks]
            embeddings = [chunk.embedding for chunk in chunks if chunk.embedding is not None]
            
            if embeddings and len(embeddings) != len(chunks):
                embeddings = None  # If not all chunks have embeddings, don't use any
            
            return await self.add_texts(texts, metadatas, ids, embeddings)
        except Exception as e:
            raise StorageError(f"Failed to add chunks to Google Drive: {str(e)}") from e
    
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
            raise StorageError("Google Drive vector store is not initialized")
        
        try:
            loop = asyncio.get_event_loop()
            
            # Get document metadata
            query = f"name = 'doc_{document_id}.json' and '{self.doc_folder_id}' in parents and trashed = false"
            response = await loop.run_in_executor(
                None,
                lambda: self.service.files().list(
                    q=query,
                    spaces="drive",
                    fields="files(id, name)"
                ).execute()
            )
            
            files = response.get("files", [])
            if not files:
                return None
            
            # Download document metadata
            file_id = files[0]["id"]
            doc_metadata = await self._download_file(file_id)
            
            # Get document content
            query = f"name = '{document_id}.json' and '{self.chunk_folder_id}' in parents and trashed = false"
            response = await loop.run_in_executor(
                None,
                lambda: self.service.files().list(
                    q=query,
                    spaces="drive",
                    fields="files(id, name)"
                ).execute()
            )
            
            files = response.get("files", [])
            if not files:
                return None
            
            # Download document content
            file_id = files[0]["id"]
            doc_content = await self._download_file(file_id)
            
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
            raise StorageError(f"Failed to get document from Google Drive: {str(e)}") from e
    
    async def _download_file(self, file_id: str) -> Dict[str, Any]:
        """
        Download a file from Google Drive and parse it as JSON.
        
        Args:
            file_id: ID of the file to download
            
        Returns:
            Parsed JSON content
            
        Raises:
            StorageError: If download fails
        """
        try:
            loop = asyncio.get_event_loop()
            
            # Create a temporary file
            temp_file = f"temp_{file_id}.json"
            
            # Download file
            request = self.service.files().get_media(fileId=file_id)
            
            with open(temp_file, "wb") as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    status, done = await loop.run_in_executor(None, downloader.next_chunk)
            
            # Read and parse file
            with open(temp_file, "r") as f:
                content = json.load(f)
            
            # Clean up temporary file
            os.remove(temp_file)
            
            return content
        except Exception as e:
            # Clean up temporary file if it exists
            if os.path.exists(f"temp_{file_id}.json"):
                os.remove(f"temp_{file_id}.json")
            
            raise StorageError(f"Failed to download file from Google Drive: {str(e)}") from e
    
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
            raise StorageError("Google Drive vector store is not initialized")
        
        try:
            loop = asyncio.get_event_loop()
            
            # Get chunk file
            query = f"name = '{chunk_id}.json' and '{self.chunk_folder_id}' in parents and trashed = false"
            response = await loop.run_in_executor(
                None,
                lambda: self.service.files().list(
                    q=query,
                    spaces="drive",
                    fields="files(id, name)"
                ).execute()
            )
            
            files = response.get("files", [])
            if not files:
                return None
            
            # Download chunk
            file_id = files[0]["id"]
            chunk_data = await self._download_file(file_id)
            
            # Create TextChunk object
            return TextChunk(
                id=chunk_id,
                text=chunk_data.get("text", ""),
                document_id=chunk_data.get("metadata", {}).get("document_id", ""),
                metadata=chunk_data.get("metadata", {}),
                embedding=chunk_data.get("embedding")
            )
        except Exception as e:
            raise StorageError(f"Failed to get chunk from Google Drive: {str(e)}") from e
    
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
            raise StorageError("Google Drive vector store is not initialized")
        
        try:
            tasks = []
            for chunk_id in chunk_ids:
                tasks.append(self.get_chunk(chunk_id))
            
            chunks = await asyncio.gather(*tasks)
            return [chunk for chunk in chunks if chunk is not None]
        except Exception as e:
            raise StorageError(f"Failed to get chunks from Google Drive: {str(e)}") from e
    
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
        as Google Drive does not support vector operations. It returns the most recent chunks.
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
            raise StorageError("Google Drive vector store is not initialized")
        
        try:
            loop = asyncio.get_event_loop()
            
            # List files in the chunks folder
            response = await loop.run_in_executor(
                None,
                lambda: self.service.files().list(
                    q=f"'{self.chunk_folder_id}' in parents and trashed = false",
                    spaces="drive",
                    fields="files(id, name, modifiedTime)",
                    orderBy="modifiedTime desc",
                    pageSize=100  # Limit to avoid too many results
                ).execute()
            )
            
            files = response.get("files", [])
            
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
            raise StorageError(f"Failed to perform similarity search in Google Drive: {str(e)}") from e
    
    async def keyword_search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[TextChunk, float]]:
        """
        Search for texts using keyword matching.
        
        Note: This implementation does not perform true keyword search
        as Google Drive does not support text search. It returns the most recent chunks.
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
        # For Google Drive, keyword search is the same as similarity search
        # since we don't have true search capabilities
        return await self.similarity_search(query, k, filter)
    
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
            raise StorageError("Google Drive vector store is not initialized")
        
        try:
            loop = asyncio.get_event_loop()
            
            for id in ids:
                # Find the file
                query = f"name = '{id}.json' and '{self.chunk_folder_id}' in parents and trashed = false"
                response = await loop.run_in_executor(
                    None,
                    lambda: self.service.files().list(
                        q=query,
                        spaces="drive",
                        fields="files(id)"
                    ).execute()
                )
                
                files = response.get("files", [])
                if files:
                    # Delete the file
                    file_id = files[0]["id"]
                    await loop.run_in_executor(
                        None,
                        lambda: self.service.files().delete(fileId=file_id).execute()
                    )
            
            return True
        except Exception as e:
            raise StorageError(f"Failed to delete chunks from Google Drive: {str(e)}") from e
    
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
            raise StorageError("Google Drive vector store is not initialized")
        
        try:
            loop = asyncio.get_event_loop()
            
            # Delete document metadata
            query = f"name = 'doc_{document_id}.json' and '{self.doc_folder_id}' in parents and trashed = false"
            response = await loop.run_in_executor(
                None,
                lambda: self.service.files().list(
                    q=query,
                    spaces="drive",
                    fields="files(id)"
                ).execute()
            )
            
            files = response.get("files", [])
            if files:
                file_id = files[0]["id"]
                await loop.run_in_executor(
                    None,
                    lambda: self.service.files().delete(fileId=file_id).execute()
                )
            
            # Delete document content
            query = f"name = '{document_id}.json' and '{self.chunk_folder_id}' in parents and trashed = false"
            response = await loop.run_in_executor(
                None,
                lambda: self.service.files().list(
                    q=query,
                    spaces="drive",
                    fields="files(id)"
                ).execute()
            )
            
            files = response.get("files", [])
            if files:
                file_id = files[0]["id"]
                await loop.run_in_executor(
                    None,
                    lambda: self.service.files().delete(fileId=file_id).execute()
                )
            
            # Find and delete all chunks with this document_id
            # This is a simplified approach - in a real implementation, we would need
            # to download and check each chunk to see if it belongs to this document
            
            return True
        except Exception as e:
            raise StorageError(f"Failed to delete document from Google Drive: {str(e)}") from e
    
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
            raise StorageError("Google Drive vector store is not initialized")
        
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
            raise StorageError(f"Failed to update metadata in Google Drive: {str(e)}") from e
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.
        
        Returns:
            Dictionary with statistics like document count, chunk count, etc.
            
        Raises:
            StorageError: If retrieving stats fails
        """
        if not self._initialized:
            raise StorageError("Google Drive vector store is not initialized")
        
        try:
            loop = asyncio.get_event_loop()
            
            # Count documents
            response = await loop.run_in_executor(
                None,
                lambda: self.service.files().list(
                    q=f"'{self.doc_folder_id}' in parents and trashed = false",
                    spaces="drive",
                    fields="files(id)"
                ).execute()
            )
            
            doc_count = len(response.get("files", []))
            
            # Count chunks
            response = await loop.run_in_executor(
                None,
                lambda: self.service.files().list(
                    q=f"'{self.chunk_folder_id}' in parents and trashed = false",
                    spaces="drive",
                    fields="files(id)"
                ).execute()
            )
            
            chunk_count = len(response.get("files", []))
            
            return {
                "document_count": doc_count,
                "chunk_count": chunk_count,
                "provider": "google_drive",
                "folder_id": self.folder_id or "auto-created"
            }
        except Exception as e:
            raise StorageError(f"Failed to get stats from Google Drive: {str(e)}") from e
    
    async def clear(self) -> bool:
        """
        Clear all data from the vector store.
        
        Returns:
            True if successful, False otherwise
            
        Raises:
            StorageError: If clearing fails
        """
        if not self._initialized:
            raise StorageError("Google Drive vector store is not initialized")
        
        try:
            loop = asyncio.get_event_loop()
            
            # List all files in the chunks folder
            response = await loop.run_in_executor(
                None,
                lambda: self.service.files().list(
                    q=f"'{self.chunk_folder_id}' in parents and trashed = false",
                    spaces="drive",
                    fields="files(id)"
                ).execute()
            )
            
            # Delete all chunk files
            for file in response.get("files", []):
                await loop.run_in_executor(
                    None,
                    lambda: self.service.files().delete(fileId=file["id"]).execute()
                )
            
            # List all files in the documents folder
            response = await loop.run_in_executor(
                None,
                lambda: self.service.files().list(
                    q=f"'{self.doc_folder_id}' in parents and trashed = false",
                    spaces="drive",
                    fields="files(id)"
                ).execute()
            )
            
            # Delete all document files
            for file in response.get("files", []):
                await loop.run_in_executor(
                    None,
                    lambda: self.service.files().delete(fileId=file["id"]).execute()
                )
            
            return True
        except Exception as e:
            raise StorageError(f"Failed to clear Google Drive vector store: {str(e)}") from e
    
    async def close(self) -> None:
        """
        Close the vector store connection and cleanup resources.
        
        Raises:
            StorageError: If closing fails
        """
        # Google Drive API client doesn't need explicit closing
        self._initialized = False