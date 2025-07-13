from typing import Dict, Any

class OrchestratorAgent:
    def __init__(self):
        self.agents = {}

    def register_agent(self, agent_name: str, agent_instance: Any):
        self.agents[agent_name] = agent_instance

    def receive_request(self, source: str, request_type: str, payload: Dict):
        # Simple routing for now, will be expanded with more complex logic
        if request_type == "collect":
            return self.distribute_task("DataCollectionAgent", "collect", payload)
        elif request_type == "process":
            return self.distribute_task("KnowledgeProcessingAgent", "process", payload)
        elif request_type == "store":
            return self.distribute_task("KnowledgeStorageAgent", "store", payload)
        elif request_type == "retrieve":
            return self.distribute_task("KnowledgeRetrievalAgent", "search", payload)
        elif request_type == "maintain":
            return self.distribute_task("KnowledgeMaintenanceAgent", "check_updates", payload)
        else:
            return {"status": "error", "message": "Unknown request type"}

    def distribute_task(self, agent_name: str, task_name: str, task_params: Dict):
        if agent_name in self.agents:
            agent = self.agents[agent_name]
            if hasattr(agent, task_name):
                task_method = getattr(agent, task_name)
                return task_method(task_params)
            else:
                return {"status": "error", "message": f"Task {task_name} not found in agent {agent_name}"}
        else:
            return {"status": "error", "message": f"Agent {agent_name} not found"}

    def aggregate_result(self, source_agent: str, status: str, result: Dict):
        # Simple aggregation, can be expanded
        print(f"Result from {source_agent}: {status} - {result}")
        return {"status": "aggregated", "result": result}
