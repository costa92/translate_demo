from typing import List, Dict, Any

class RawDocument:
    def __init__(self, id: str, content: Any, source: str, type: str, metadata: Dict):
        self.id = id
        self.content = content
        self.source = source
        self.type = type
        self.metadata = metadata

class DataCollectionAgent:
    def collect(self, source_config: Dict) -> List[RawDocument]:
        # Placeholder implementation
        print(f"Collecting data from {source_config}")
        return [
            RawDocument(
                id="doc1",
                content="This is a sample document.",
                source=source_config.get("path", "unknown"),
                type="text",
                metadata={}
            )
        ]
