import os
import json
import io
from typing import List, Dict, Any

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from .base import BaseStorageProvider, RetrievedChunk
from agents.knowledge_base.knowledge_processing_agent import ProcessedKnowledgeChunk

SCOPES = ["https://www.googleapis.com/auth/drive"]

class GoogleDriveServiceAccountProvider(BaseStorageProvider):
    """
    A storage provider for Google Drive using a Service Account.
    This allows the application to have its own identity and access a shared folder
    without requiring user interaction (no browser login).
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.creds = self._authenticate()
        self.service = build("drive", "v3", credentials=self.creds)
        self.folder_id = self._get_or_create_folder(self.config.get("folder_name", "CentralizedKnowledgeBase"))

    def _authenticate(self) -> service_account.Credentials:
        """Authenticates using a service account JSON key file."""
        creds_path = self.config.get("service_account_key_path")
        if not creds_path or not os.path.exists(creds_path):
            raise FileNotFoundError(
                f"Service account key file not found at '{creds_path}'. "
                f"Please follow the setup instructions."
            )
        
        creds = service_account.Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        return creds

    def _get_or_create_folder(self, folder_name: str) -> str:
        """Finds a folder by name within the Shared Drive or creates it."""
        try:
            # Search for the folder within all drives the service account can access.
            query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
            response = self.service.files().list(
                q=query, 
                spaces='drive', 
                fields='files(id, name)', 
                supportsAllDrives=True, 
                includeItemsFromAllDrives=True
            ).execute()
            
            files = response.get("files", [])
            if files:
                print(f"[ServiceAccountProvider] Found folder '{folder_name}' with ID: {files[0].get('id')}")
                return files[0].get('id')
            else:
                print(f"[ServiceAccountProvider] Folder '{folder_name}' not found, creating it...")
                # To create a folder in a Shared Drive, we need the ID of the Shared Drive.
                # A robust implementation would require the sharedDriveId in the config.
                # For simplicity, we assume the service account has access to only one shared drive.
                # A better approach is to create the folder manually in the shared drive.
                print("Please create the folder manually in your Shared Drive for now.")
                # This part is complex and requires sharedDriveId, so we will assume manual creation for now.
                return None

        except HttpError as error:
            print(f"An error occurred: {error}")
            return None

    def store(self, chunks: List[ProcessedKnowledgeChunk]) -> bool:
        """Stores each chunk as a JSON file in the designated Google Drive folder."""
        if not self.folder_id:
            print("[ServiceAccountProvider] Error: Folder ID not set. Cannot store files.")
            return False
            
        print(f"[ServiceAccountProvider] Storing {len(chunks)} chunks...")
        try:
            for chunk in chunks:
                file_metadata = {"name": f"{chunk.id}.json", "parents": [self.folder_id]}
                chunk_dict = chunk.__dict__
                json_bytes = json.dumps(chunk_dict).encode('utf-8')
                
                tmp_file_path = f"{chunk.id}.tmp.json"
                with open(tmp_file_path, "wb") as f:
                    f.write(json_bytes)
                
                media = MediaFileUpload(tmp_file_path, mimetype="application/json")
                self.service.files().create(
                    body=file_metadata, 
                    media_body=media, 
                    fields="id",
                    supportsAllDrives=True
                ).execute()
                os.remove(tmp_file_path)
            return True
        except HttpError as error:
            print(f"An error occurred during store: {error}")
            return False

    def retrieve(self, query_vector: List[float], top_k: int, filters: Dict) -> List[RetrievedChunk]:
        """Retrieves chunks from the shared Google Drive folder."""
        if not self.folder_id:
            return []
            
        print(f"[ServiceAccountProvider] Retrieving top {top_k} chunks...")
        try:
            query = f"'{self.folder_id}' in parents and trashed=false"
            response = self.service.files().list(
                q=query, 
                pageSize=top_k, 
                orderBy='createdTime desc', 
                fields="files(id, name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()
            files = response.get("files", [])
            retrieved_chunks = []
            for file in files:
                request = self.service.files().get_media(fileId=file.get('id'), supportsAllDrives=True)
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                
                chunk_data = json.loads(fh.getvalue().decode('utf-8'))
                retrieved_chunks.append(
                    RetrievedChunk(
                        id=chunk_data['id'],
                        text_content=chunk_data['text_content'],
                        score=0.9, # Dummy score
                        metadata=chunk_data['metadata']
                    )
                )
            return retrieved_chunks
        except HttpError as error:
            print(f"An error occurred during retrieve: {error}")
            return []

    def get_all_chunk_ids(self) -> List[str]:
        """Gets all chunk IDs (filenames) from the folder."""
        if not self.folder_id:
            return []
            
        try:
            query = f"'{self.folder_id}' in parents and trashed=false"
            response = self.service.files().list(
                q=query, 
                fields="files(name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()
            files = response.get("files", [])
            return [f.get('name').replace('.json', '') for f in files]
        except HttpError as error:
            print(f"An error occurred during get_all_chunk_ids: {error}")
            return []