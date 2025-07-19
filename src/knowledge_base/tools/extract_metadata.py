#!/usr/bin/env python
"""
Command-line tool for extracting metadata from documents.

This tool demonstrates the metadata extraction capabilities of the unified knowledge base system.
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path to allow importing from src
sys.path.append(str(Path(__file__).parent.parent.parent))

from knowledge_base.core.config import Config
from knowledge_base.core.types import Document, DocumentType
from knowledge_base.processing.processor import DocumentProcessor
from knowledge_base.processing.metadata_extractor import MetadataExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("metadata_extractor")


async def extract_metadata(file_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract metadata from a document.
    
    Args:
        file_path: Path to the document file
        output_path: Optional path to save the metadata as JSON
        
    Returns:
        Dictionary of extracted metadata
    """
    # Create configuration
    config = Config()
    
    # Ensure metadata extraction is enabled
    config.chunking.extract_metadata = True
    config.chunking.generate_automatic_metadata = True
    config.chunking.index_metadata = True
    
    # Create document processor
    processor = DocumentProcessor(config)
    
    try:
        # Process file into document
        document = await processor.process_file(file_path)
        
        # Extract metadata
        metadata = document.metadata
        
        # Print metadata summary
        logger.info(f"Extracted {len(metadata)} metadata fields from {file_path}")
        
        # Save metadata to file if output path is provided
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, default=str)
            logger.info(f"Saved metadata to {output_path}")
        
        return metadata
        
    finally:
        # Clean up resources
        await processor.close()


async def extract_metadata_batch(file_paths: List[str], output_dir: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """
    Extract metadata from multiple documents.
    
    Args:
        file_paths: List of paths to document files
        output_dir: Optional directory to save the metadata as JSON files
        
    Returns:
        Dictionary mapping file paths to their extracted metadata
    """
    # Create configuration
    config = Config()
    
    # Ensure metadata extraction is enabled
    config.chunking.extract_metadata = True
    config.chunking.generate_automatic_metadata = True
    config.chunking.index_metadata = True
    
    # Create document processor
    processor = DocumentProcessor(config)
    
    try:
        results = {}
        
        # Create output directory if needed
        if output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Process each file
        for file_path in file_paths:
            try:
                # Process file into document
                document = await processor.process_file(file_path)
                
                # Extract metadata
                metadata = document.metadata
                
                # Save results
                results[file_path] = metadata
                
                # Print metadata summary
                logger.info(f"Extracted {len(metadata)} metadata fields from {file_path}")
                
                # Save metadata to file if output directory is provided
                if output_dir:
                    output_path = Path(output_dir) / f"{Path(file_path).stem}_metadata.json"
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, indent=2, default=str)
                    logger.info(f"Saved metadata to {output_path}")
                    
            except Exception as e:
                logger.error(f"Failed to extract metadata from {file_path}: {e}")
                results[file_path] = {"error": str(e)}
        
        return results
        
    finally:
        # Clean up resources
        await processor.close()


def main():
    """Main entry point for the command-line tool."""
    parser = argparse.ArgumentParser(description="Extract metadata from documents")
    parser.add_argument("files", nargs="+", help="Paths to document files")
    parser.add_argument("--output", "-o", help="Output path for metadata (file or directory)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Extract metadata
    if len(args.files) == 1:
        # Single file mode
        asyncio.run(extract_metadata(args.files[0], args.output))
    else:
        # Batch mode
        asyncio.run(extract_metadata_batch(args.files, args.output))


if __name__ == "__main__":
    main()