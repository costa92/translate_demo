import os
import json
from typing import List, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io

from .base import BaseStorageProvider, RetrievedChunk
from src.agents.knowledge_base.knowledge_processing_agent import ProcessedKnowledgeChunk

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

class GoogleDriveStorageProvider(BaseStorageProvider):
    """
    A storage provider for Google Drive. Uses OAuth2 for authentication and
    stores each knowledge chunk as a separate JSON file in a dedicated folder.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.creds = self._authenticate()
        self.service = build("drive", "v3", credentials=self.creds)
        self.folder_id = self._get_or_create_folder(self.config.get("folder_name", "KnowledgeBase"))

    def _authenticate(self) -> Credentials:
        """Handles the OAuth2 authentication flow."""
        creds = None
        token_path = self.config.get("token_path", "token.json")
        creds_path = self.config.get("credentials_path", "credentials.json")

        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(creds_path):
                    raise FileNotFoundError(
                        f"Credentials file not found at '{creds_path}'. "
                        f"Please follow the authentication instructions."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(token_path, "w") as token:
                token.write(creds.to_json())
        return creds

    def _get_or_create_folder(self, folder_name: str) -> str:
        """Finds a folder by name or creates it if it doesn't exist."""
        try:
            query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
            response = self.service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            files = response.get("files", [])
            if files:
                print(f"[GoogleDriveProvider] Found folder '{folder_name}' with ID: {files[0].get('id')}")
                return files[0].get("id")
            else:
                print(f"[GoogleDriveProvider] Folder '{folder_name}' not found, creating it...")
                file_metadata = {"name": folder_name, "mimeType": "application/vnd.google-apps.folder"}
                folder = self.service.files().create(body=file_metadata, fields="id").execute()
                print(f"[GoogleDriveProvider] Created folder with ID: {folder.get('id')}")
                return folder.get("id")
        except HttpError as error:
            print(f"An error occurred: {error}")
            return None

    def store(self, chunks: List[ProcessedKnowledgeChunk]) -> bool:
        """Stores each chunk as a JSON file in the designated Google Drive folder."""
        print(f"[GoogleDriveProvider] Storing {len(chunks)} chunks...")
        try:
            for chunk in chunks:
                file_metadata = {"name": f"{chunk.id}.json", "parents": [self.folder_id]}
                chunk_dict = chunk.__dict__
                json_bytes = json.dumps(chunk_dict).encode('utf-8')
                
                # Create a temporary file to upload
                tmp_file_path = f"{chunk.id}.tmp.json"
                with open(tmp_file_path, "wb") as f:
                    f.write(json_bytes)
                
                media = MediaFileUpload(tmp_file_path, mimetype="application/json")
                
                self.service.files().create(body=file_metadata, media_body=media, fields="id").execute()
                os.remove(tmp_file_path)
            return True
        except HttpError as error:
            print(f"An error occurred during store: {error}")
            return False

    def retrieve(self, query_vector: List[float], top_k: int, filters: Dict) -> List[RetrievedChunk]:
        """
        Retrieves chunks from Google Drive. 
        NOTE: This provider does not support vector search. It retrieves the most recent files.
        A more advanced implementation would require a separate index.
        """
        print(f"[GoogleDriveProvider] Retrieving top {top_k} chunks...")
        try:
            query = f"'{self.folder_id}' in parents and trashed=false"
            response = self.service.files().list(q=query, pageSize=top_k, orderBy='createdTime desc', fields="files(id, name)").execute()
            files = response.get("files", [])
            retrieved_chunks = []
            for file in files:
                request = self.service.files().get_media(fileId=file.get('id'))
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                
                chunk_data = json.loads(fh.getvalue().decode('utf-8'))
                retrieved_chunks.append(
                    RetrievedChunk(
                        id=chunk_data['id'],
                        text_content=chunk_data['text_content'],
                        score=0.9, # Dummy score as there is no vector search
                        metadata=chunk_data['metadata']
                    )
                )
            return retrieved_chunks
        except HttpError as error:
            print(f"An error occurred during retrieve: {error}")
            return []

    def get_all_chunk_ids(self) -> List[str]:
        """Gets all chunk IDs (filenames) from the folder."""
        try:
            query = f"'{self.folder_id}' in parents and trashed=false"
            response = self.service.files().list(q=query, fields="files(name)").execute()
            files = response.get("files", [])
            return [f.get('name').replace('.json', '') for f in files]
        except HttpError as error:
            print(f"An error occurred during get_all_chunk_ids: {error}")
            return []