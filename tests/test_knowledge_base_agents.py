import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents.knowledge_base.orchestrator_agent import OrchestratorAgent
from agents.knowledge_base.data_collection_agent import DataCollectionAgent
from agents.knowledge_base.knowledge_processing_agent import KnowledgeProcessingAgent
from agents.knowledge_base.knowledge_storage_agent import KnowledgeStorageAgent
from agents.knowledge_base.knowledge_retrieval_agent import KnowledgeRetrievalAgent
from agents.knowledge_base.knowledge_maintenance_agent import KnowledgeMaintenanceAgent

class TestKnowledgeBaseAgents(unittest.TestCase):

    def setUp(self):
        self.orchestrator = OrchestratorAgent()
        self.data_collection_agent = DataCollectionAgent()
        self.knowledge_processing_agent = KnowledgeProcessingAgent()
        self.knowledge_storage_agent = KnowledgeStorageAgent()
        self.knowledge_retrieval_agent = KnowledgeRetrievalAgent()
        self.knowledge_maintenance_agent = KnowledgeMaintenanceAgent()

        self.orchestrator.register_agent("DataCollectionAgent", self.data_collection_agent)
        self.orchestrator.register_agent("KnowledgeProcessingAgent", self.knowledge_processing_agent)
        self.orchestrator.register_agent("KnowledgeStorageAgent", self.knowledge_storage_agent)
        self.orchestrator.register_agent("KnowledgeRetrievalAgent", self.knowledge_retrieval_agent)
        self.orchestrator.register_agent("KnowledgeMaintenanceAgent", self.knowledge_maintenance_agent)

    def test_data_collection_agent(self):
        payload = {"source": "test_source", "path": "/test/path"}
        result = self.orchestrator.receive_request("collect", "collect", payload)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, "doc1")

    def test_knowledge_processing_agent(self):
        payload = self.data_collection_agent.collect({})
        result = self.orchestrator.receive_request("process", "process", payload)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, "processed_doc1")

    def test_knowledge_storage_agent(self):
        processed_data = self.knowledge_processing_agent.process(self.data_collection_agent.collect({}))
        payload = processed_data
        result = self.orchestrator.receive_request("store", "store", payload)
        self.assertTrue(result)

    def test_knowledge_retrieval_agent(self):
        payload = {"query": "test query", "search_params": {}}
        result = self.orchestrator.receive_request("retrieve", "retrieve", payload)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].content, "This is a sample answer.")

    def test_knowledge_maintenance_agent(self):
        payload = {"source_config": {}}
        result = self.orchestrator.receive_request("maintain", "maintain", payload)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

if __name__ == '__main__':
    unittest.main()
