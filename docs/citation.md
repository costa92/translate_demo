# Source Citation in the Knowledge Base System

This document describes the source citation functionality in the unified knowledge base system.

## Overview

Source citation is a critical feature for retrieval-augmented generation (RAG) systems, as it provides transparency and credibility to generated answers. The citation system in the knowledge base allows for:

1. **Reference Tracking**: Keeping track of which sources were used to generate an answer
2. **Source Attribution**: Adding citation markers to the generated text
3. **Citation Generation**: Creating properly formatted citations for sources

## Components

### Citation

The `Citation` class represents a citation to a source document. It contains:

- `chunk_id`: ID of the cited text chunk
- `document_id`: ID of the document containing the chunk
- `text_snippet`: Short snippet of the cited text
- `relevance_score`: Relevance score of the chunk to the query
- `metadata`: Additional information about the citation

### ReferenceTracker

The `ReferenceTracker` class tracks references to sources in generated content:

- `add_citation(citation)`: Adds a citation and returns a citation marker
- `get_citation(marker)`: Gets a citation by its marker
- `get_all_citations()`: Gets all citations in order

### CitationGenerator

The `CitationGenerator` class generates citations for sources:

- `generate_citations(sources)`: Generates citations for a list of sources
- `format_citation_text(citation)`: Formats a citation as text
- `format_references_section(tracker)`: Formats a references section

### SourceAttributor

The `SourceAttributor` class attributes sources in generated content:

- `attribute_sources(answer, sources)`: Attributes sources in an answer
- `create_attributed_result(query, answer, sources)`: Creates a query result with attributed sources

## Usage

### Basic Usage

```python
from src.knowledge_base.core.config import Config
from src.knowledge_base.generation.generator import Generator

# Create a configuration
config = Config()
config.generation.include_citations = True

# Create a generator
generator = Generator(config)

# Generate an answer with citations
result = await generator.generate(query, chunks, include_citations=True)

# The result will be a QueryResult object with attributed sources
print(result.answer)  # Contains the answer with citation markers and a references section
```

### Direct Use of SourceAttributor

```python
from src.knowledge_base.core.config import Config
from src.knowledge_base.core.types import RetrievalResult
from src.knowledge_base.generation.citation import SourceAttributor

# Create a configuration
config = Config()
config.generation.citation_style = "numbered"
config.generation.include_references_section = True

# Create a source attributor
attributor = SourceAttributor(config)

# Create retrieval results
sources = [RetrievalResult(chunk=chunk, score=0.95, rank=1) for chunk in chunks]

# Attribute sources in an answer
attributed_answer, references_section = attributor.attribute_sources(answer, sources)

# Create a query result with attributed sources
result = attributor.create_attributed_result(query, answer, sources)
```

## Configuration Options

The citation system can be configured through the following options in the `generation` section of the configuration:

- `citation_style`: The style of citation markers ("numbered" or "bullet")
- `include_references_section`: Whether to include a references section in the answer
- `include_citations`: Whether to include citations in generated answers

## Citation Styles

The system supports different citation styles:

### Numbered Style

```
This is a sentence with a citation [1]. This is another sentence with a citation [2].

## References

1. Author. (2023). Title. Publisher.
2. Author. (2023). Title. Journal, Volume(Issue), Pages.
```

### Bullet Style

```
This is a sentence with a citation [1]. This is another sentence with a citation [2].

## References

- Author. (2023). Title. Publisher.
- Author. (2023). Title. Journal, Volume(Issue), Pages.
```

## Metadata for Citations

The citation system uses metadata from the text chunks to format citations. The following metadata fields are used:

- `title`: The title of the document
- `author`: The author of the document
- `date`: The date of the document
- `source_type`: The type of source (document, webpage, book, article)
- `url`: The URL of the source (for webpages)
- `publisher`: The publisher of the source (for books)
- `journal`: The journal name (for articles)
- `volume`: The volume number (for articles)
- `issue`: The issue number (for articles)
- `pages`: The page range (for articles)

## Example

```python
# Generate an answer with citations
result = await generator.generate(
    query="Tell me about Earth and its atmosphere.",
    chunks=chunks,
    include_citations=True
)

# The answer might look like:
"""
Earth is the third planet from the Sun and the only place known to support life [1]. 
The Earth's atmosphere is composed primarily of nitrogen (78%) and oxygen (21%), 
with trace amounts of other gases [2].

## References

1. Science Encyclopedia. (2022-05-15). Earth Facts.
2. Environmental Science Journal. (2023-01-10). Atmospheric Composition. Environmental Science, 45(2).
"""
```