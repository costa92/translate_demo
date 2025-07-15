import os
from typing import List, Dict, Any
import requests
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

class RawDocument:
    def __init__(self, id: str, content: Any, source: str, type: str, metadata: Dict):
        self.id = id
        self.content = content
        self.source = source
        self.type = type
        self.metadata = metadata

class DataCollectionAgent:
    def collect(self, source_config: Dict) -> List[RawDocument]:
        source_type = source_config.get("type")
        if source_type == "file":
            return self._collect_from_file(source_config.get("path"))
        elif source_type == "http":
            return self._collect_from_http(source_config.get("url"))
        elif source_type == "text":
            return self._collect_from_text(source_config.get("location"), source_config.get("metadata", {}))
        else:
            raise ValueError(f"Unsupported source type: {source_type}")

    def _collect_from_file(self, file_path: str) -> List[RawDocument]:
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        if ext == ".txt":
            return self._read_txt(file_path)
        elif ext == ".pdf":
            return self._read_pdf(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    def _read_txt(self, file_path: str) -> List[RawDocument]:
        with open(file_path, "r", encoding='utf-8') as f:
            content = f.read()
        return [RawDocument(id=file_path, content=content, source=file_path, type="text", metadata={})]

    def _read_pdf(self, file_path: str) -> List[RawDocument]:
        if PyPDF2 is None:
            raise ImportError("PyPDF2 is not installed. Please install it with 'pip install PyPDF2'")
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            content = ""
            for page in reader.pages:
                content += page.extract_text()
        return [RawDocument(id=file_path, content=content, source=file_path, type="pdf", metadata={})]

    def _collect_from_http(self, url: str) -> List[RawDocument]:
        response = requests.get(url)
        response.raise_for_status()
        return [RawDocument(id=url, content=response.text, source=url, type="http", metadata={})]
        
    def _collect_from_text(self, text_content: str, metadata: Dict = None) -> List[RawDocument]:
        """Collect from direct text content"""
        if metadata is None:
            metadata = {}
        
        # Generate a unique ID for the text
        text_id = f"text_{hash(text_content)}"
        
        return [RawDocument(
            id=text_id,
            content=text_content,
            source="direct_text",
            type="text",
            metadata=metadata
        )]
