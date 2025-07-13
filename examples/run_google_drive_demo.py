
"""
Example script for using the GoogleDriveStorageProvider.

This script provides a focused demonstration of how to initialize and use
the KnowledgeStorageAgent specifically with the Google Drive backend.

Before running this script, you MUST:
1.  Follow the instructions in `docs/google_drive_setup.md` to get your `credentials.json` file.
2.  Place the `credentials.json` file in the root directory of this project.

The first time you run this, a browser window will open for you to authorize the application.
"""

import sys
import os

# Add the project root to the Python path to allow imports from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.knowledge_base.knowledge_storage_agent import KnowledgeStorageAgent
from src.agents.knowledge_base.knowledge_processing_agent import ProcessedKnowledgeChunk

def run_google_drive_demo():
    """Initializes the agent and runs a simple store/retrieve workflow."""
    print("==================================================")
    print("    Google Drive Storage Provider Demonstration")
    print("==================================================\n")

    # --- 1. Configure the Google Drive Provider ---
    # This configuration points to the default paths. The `folder_name` is optional.
    # If the folder does not exist in your Google Drive, it will be created automatically on the first run.
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    gdrive_config = {
        "credentials_path": os.path.join(project_root, "credentials.json"),
        "token_path": os.path.join(project_root, "token.json"),
        "folder_name": "GeminiCLIKnowledgeBase"
    }

    try:
        # --- 2. Initialize the Storage Agent ---
        print("Initializing KnowledgeStorageAgent with Google Drive provider...")
        storage_agent = KnowledgeStorageAgent(provider_type='google_drive', provider_config=gdrive_config)
        print("Initialization complete.")

        # --- 3. Create Dummy Data ---
        chunks_to_store = [
            ProcessedKnowledgeChunk(
                id="gdrive_chunk_001",
                original_id="doc_A",
                text_content="Google Drive stores files in the cloud.",
                vector=[0.8, 0.1, 0.1],
                category="tech_facts",
                entities=["Google Drive", "cloud"],
                relationships=[],
                metadata={"source": "google_api.txt"}
            )
        ]

        # --- 4. Store the Data ---
        print(f"\nAttempting to store {len(chunks_to_store)} chunk(s) in Google Drive...")
        success = storage_agent.store(chunks_to_store)
        if not success:
            print("Store operation failed. Please check the error messages above.")
            return
        print("Store operation successful.")

        # --- 5. Retrieve the Data ---
        print("\nAttempting to retrieve the latest chunk from Google Drive...")
        # Note: The basic provider retrieves the most recent file, it does not perform vector search.
        retrieved_chunks = storage_agent.retrieve(query_vector=[], top_k=1, filters={})
        print(f"Retrieved {len(retrieved_chunks)} chunk(s).")
        if retrieved_chunks:
            print(f"  -> Retrieved chunk ID: {retrieved_chunks[0].id}")
            print(f"  -> Content: '{retrieved_chunks[0].text_content}'")

    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        print("Please ensure your configuration is correct and you have a stable internet connection.")

    print("\n--- Demo Finished ---")


if __name__ == "__main__":
    run_google_drive_demo()
