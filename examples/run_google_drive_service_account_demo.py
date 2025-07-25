
"""
Example script for using the GoogleDriveServiceAccountProvider.

This script demonstrates how to use the application-centric Service Account
authentication method to store all knowledge in a single, centralized folder.

Before running this script, you MUST:
1.  Follow the instructions in `docs/google_drive_service_account_setup.md` to:
    a. Create a Service Account.
    b. Download its JSON key file.
    c. Create a folder in your personal Google Drive and share it with the Service Account's email address.
2.  Place the downloaded JSON key file in the root of this project (or update the path below).
"""




from agents.knowledge_base.knowledge_storage_agent import KnowledgeStorageAgent
from agents.knowledge_base.knowledge_processing_agent import ProcessedKnowledgeChunk

def run_service_account_demo():
    """Initializes the agent and runs a simple store/retrieve workflow."""
    print("===========================================================")
    print("    Google Drive Service Account Provider Demonstration")
    print("===========================================================\n")

    # --- 1. Configure the Service Account Provider ---
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sa_config = {
        "service_account_key_path": os.path.join(project_root, "service-account-credentials.json"),
        "folder_name": "CentralizedKnowledgeBase" # Must match the folder you shared
    }

    try:
        # --- 2. Initialize the Storage Agent ---
        print("Initializing KnowledgeStorageAgent with Service Account provider...")
        storage_agent = KnowledgeStorageAgent(provider_type='google_drive_service_account', provider_config=sa_config)
        print("Initialization complete.")

        # --- 3. Create Dummy Data ---
        chunk_id = f"sa_chunk_{int(os.times().user)}" # Create a unique ID
        chunks_to_store = [
            ProcessedKnowledgeChunk(
                id=chunk_id,
                original_id="doc_C",
                text_content="Service Accounts provide application-level authentication.",
                vector=[0.1, 0.8, 0.1],
                category="tech_facts",
                entities=["Service Account"],
                relationships=[],
                metadata={"source": "gcp_docs.txt", "author": "system"}
            )
        ]

        # --- 4. Store the Data ---
        print(f"\nAttempting to store {len(chunks_to_store)} chunk(s) in the shared Google Drive folder...")
        success = storage_agent.store(chunks_to_store)
        if not success:
            print("Store operation failed. Please check the error messages above.")
            return
        print("Store operation successful.")

        # --- 5. Retrieve the Data ---
        print("\nAttempting to retrieve the latest chunk from the shared folder...")
        retrieved_chunks = storage_agent.retrieve(query_vector=[], top_k=1, filters={})
        print(f"Retrieved {len(retrieved_chunks)} chunk(s).")
        if retrieved_chunks:
            print(f"  -> Retrieved chunk ID: {retrieved_chunks[0].id}")
            print(f"  -> Content: '{retrieved_chunks[0].text_content}'")

    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
        print("Please follow the setup instructions in `docs/google_drive_service_account_setup.md`.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        print("Please ensure your configuration is correct and you have a stable internet connection.")

    print("\n--- Demo Finished ---")


if __name__ == "__main__":
    run_service_account_demo()
