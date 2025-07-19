# Metadata Extraction

The unified knowledge base system includes powerful metadata extraction capabilities that automatically generate and enhance metadata for documents and text chunks. This metadata can be used for filtering, sorting, and improving search relevance.

## Overview

The metadata extraction system consists of several components:

1. **Document Metadata Extraction**: Extracts metadata from documents based on their content and type.
2. **Chunk Metadata Extraction**: Extracts metadata from text chunks, including context from their parent documents.
3. **Automatic Metadata Generation**: Generates additional metadata through content analysis.
4. **Metadata Indexing**: Prepares metadata for efficient searching and filtering.

## Extracted Metadata

The system extracts different types of metadata depending on the document type:

### Common Metadata (All Documents)

- `document_id`: Unique identifier for the document
- `document_type`: Type of the document (text, markdown, html, code, etc.)
- `content_length`: Length of the document content in characters
- `extracted_at`: Timestamp when the metadata was extracted
- `source`: Source of the document (e.g., file path, URL)
- `content_hash`: Hash of the document content for deduplication
- `word_count`: Number of words in the document
- `language`: Detected language of the document
- `reading_level`: Estimated reading level (basic, intermediate, advanced)
- `content_type`: Categorization of the content (general, code, narrative, instructional, informational)
- `keywords`: Automatically extracted keywords from the content

### Text Document Metadata

- `paragraph_count`: Number of paragraphs in the text
- `estimated_reading_time_seconds`: Estimated time to read the document
- `contains_urls`: Whether the text contains URLs
- `url_count`: Number of URLs in the text
- `contains_emails`: Whether the text contains email addresses
- `email_count`: Number of email addresses in the text

### Markdown Document Metadata

- `header_count`: Number of headers in the markdown
- `title`: Title of the document (first h1 header)
- `code_block_count`: Number of code blocks
- `link_count`: Number of links
- `image_count`: Number of images
- `contains_tables`: Whether the markdown contains tables

### HTML Document Metadata

- `title`: Title of the HTML document
- `meta_*`: Values from meta tags
- `h1_count`, `h2_count`, etc.: Number of headings at each level
- `link_count`: Number of links
- `image_count`: Number of images
- `contains_tables`: Whether the HTML contains tables
- `contains_forms`: Whether the HTML contains forms
- `contains_scripts`: Whether the HTML contains scripts

### Code Document Metadata

- `code_lines`: Number of lines of code
- `comment_lines`: Number of comment lines
- `blank_lines`: Number of blank lines
- `total_lines`: Total number of lines
- `comment_ratio`: Ratio of comments to code
- `language`: Detected programming language
- `function_count`: Number of functions/methods
- `class_count`: Number of classes

### File Metadata

- `filename`: Name of the file
- `file_size`: Size of the file in bytes
- `mime_type`: MIME type of the file
- `created_time`: Creation time of the file
- `modified_time`: Last modification time of the file
- `file_extension`: Extension of the file
- `file_path`: Absolute path to the file

### Chunk Metadata

- `chunk_id`: Unique identifier for the chunk
- `document_id`: ID of the parent document
- `chunk_length`: Length of the chunk in characters
- `start_index`: Starting position in the original document
- `end_index`: Ending position in the original document
- `chunk_index`: Index of the chunk within the document
- `chunk_count`: Total number of chunks in the document
- `content_hash`: Hash of the chunk content for deduplication

## Configuration

Metadata extraction can be configured in the system configuration:

```python
config = Config()

# Enable/disable metadata extraction
config.chunking.extract_metadata = True

# Enable/disable automatic metadata generation
config.chunking.generate_automatic_metadata = True

# Enable/disable metadata indexing
config.chunking.index_metadata = True

# Specify fields to extract (empty list means all fields)
config.chunking.metadata_fields_to_extract = []

# Specify fields to index (empty list means all fields)
config.chunking.metadata_fields_to_index = []
```

## Usage

### Extracting Metadata from a Document

```python
from src.knowledge_base.core.config import Config
from src.knowledge_base.processing.processor import DocumentProcessor

# Create configuration
config = Config()
config.chunking.extract_metadata = True

# Create document processor
processor = DocumentProcessor(config)

# Process file into document with metadata
document = await processor.process_file("path/to/document.txt")

# Access metadata
print(document.metadata)
```

### Using the Command-Line Tool

The system includes a command-line tool for extracting metadata from documents:

```bash
# Extract metadata from a single file
python -m src.knowledge_base.tools.extract_metadata path/to/document.txt --output metadata.json

# Extract metadata from multiple files
python -m src.knowledge_base.tools.extract_metadata file1.txt file2.md file3.py --output metadata_dir/

# Enable verbose logging
python -m src.knowledge_base.tools.extract_metadata path/to/document.txt -v
```

## Metadata Indexing

The metadata indexing process prepares metadata for efficient searching and filtering:

1. **Original Values Preservation**: Keeps the original values for all metadata fields.
2. **String Normalization**: Adds normalized versions of string values by removing diacritics, converting to lowercase, and removing punctuation.
3. **Tokenization**: Splits strings into tokens for partial matching.
4. **Case-Insensitive Search**: Adds lowercase versions of string fields for case-insensitive search.

This allows for more flexible and powerful search capabilities, such as:

- Case-insensitive search
- Partial matching
- Filtering by metadata fields
- Sorting by metadata fields
- Faceted search