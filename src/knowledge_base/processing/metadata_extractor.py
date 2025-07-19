"""
Metadata extraction utilities for the unified knowledge base system.

This module provides functionality for extracting and generating metadata
from documents and text chunks.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import hashlib
import unicodedata
from pathlib import Path

from ..core.types import Document, TextChunk, DocumentType
from ..core.exceptions import ProcessingError

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """
    Extracts and generates metadata from documents and text chunks.
    """
    
    def __init__(self):
        """Initialize the metadata extractor."""
        logger.debug("MetadataExtractor initialized")
    
    def extract_document_metadata(self, document: Document) -> Dict[str, Any]:
        """
        Extract metadata from a document based on its content and type.
        
        Args:
            document: The document to extract metadata from
            
        Returns:
            Dictionary of extracted metadata
        """
        metadata = {}
        
        # Add basic metadata
        metadata["document_id"] = document.id
        metadata["document_type"] = document.type.value
        metadata["content_length"] = len(document.content)
        metadata["extracted_at"] = datetime.now().isoformat()
        
        # Add source if available
        if document.source:
            metadata["source"] = document.source
            
            # Extract filename and extension if source is a file path
            try:
                path = Path(document.source)
                if path.exists() or "/" in document.source or "\\" in document.source:
                    metadata["filename"] = path.name
                    metadata["extension"] = path.suffix.lstrip(".")
                    metadata["directory"] = str(path.parent)
            except Exception:
                # If not a valid path, ignore these fields
                pass
        
        # Add content hash for deduplication
        metadata["content_hash"] = self._generate_content_hash(document.content)
        
        # Extract type-specific metadata
        if document.type == DocumentType.TEXT:
            self._extract_text_metadata(document.content, metadata)
        elif document.type == DocumentType.MARKDOWN:
            self._extract_markdown_metadata(document.content, metadata)
        elif document.type == DocumentType.HTML:
            self._extract_html_metadata(document.content, metadata)
        elif document.type == DocumentType.CODE:
            self._extract_code_metadata(document.content, metadata)
        
        # Merge with existing metadata, giving priority to existing values
        merged_metadata = {**metadata, **document.metadata}
        
        logger.debug(f"Extracted {len(metadata)} metadata fields for document {document.id}")
        return merged_metadata
    
    def extract_chunk_metadata(self, chunk: TextChunk, document: Optional[Document] = None) -> Dict[str, Any]:
        """
        Extract metadata from a text chunk.
        
        Args:
            chunk: The text chunk to extract metadata from
            document: Optional parent document for context
            
        Returns:
            Dictionary of extracted metadata
        """
        metadata = {}
        
        # Add basic metadata
        metadata["chunk_id"] = chunk.id
        metadata["document_id"] = chunk.document_id
        metadata["chunk_length"] = len(chunk.text)
        metadata["start_index"] = chunk.start_index
        metadata["end_index"] = chunk.end_index
        metadata["extracted_at"] = datetime.now().isoformat()
        
        # Add content hash for deduplication
        metadata["content_hash"] = self._generate_content_hash(chunk.text)
        
        # Extract text-specific metadata
        self._extract_text_metadata(chunk.text, metadata)
        
        # Add document context if available
        if document:
            metadata["document_type"] = document.type.value
            if document.source:
                metadata["source"] = document.source
        
        # Merge with existing metadata, giving priority to existing values
        merged_metadata = {**metadata, **chunk.metadata}
        
        logger.debug(f"Extracted {len(metadata)} metadata fields for chunk {chunk.id}")
        return merged_metadata
    
    def generate_automatic_metadata(self, text: str) -> Dict[str, Any]:
        """
        Generate automatic metadata for any text content.
        
        Args:
            text: The text content to analyze
            
        Returns:
            Dictionary of generated metadata
        """
        metadata = {}
        
        # Basic text statistics
        metadata["char_count"] = len(text)
        metadata["word_count"] = len(text.split())
        metadata["line_count"] = text.count('\n') + 1
        
        # Language detection (simplified)
        metadata["language"] = self._detect_language(text)
        
        # Reading level estimation
        metadata["reading_level"] = self._estimate_reading_level(text)
        
        # Content categorization (simplified)
        metadata["content_type"] = self._categorize_content(text)
        
        # Named entities (simplified)
        entities = self._extract_entities(text)
        if entities:
            metadata["entities"] = entities
        
        # Keywords (simplified)
        keywords = self._extract_keywords(text)
        if keywords:
            metadata["keywords"] = keywords
        
        logger.debug(f"Generated {len(metadata)} automatic metadata fields")
        return metadata
    
    def index_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare metadata for indexing by normalizing values and adding search-optimized fields.
        
        Args:
            metadata: The metadata to prepare for indexing
            
        Returns:
            Dictionary of indexed metadata
        """
        indexed_metadata = {}
        
        for key, value in metadata.items():
            # Skip None values
            if value is None:
                continue
                
            # Handle different value types
            if isinstance(value, str):
                # Keep original string value
                indexed_metadata[key] = value
                
                # Add normalized version for search
                indexed_metadata[f"{key}_normalized"] = self._normalize_string(value)
                
                # Add lowercase version for case-insensitive search
                indexed_metadata[f"{key}_lower"] = value.lower()
                
                # Add tokenized version for partial matching
                tokens = self._tokenize_string(value)
                if tokens:
                    indexed_metadata[f"{key}_tokens"] = tokens
                    
            elif isinstance(value, (int, float, bool)):
                # Keep numeric and boolean values as is
                indexed_metadata[key] = value
                
            elif isinstance(value, list):
                # For lists, keep original values
                indexed_metadata[key] = value
                
                # For string lists, add lowercase version
                if all(isinstance(item, str) for item in value):
                    indexed_metadata[f"{key}_lower"] = [item.lower() for item in value]
                    
            elif isinstance(value, dict):
                # For dictionaries, recursively index
                indexed_metadata[key] = self.index_metadata(value)
            else:
                # Convert other types to string
                indexed_metadata[key] = str(value)
        
        logger.debug(f"Indexed {len(indexed_metadata)} metadata fields")
        return indexed_metadata
    
    def _extract_text_metadata(self, text: str, metadata: Dict[str, Any]) -> None:
        """Extract metadata from plain text content."""
        # Count paragraphs (text blocks separated by blank lines)
        paragraphs = re.split(r'\n\s*\n', text)
        metadata["paragraph_count"] = len(paragraphs)
        
        # Estimate reading time (average reading speed: 200 words per minute)
        word_count = len(text.split())
        metadata["word_count"] = word_count
        metadata["estimated_reading_time_seconds"] = int(word_count / 200 * 60)
        
        # Detect if text contains URLs
        urls = re.findall(r'https?://\S+', text)
        if urls:
            metadata["contains_urls"] = True
            metadata["url_count"] = len(urls)
        
        # Detect if text contains email addresses
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if emails:
            metadata["contains_emails"] = True
            metadata["email_count"] = len(emails)
    
    def _extract_markdown_metadata(self, text: str, metadata: Dict[str, Any]) -> None:
        """Extract metadata from Markdown content."""
        # Extract basic text metadata first
        self._extract_text_metadata(text, metadata)
        
        # Count headers
        headers = re.findall(r'^#+\s+.+$', text, re.MULTILINE)
        metadata["header_count"] = len(headers)
        
        # Extract title (first h1 header)
        title_match = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
        if title_match:
            metadata["title"] = title_match.group(1)
        
        # Count code blocks
        code_blocks = re.findall(r'```[\s\S]*?```', text)
        metadata["code_block_count"] = len(code_blocks)
        
        # Count links
        links = re.findall(r'\[.+?\]\(.+?\)', text)
        metadata["link_count"] = len(links)
        
        # Count images
        images = re.findall(r'!\[.+?\]\(.+?\)', text)
        metadata["image_count"] = len(images)
        
        # Detect if contains tables
        if '|---' in text or '| ---' in text:
            metadata["contains_tables"] = True
    
    def _extract_html_metadata(self, text: str, metadata: Dict[str, Any]) -> None:
        """Extract metadata from HTML content."""
        # Extract title
        title_match = re.search(r'<title>(.*?)</title>', text, re.IGNORECASE | re.DOTALL)
        if title_match:
            metadata["title"] = title_match.group(1)
        
        # Extract meta tags
        meta_tags = re.findall(r'<meta\s+([^>]+)>', text, re.IGNORECASE)
        for meta in meta_tags:
            name_match = re.search(r'name=["\'](.*?)["\']', meta, re.IGNORECASE)
            content_match = re.search(r'content=["\'](.*?)["\']', meta, re.IGNORECASE)
            if name_match and content_match:
                name = name_match.group(1).lower()
                content = content_match.group(1)
                metadata[f"meta_{name}"] = content
        
        # Count headings
        for i in range(1, 7):
            headings = re.findall(f'<h{i}[^>]*>(.*?)</h{i}>', text, re.IGNORECASE | re.DOTALL)
            metadata[f"h{i}_count"] = len(headings)
        
        # Count links
        links = re.findall(r'<a\s+[^>]*href=["\'](.*?)["\'][^>]*>', text, re.IGNORECASE)
        metadata["link_count"] = len(links)
        
        # Count images
        images = re.findall(r'<img\s+[^>]*>', text, re.IGNORECASE)
        metadata["image_count"] = len(images)
        
        # Detect if contains tables
        if '<table' in text.lower():
            metadata["contains_tables"] = True
        
        # Detect if contains forms
        if '<form' in text.lower():
            metadata["contains_forms"] = True
        
        # Detect if contains scripts
        if '<script' in text.lower():
            metadata["contains_scripts"] = True
    
    def _extract_code_metadata(self, text: str, metadata: Dict[str, Any]) -> None:
        """Extract metadata from code content."""
        # Count lines of code (excluding blank lines and comments)
        code_lines = 0
        comment_lines = 0
        blank_lines = 0
        
        # Simple comment detection for common languages
        single_line_comment_patterns = [r'^\s*#', r'^\s*//', r'^\s*--']
        multi_line_comment_patterns = [(r'/\*', r'\*/'), (r'"""', r'"""'), (r"'''", r"'''")]
        
        in_multi_line_comment = False
        current_multi_line_pattern = None
        
        for line in text.split('\n'):
            stripped_line = line.strip()
            
            # Check for blank lines
            if not stripped_line:
                blank_lines += 1
                continue
            
            # Check if we're in a multi-line comment
            if in_multi_line_comment:
                comment_lines += 1
                # Check if this line ends the multi-line comment
                if current_multi_line_pattern and re.search(current_multi_line_pattern[1], stripped_line):
                    in_multi_line_comment = False
                    current_multi_line_pattern = None
                continue
            
            # Check for single-line comments
            is_comment = False
            for pattern in single_line_comment_patterns:
                if re.match(pattern, stripped_line):
                    comment_lines += 1
                    is_comment = True
                    break
            
            if is_comment:
                continue
            
            # Check for start of multi-line comments
            for start_pattern, end_pattern in multi_line_comment_patterns:
                if re.search(start_pattern, stripped_line):
                    comment_lines += 1
                    in_multi_line_comment = True
                    current_multi_line_pattern = (start_pattern, end_pattern)
                    # Check if the comment ends on the same line
                    if re.search(end_pattern, stripped_line[re.search(start_pattern, stripped_line).end():]):
                        in_multi_line_comment = False
                        current_multi_line_pattern = None
                    break
            
            if not in_multi_line_comment:
                code_lines += 1
        
        metadata["code_lines"] = code_lines
        metadata["comment_lines"] = comment_lines
        metadata["blank_lines"] = blank_lines
        metadata["total_lines"] = code_lines + comment_lines + blank_lines
        
        # Calculate comment ratio
        if code_lines > 0:
            metadata["comment_ratio"] = round(comment_lines / code_lines, 2)
        
        # Detect programming language (simplified)
        metadata["language"] = self._detect_programming_language(text)
        
        # Count functions/methods (simplified)
        function_patterns = [
            r'def\s+\w+\s*\(', # Python
            r'function\s+\w+\s*\(', # JavaScript
            r'\w+\s*=\s*function\s*\(', # JavaScript
            r'const\s+\w+\s*=\s*\(.*\)\s*=>', # JavaScript arrow function
            r'public|private|protected|static\s+\w+\s+\w+\s*\(', # Java/C#
        ]
        
        function_count = 0
        for pattern in function_patterns:
            function_count += len(re.findall(pattern, text))
        
        metadata["function_count"] = function_count
        
        # Count classes (simplified)
        class_patterns = [
            r'class\s+\w+', # Python, JavaScript, Java
            r'interface\s+\w+', # TypeScript, Java
        ]
        
        class_count = 0
        for pattern in class_patterns:
            class_count += len(re.findall(pattern, text))
        
        metadata["class_count"] = class_count
    
    def _detect_programming_language(self, text: str) -> str:
        """Detect programming language from code content (simplified)."""
        # Check for language-specific patterns
        patterns = {
            "python": [r'import\s+\w+', r'from\s+\w+\s+import', r'def\s+\w+\s*\(', r'class\s+\w+:'],
            "javascript": [r'const\s+\w+\s*=', r'let\s+\w+\s*=', r'function\s+\w+\s*\(', r'export\s+default'],
            "typescript": [r'interface\s+\w+', r'type\s+\w+\s*=', r':\s*\w+\[\]', r':\s*Promise<'],
            "java": [r'public\s+class', r'private\s+\w+\(', r'protected\s+\w+\(', r'import\s+java\.'],
            "c#": [r'namespace\s+\w+', r'using\s+\w+;', r'public\s+class', r'private\s+void'],
            "go": [r'package\s+\w+', r'func\s+\w+\s*\(', r'import\s+\(', r'type\s+\w+\s+struct'],
            "rust": [r'fn\s+\w+\s*\(', r'let\s+mut\s+\w+', r'use\s+\w+::', r'impl\s+\w+'],
            "php": [r'<\?php', r'function\s+\w+\s*\(', r'\$\w+\s*=', r'namespace\s+\w+'],
            "ruby": [r'def\s+\w+', r'class\s+\w+\s+<', r'require\s+[\'\"]', r'module\s+\w+'],
            "html": [r'<!DOCTYPE\s+html>', r'<html', r'<head', r'<body'],
            "css": [r'\w+\s*{', r'@media', r'#\w+\s*{', r'\.\w+\s*{'],
            "sql": [r'SELECT\s+\w+\s+FROM', r'INSERT\s+INTO', r'CREATE\s+TABLE', r'UPDATE\s+\w+\s+SET'],
        }
        
        scores = {lang: 0 for lang in patterns}
        
        for lang, lang_patterns in patterns.items():
            for pattern in lang_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                scores[lang] += len(matches)
        
        # Get language with highest score
        max_score = 0
        detected_lang = "unknown"
        
        for lang, score in scores.items():
            if score > max_score:
                max_score = score
                detected_lang = lang
        
        return detected_lang if max_score > 0 else "unknown"
    
    def _detect_language(self, text: str) -> str:
        """Detect natural language of text (simplified)."""
        # This is a very simplified language detection
        # In a real implementation, you would use a library like langdetect
        
        # Sample of common words in different languages
        language_markers = {
            "en": ["the", "and", "is", "in", "to", "of", "that", "for", "it", "with"],
            "es": ["el", "la", "de", "en", "y", "a", "que", "los", "se", "del"],
            "fr": ["le", "la", "de", "et", "les", "des", "en", "un", "du", "une"],
            "de": ["der", "die", "und", "in", "den", "von", "zu", "das", "mit", "sich"],
            "zh": ["的", "是", "不", "了", "在", "人", "有", "我", "他", "这"],
            "ja": ["の", "に", "は", "を", "た", "が", "で", "て", "と", "し"],
            "ru": ["и", "в", "не", "на", "я", "что", "с", "по", "это", "от"],
        }
        
        # Count occurrences of marker words
        scores = {lang: 0 for lang in language_markers}
        
        # Convert to lowercase for matching
        lower_text = text.lower()
        
        for lang, markers in language_markers.items():
            for marker in markers:
                # Count occurrences of the marker word
                # Use word boundaries for non-Asian languages
                if lang in ["zh", "ja"]:
                    scores[lang] += lower_text.count(marker)
                else:
                    scores[lang] += len(re.findall(r'\b' + re.escape(marker) + r'\b', lower_text))
        
        # Get language with highest score
        max_score = 0
        detected_lang = "en"  # Default to English
        
        for lang, score in scores.items():
            if score > max_score:
                max_score = score
                detected_lang = lang
        
        return detected_lang
    
    def _estimate_reading_level(self, text: str) -> str:
        """Estimate reading level of text (simplified)."""
        # This is a very simplified reading level estimation
        # In a real implementation, you would use more sophisticated algorithms
        
        # Count sentences, words, and syllables
        sentences = re.split(r'[.!?]+', text)
        sentences = [s for s in sentences if s.strip()]
        
        words = text.split()
        word_count = len(words)
        
        if not sentences or word_count == 0:
            return "unknown"
        
        # Calculate average sentence length
        avg_sentence_length = word_count / len(sentences)
        
        # Calculate average word length as a proxy for syllables
        avg_word_length = sum(len(word) for word in words) / word_count
        
        # Simple classification based on average sentence and word length
        if avg_sentence_length > 20 or avg_word_length > 6:
            return "advanced"
        elif avg_sentence_length > 14 or avg_word_length > 5:
            return "intermediate"
        else:
            return "basic"
    
    def _categorize_content(self, text: str) -> str:
        """Categorize content type (simplified)."""
        # This is a very simplified content categorization
        # In a real implementation, you would use more sophisticated algorithms
        
        # Check for code-like content
        code_patterns = [
            r'function\s+\w+\s*\(',
            r'class\s+\w+',
            r'def\s+\w+\s*\(',
            r'import\s+\w+',
            r'<html',
            r'SELECT\s+\w+\s+FROM',
        ]
        
        for pattern in code_patterns:
            if re.search(pattern, text):
                return "code"
        
        # Check for structured data
        if re.search(r'^\s*[\[{]', text) and re.search(r'[\]}]\s*$', text):
            return "structured_data"
        
        # Check for tabular data
        if re.search(r'^\s*\w+(\s*,\s*\w+)+\s*$', text, re.MULTILINE):
            return "tabular_data"
        
        # Check for narrative content
        narrative_markers = [
            r'\b(once|one day|story|narrative|tale|novel|chapter)\b',
            r'\b(he|she|they)\s+\w+ed\b',
        ]
        
        for pattern in narrative_markers:
            if re.search(pattern, text, re.IGNORECASE):
                return "narrative"
        
        # Check for instructional content
        instructional_markers = [
            r'\b(step|guide|how to|tutorial|instructions|follow|procedure)\b',
            r'^\s*\d+\.\s+\w+',
        ]
        
        for pattern in instructional_markers:
            if re.search(pattern, text, re.IGNORECASE):
                return "instructional"
        
        # Check for informational content
        informational_markers = [
            r'\b(overview|introduction|summary|description|explanation|definition)\b',
        ]
        
        for pattern in informational_markers:
            if re.search(pattern, text, re.IGNORECASE):
                return "informational"
        
        # Default to general
        return "general"
    
    def _extract_entities(self, text: str) -> List[Dict[str, str]]:
        """Extract named entities from text (simplified)."""
        # This is a very simplified entity extraction
        # In a real implementation, you would use NER models
        
        entities = []
        
        # Extract potential person names (simplified)
        person_pattern = r'(?:[A-Z][a-z]+\s+){1,2}[A-Z][a-z]+'
        person_matches = re.findall(person_pattern, text)
        for match in person_matches[:5]:  # Limit to 5 matches
            entities.append({"type": "person", "value": match})
        
        # Extract potential organizations (simplified)
        org_pattern = r'(?:[A-Z][a-z]*\s*){2,}(?:Inc|LLC|Ltd|Corp|Corporation|Company)'
        org_matches = re.findall(org_pattern, text)
        for match in org_matches[:5]:  # Limit to 5 matches
            entities.append({"type": "organization", "value": match})
        
        # Extract potential locations (simplified)
        location_pattern = r'(?:in|at|from|to)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})'
        location_matches = re.findall(location_pattern, text)
        for match in location_matches[:5]:  # Limit to 5 matches
            entities.append({"type": "location", "value": match})
        
        # Extract dates (simplified)
        date_pattern = r'\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})\b'
        date_matches = re.findall(date_pattern, text, re.IGNORECASE)
        for match in date_matches[:5]:  # Limit to 5 matches
            entities.append({"type": "date", "value": match})
        
        return entities
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text (simplified)."""
        # This is a very simplified keyword extraction
        # In a real implementation, you would use more sophisticated algorithms
        
        # Remove common punctuation and convert to lowercase
        cleaned_text = re.sub(r'[^\w\s]', ' ', text.lower())
        
        # Split into words
        words = cleaned_text.split()
        
        # Remove common stop words (simplified list)
        stop_words = {
            "the", "and", "is", "in", "to", "of", "that", "for", "it", "with",
            "as", "was", "be", "this", "have", "from", "a", "an", "are", "were",
            "by", "on", "not", "they", "but", "or", "at", "what", "which", "who",
            "when", "where", "how", "why", "all", "their", "there", "has", "had",
            "would", "could", "should", "will", "can", "may", "about", "if"
        }
        
        filtered_words = [word for word in words if word not in stop_words and len(word) > 3]
        
        # Count word frequencies
        word_counts = {}
        for word in filtered_words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # Sort by frequency
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Return top keywords (up to 10)
        return [word for word, count in sorted_words[:10]]
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate a hash of the content for deduplication."""
        # Normalize content by removing whitespace and converting to lowercase
        normalized_content = re.sub(r'\s+', ' ', content.lower()).strip()
        
        # Generate SHA-256 hash
        return hashlib.sha256(normalized_content.encode('utf-8')).hexdigest()
    
    def _normalize_string(self, text: str) -> str:
        """Normalize a string for indexing."""
        # Convert to lowercase
        text = text.lower()
        
        # Remove diacritics
        text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
        
        # Remove punctuation
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _tokenize_string(self, text: str) -> List[str]:
        """Tokenize a string into words for partial matching."""
        # Normalize first
        normalized = self._normalize_string(text)
        
        # Split into words
        words = normalized.split()
        
        # Filter out short words
        return [word for word in words if len(word) > 2]