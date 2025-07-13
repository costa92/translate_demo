import os
import json
from typing import List, Dict, Any

from google.cloud import storage
from google.api_core import exceptions

from .base import BaseStorageProvider, RetrievedChunk
from src.agents.knowledge_base.knowledge_processing_agent import ProcessedKnowledgeChunk

class GCSStorageProvider(BaseStorageProvider):
    """
    A storage provider for Google Cloud Storage (GCS).
    Supports both Application Default Credentials (ADC) for local development
    and Service Account keys for production/automation.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.bucket_name = self.config.get("bucket_name")
        if not self.bucket_name:
            raise ValueError("GCSStorageProvider requires a 'bucket_name' in the configuration.")
        
        self.storage_client = self._authenticate()
        self.bucket = self.storage_client.bucket(self.bucket_name)

    def _authenticate(self) -> storage.Client:
        """Authenticates using the configured method."""
        auth_method = self.config.get("auth_method", "adc") # Default to ADC

        if auth_method == "adc":
            print("[GCSProvider] Authenticating using Application Default Credentials (ADC).")
            try:
                return storage.Client()
            except exceptions.DefaultCredentialsError as e:
                print("\n[AUTH ERROR] Could not find Application Default Credentials.")
                print("Please run 'gcloud auth application-default login' in your terminal.")
                raise e

        elif auth_method == "service_account":
            print("[GCSProvider] Authenticating using Service Account key.")
            creds_path = self.config.get("service_account_key_path")
            if not creds_path or not os.path.exists(creds_path):
                raise FileNotFoundError(
                    f"Service account key file not found at '{creds_path}'."
                )
            return storage.Client.from_service_account_json(creds_path)
        
        else:
            raise ValueError(f"Unsupported GCS auth_method: '{auth_method}'. Use 'adc' or 'service_account'.")

    def store(self, chunks: List[ProcessedKnowledgeChunk]) -> bool:
        """Stores each chunk as a JSON object in the GCS bucket."""
        print(f"[GCSProvider] Storing {len(chunks)} chunks in bucket '{self.bucket_name}'...")
        try:
            for chunk in chunks:
                blob = self.bucket.blob(f"{chunk.id}.json")
                chunk_dict = chunk.__dict__
                blob.upload_from_string(
                    json.dumps(chunk_dict),
                    content_type="application/json"
                )
            return True
        except exceptions.GoogleAPICallError as e:
            print(f"An API error occurred during store: {e}")
            return False

    def retrieve(self, query_vector: List[float], top_k: int, filters: Dict) -> List[RetrievedChunk]:
        """Retrieves chunks from GCS."""
        print(f"[GCSProvider] Retrieving top {top_k} chunks from bucket '{self.bucket_name}'...")
        try:
            blobs = list(self.storage_client.list_blobs(self.bucket_name, max_results=top_k))
            retrieved_chunks = []
            for blob in blobs:
                chunk_data = json.loads(blob.download_as_string())
                retrieved_chunks.append(
                    RetrievedChunk(
                        id=chunk_data['id'],
                        text_content=chunk_data['text_content'],
                        score=0.9, # Dummy score
                        metadata=chunk_data['metadata']
                    )
                )
            return retrieved_chunks
        except exceptions.GoogleAPICallError as e:
            print(f"An error occurred during retrieve: {e}")
            return []

    def get_all_chunk_ids(self) -> List[str]:
        """Gets all chunk IDs (object names) from the bucket."""
        try:
            blobs = list(self.storage_client.list_blobs(self.bucket_name))
            return [blob.name.replace('.json', '') for blob in blobs]
        except exceptions.GoogleAPICallError as e:
            print(f"An error occurred during get_all_chunk_ids: {e}")
            return []