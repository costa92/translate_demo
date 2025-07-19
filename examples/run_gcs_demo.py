#!/usr/bin/env python
"""
Example script for using the GCSStorageProvider with Application Default Credentials (ADC).

This script demonstrates the recommended way to connect to GCS for local development.

Before running this script, you MUST:
1.  Follow the instructions in `docs/gcs_setup.md` to:
    a. Install the gcloud CLI.
    b. Run `gcloud auth application-default login`.
    c. Create a GCS bucket and grant your user account the "Storage Object Admin" role.
2.  Update the `bucket_name` in the configuration below.
"""

import os
import sys

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    # Try to import from src
    from src.knowledge_base.storage.providers.gcs import GCSStorageProvider
    from src.knowledge_base.core.types import TextChunk as ProcessedKnowledgeChunk
    
    # Simple wrapper to mimic the KnowledgeStorageAgent interface
    class KnowledgeStorageAgent:
        def __init__(self, provider_type, provider_config):
            if provider_type == 'gcs':
                self.provider = GCSStorageProvider(provider_config)
            else:
                raise ValueError(f"Unsupported provider type: {provider_type}")
        
        def store(self, chunks):
            try:
                for chunk in chunks:
                    self.provider.store(chunk)
                return True
            except Exception as e:
                print(f"Error storing chunks: {e}")
                return False
        
        def retrieve(self, query_vector, top_k, filters):
            try:
                return self.provider.search(query_vector, top_k, filters)
            except Exception as e:
                print(f"Error retrieving chunks: {e}")
                return []
except ImportError:
    # Fall back to original imports
    try:
        from agents.knowledge_base.knowledge_storage_agent import KnowledgeStorageAgent
        from agents.knowledge_base.knowledge_processing_agent import ProcessedKnowledgeChunk
    except ImportError:
        print("Error: Required modules not found. This example requires either:")
        print("  1. The src.knowledge_base.storage.providers.gcs module, or")
        print("  2. The agents.knowledge_base.knowledge_storage_agent module")
        print("Please ensure you have the correct dependencies installed.")
        sys.exit(1)

def run_gcs_adc_demo():
    """Initializes the agent and runs a simple store/retrieve workflow with GCS using ADC."""
    print("====================================================================")
    print("    Google Cloud Storage (GCS) Provider Demonstration (ADC Mode)")
    print("====================================================================\n")

    # --- 1. Configure the GCS Provider for ADC ---
    # Note: No key file is needed. The SDK automatically finds credentials
    # after you run `gcloud auth application-default login`.
    gcs_config = {
        "auth_method": "adc",
        "bucket_name": "YOUR_GCS_BUCKET_NAME"  # <-- IMPORTANT: Replace with your actual bucket name
    }

    if gcs_config["bucket_name"] == "YOUR_GCS_BUCKET_NAME":
        print("[CONFIG ERROR] Please replace 'YOUR_GCS_BUCKET_NAME' in the script with your actual GCS bucket name.")
        return

    try:
        # --- 2. Initialize the Storage Agent ---
        print("Initializing KnowledgeStorageAgent with GCS provider (ADC)...")
        storage_agent = KnowledgeStorageAgent(provider_type='gcs', provider_config=gcs_config)
        print("Initialization complete.")

        # --- 3. Create Dummy Data ---
        chunk_id = f"gcs_adc_chunk_{int(os.times().user)}"
        chunks_to_store = [
            ProcessedKnowledgeChunk(
                id=chunk_id,
                original_id="doc_ADC",
                text_content="ADC simplifies authentication for local development.",
                vector=[0.1, 0.1, 0.9],
                category="gcp_auth",
                entities=["ADC"],
                relationships=[],
                metadata={"source": "gcp_docs.txt", "user": os.environ.get("USER", "unknown")}
            )
        ]

        # --- 4. Store the Data ---
        print(f"\nAttempting to store {len(chunks_to_store)} chunk(s) in GCS bucket '{gcs_config['bucket_name']}'...")
        success = storage_agent.store(chunks_to_store)
        if not success:
            print("Store operation failed. Please check the error messages above.")
            return
        print("Store operation successful.")

        # --- 5. Retrieve the Data ---
        print(f"\nAttempting to retrieve the latest chunk from the GCS bucket...")
        retrieved_chunks = storage_agent.retrieve(query_vector=[], top_k=1, filters={})
        print(f"Retrieved {len(retrieved_chunks)} chunk(s).")
        if retrieved_chunks:
            print(f"  -> Retrieved chunk ID: {retrieved_chunks[0].id}")
            print(f"  -> Content: '{retrieved_chunks[0].text_content}'")

    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        print("Please ensure you have followed the setup instructions in `docs/gcs_setup.md`.")

    print("\n--- Demo Finished ---")


if __name__ == "__main__":
    run_gcs_adc_demo()