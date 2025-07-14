# Add the project root to the Python path
# This is required to run the script directly
# and to resolve the modules correctly.

from agents.knowledge_base.data_collection_agent import DataCollectionAgent
from agents.knowledge_base.knowledge_processing_agent import KnowledgeProcessingAgent
from agents.knowledge_base.knowledge_storage_agent import KnowledgeStorageAgent
from agents.knowledge_base.knowledge_retrieval_agent import KnowledgeRetrievalAgent
from agents.knowledge_base.rag_agent import RAGAgent


def run_rag_demo():
    """Demonstrates the full RAG pipeline."""
    print("==================================================================")
    print("    RAG Pipeline Demonstration")
    print("====================================================================\n")

    # --- 1. Setup Agents ---
    data_collection_agent = DataCollectionAgent()
    knowledge_processing_agent = KnowledgeProcessingAgent()
    storage_agent = KnowledgeStorageAgent(provider_type='memory')
    retrieval_agent = KnowledgeRetrievalAgent(storage_agent)
    rag_agent = RAGAgent(llm_provider='ollama', model='llama3:latest')

    # --- 2a. Data Collection from File ---
    print("--- Step 1a: Collecting data from a local file ---")
    file_path = "/tmp/rag_demo.txt"
    with open(file_path, "w") as f:
        f.write("The sky is blue. The grass is green.")

    file_docs = data_collection_agent.collect({"type": "file", "path": file_path})
    print(f"Collected {len(file_docs)} document(s) from file.")

    # --- 2b. Data Collection from HTTP ---
    print("\n--- Step 1b: Collecting data from an HTTP source ---")
    url = "https://gemini-cli.xyz/docs/zh/deployment"
    try:
        http_docs = data_collection_agent.collect({"type": "http", "url": url})
        print(f"Collected {len(http_docs)} document(s) from {url}.")
        raw_docs = file_docs + http_docs
    except Exception as e:
        print(f"Could not fetch from {url}. Skipping. Error: {e}")
        raw_docs = file_docs

    # --- 3. Knowledge Processing ---
    print("\n--- Step 2: Processing knowledge ---")
    processed_chunks = knowledge_processing_agent.process(raw_docs)
    print(f"Processed into {len(processed_chunks)} chunk(s).")

    # --- 4. Knowledge Storage ---
    print("\n--- Step 3: Storing knowledge ---")
    storage_agent.store(processed_chunks)
    print("Knowledge stored successfully.")

    # --- 5. Knowledge Retrieval ---
    query = "如何使用 NPX 安装 Gemini CLI？"
    print(f"\n--- Step 4: Retrieving knowledge for query: '{query}' ---")
    retrieved_chunks = retrieval_agent.search({"query": query})
    retrieved_context = [chunk.content for chunk in retrieved_chunks]
    print(f"Retrieved {len(retrieved_context)} context chunk(s).")

    # --- 6. Answer Generation ---
    print("\n--- Step 5: Generating answer with RAG ---")
    answer = rag_agent.generate(query, retrieved_context)
    print(f"\nGenerated Answer: {answer}")

    print("\n--- Demo Finished ---")

if __name__ == "__main__":
    run_rag_demo()

