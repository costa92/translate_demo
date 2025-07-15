import hashlib
from typing import List, Dict, Optional
from data_collection_agent import RawDocument

class ProcessedKnowledgeChunk:
    def __init__(self, id: str, original_id: str, text_content: str, vector: List[float], category: str, entities: List[str], relationships: List[Dict], metadata: Dict):
        self.id = id
        self.original_id = original_id
        self.text_content = text_content
        self.vector = vector
        self.category = category
        self.entities = entities
        self.relationships = relationships
        self.metadata = metadata

class KnowledgeProcessingAgent:
    def __init__(self, embedding_model: Optional[str] = None, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
    def process(self, documents: List[RawDocument]) -> List[ProcessedKnowledgeChunk]:
        """
        Process raw documents into knowledge chunks with embeddings.
        """
        print(f"Processing {len(documents)} documents")
        processed_chunks = []
        
        for doc in documents:
            # Split document into chunks
            chunks = self._split_text(doc.content)
            
            for i, chunk_text in enumerate(chunks):
                # Generate embedding (using dummy vector for now)
                vector = self._generate_embedding(chunk_text)
                
                # Extract entities and relationships (basic implementation)
                entities = self._extract_entities(chunk_text)
                relationships = self._extract_relationships(chunk_text)
                
                # Create chunk metadata
                chunk_metadata = {
                    **doc.metadata,
                    'chunk_index': i,
                    'chunk_size': len(chunk_text),
                    'source_type': doc.type,
                    'source_id': doc.id
                }
                
                # Create chunk ID
                chunk_id = self._generate_chunk_id(doc.id, i)
                
                processed_chunks.append(
                    ProcessedKnowledgeChunk(
                        id=chunk_id,
                        original_id=doc.id,
                        text_content=chunk_text,
                        vector=vector,
                        category=self._categorize_text(chunk_text),
                        entities=entities,
                        relationships=relationships,
                        metadata=chunk_metadata
                    )
                )
                
        return processed_chunks
    
    def _split_text(self, text: str) -> List[str]:
        """
        Split text into chunks with overlap.
        """
        if not text:
            return []
            
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            
            # Try to break at word boundaries
            if end < len(text) and not text[end].isspace():
                last_space = chunk.rfind(' ')
                if last_space != -1:
                    chunk = chunk[:last_space]
                    end = start + last_space
            
            chunks.append(chunk.strip())
            start = end - self.chunk_overlap
            
            if start >= len(text):
                break
                
        return [chunk for chunk in chunks if chunk]
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text. Using dummy implementation for now.
        TODO: Integrate with actual embedding model (OpenAI, Sentence Transformers, etc.)
        """
        # Simple hash-based dummy embedding
        text_hash = hashlib.md5(text.encode()).hexdigest()
        # Convert hash to float values
        embedding = []
        for i in range(0, len(text_hash), 2):
            hex_val = text_hash[i:i+2]
            float_val = int(hex_val, 16) / 255.0
            embedding.append(float_val)
        
        # Pad or truncate to desired dimension (384 for sentence transformers)
        target_dim = 384
        if len(embedding) < target_dim:
            embedding.extend([0.0] * (target_dim - len(embedding)))
        else:
            embedding = embedding[:target_dim]
            
        return embedding
    
    def _extract_entities(self, text: str) -> List[str]:
        """
        Extract named entities from text.
        TODO: Integrate with NER model (spaCy, transformers, etc.)
        """
        # Simple keyword extraction as placeholder
        words = text.lower().split()
        # Filter out common words and keep potential entities
        entities = []
        for word in words:
            if len(word) > 3 and word.isalpha() and word.istitle():
                entities.append(word)
        return list(set(entities))
    
    def _extract_relationships(self, text: str) -> List[Dict]:
        """
        Extract relationships from text.
        TODO: Integrate with relationship extraction model
        """
        # Placeholder implementation
        return []
    
    def _categorize_text(self, text: str) -> str:
        """
        Categorize text content.
        TODO: Implement proper text classification
        """
        text_lower = text.lower()
        if any(keyword in text_lower for keyword in ['code', 'function', 'class', 'import', 'def']):
            return 'code'
        elif any(keyword in text_lower for keyword in ['api', 'endpoint', 'request', 'response']):
            return 'api'
        elif any(keyword in text_lower for keyword in ['config', 'setting', 'parameter']):
            return 'configuration'
        else:
            return 'general'
    
    def _generate_chunk_id(self, document_id: str, chunk_index: int) -> str:
        """
        Generate unique chunk ID.
        """
        return f"{document_id}_chunk_{chunk_index}"
