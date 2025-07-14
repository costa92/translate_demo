

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.knowledge_base.data_collection_agent import DataCollectionAgent
from src.agents.knowledge_base.knowledge_processing_agent import KnowledgeProcessingAgent
from src.agents.knowledge_base.knowledge_storage_agent import KnowledgeStorageAgent
from src.agents.knowledge_base.knowledge_retrieval_agent import KnowledgeRetrievalAgent
from src.agents.knowledge_base.rag_agent import RAGAgent

def run_rag_demo():
    """Demonstrates the full RAG pipeline."""
    print("==================================================================")
    print("    RAG Pipeline Demonstration")
    print("====================================================================\n")

    # --- 1. Setup Agents ---
    data_collection_agent = DataCollectionAgent()
    knowledge_processing_agent = KnowledgeProcessingAgent()
    storage_agent = KnowledgeStorageAgent(provider_type='memory')
    retrieval_agent = KnowledgeRetrievalAgent()
    rag_agent = RAGAgent(llm_provider='ollama', model='llama3:latest')

    # --- 2. Data Collection ---
    print("--- Step 1: Collecting data ---")
    # Create a dummy text file
    file_path = "/tmp/rag_demo.txt"
    with open(file_path, "w") as f:
        f.write("The sky is blue. The grass is green.")
    
    raw_docs = data_collection_agent.collect({"type": "file", "path": file_path})
    print(f"Collected {len(raw_docs)} document(s).")

    # --- 3. Knowledge Processing ---
    print("\n--- Step 2: Processing knowledge ---")
    processed_chunks = knowledge_processing_agent.process(raw_docs)
    print(f"Processed into {len(processed_chunks)} chunk(s).")

    # --- 4. Knowledge Storage ---
    print("\n--- Step 3: Storing knowledge ---")
    storage_agent.store(processed_chunks)
    print("Knowledge stored successfully.")

    # --- 5. Knowledge Retrieval ---
    query = "What color is the sky?"
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

