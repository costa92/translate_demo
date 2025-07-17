#!/usr/bin/env python3
"""
Setup script for Notion database for knowledge base storage.
This script creates the required database structure in Notion.
"""

import asyncio
import logging
import os
import json
from typing import Dict, Any
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NotionDatabaseSetup:
    """Setup Notion database for knowledge base storage."""
    
    def __init__(self, api_key: str, parent_page_id: str):
        """
        Initialize setup with Notion credentials.
        
        Args:
            api_key: Notion integration API key
            parent_page_id: ID of the parent page where database will be created
        """
        self.api_key = api_key
        self.parent_page_id = parent_page_id
        self.base_url = "https://api.notion.com/v1"
        self.client = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            },
            timeout=30.0
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()
    
    async def create_knowledge_base_database(self) -> str:
        """
        Create a new database for knowledge base storage.
        
        Returns:
            Database ID of the created database
        """
        logger.info("Creating knowledge base database in Notion...")
        
        # Define database schema
        database_schema = {
            "parent": {
                "type": "page_id",
                "page_id": self.parent_page_id
            },
            "title": [
                {
                    "type": "text",
                    "text": {
                        "content": "Knowledge Base Chunks"
                    }
                }
            ],
            "properties": {
                "Chunk ID": {
                    "title": {}
                },
                "Document ID": {
                    "rich_text": {}
                },
                "Text": {
                    "rich_text": {}
                },
                "Start Index": {
                    "number": {
                        "format": "number"
                    }
                },
                "End Index": {
                    "number": {
                        "format": "number"
                    }
                },
                "Embedding": {
                    "rich_text": {}
                },
                "Metadata": {
                    "rich_text": {}
                },
                "Created": {
                    "date": {}
                },
                "Document Type": {
                    "select": {
                        "options": [
                            {
                                "name": "Text",
                                "color": "blue"
                            },
                            {
                                "name": "PDF",
                                "color": "red"
                            },
                            {
                                "name": "Markdown",
                                "color": "green"
                            },
                            {
                                "name": "URL",
                                "color": "yellow"
                            }
                        ]
                    }
                },
                "Source": {
                    "url": {}
                },
                "Tags": {
                    "multi_select": {
                        "options": [
                            {
                                "name": "Important",
                                "color": "red"
                            },
                            {
                                "name": "Reference",
                                "color": "blue"
                            },
                            {
                                "name": "Draft",
                                "color": "gray"
                            }
                        ]
                    }
                }
            }
        }
        
        try:
            response = await self.client.post("/databases", json=database_schema)
            
            if response.status_code != 200:
                raise Exception(f"Failed to create database: {response.status_code} - {response.text}")
            
            database_info = response.json()
            database_id = database_info["id"]
            
            logger.info(f"Successfully created database with ID: {database_id}")
            return database_id
            
        except Exception as e:
            logger.error(f"Failed to create database: {e}")
            raise
    
    async def verify_database_access(self, database_id: str) -> Dict[str, Any]:
        """
        Verify access to the database and return its information.
        
        Args:
            database_id: ID of the database to verify
            
        Returns:
            Database information
        """
        logger.info(f"Verifying access to database: {database_id}")
        
        try:
            response = await self.client.get(f"/databases/{database_id}")
            
            if response.status_code != 200:
                raise Exception(f"Cannot access database: {response.status_code} - {response.text}")
            
            database_info = response.json()
            
            logger.info(f"Database access verified: {database_info.get('title', [{}])[0].get('plain_text', 'Unknown')}")
            return database_info
            
        except Exception as e:
            logger.error(f"Failed to verify database access: {e}")
            raise
    
    async def add_sample_data(self, database_id: str) -> None:
        """
        Add sample data to the database for testing.
        
        Args:
            database_id: ID of the database
        """
        logger.info("Adding sample data to database...")
        
        sample_chunks = [
            {
                "chunk_id": "sample_001",
                "document_id": "doc_sample",
                "text": "This is a sample chunk for testing the Notion knowledge base integration.",
                "start_index": 0,
                "end_index": 80,
                "metadata": {"source": "setup_script", "type": "sample"}
            },
            {
                "chunk_id": "sample_002", 
                "document_id": "doc_sample",
                "text": "Another sample chunk to demonstrate the storage capabilities of the system.",
                "start_index": 81,
                "end_index": 160,
                "metadata": {"source": "setup_script", "type": "sample"}
            }
        ]
        
        for chunk in sample_chunks:
            await self._add_sample_chunk(database_id, chunk)
        
        logger.info(f"Added {len(sample_chunks)} sample chunks to database")
    
    async def _add_sample_chunk(self, database_id: str, chunk_data: Dict[str, Any]) -> None:
        """Add a single sample chunk to the database."""
        page_data = {
            "parent": {
                "database_id": database_id
            },
            "properties": {
                "Chunk ID": {
                    "title": [
                        {
                            "text": {
                                "content": chunk_data["chunk_id"]
                            }
                        }
                    ]
                },
                "Document ID": {
                    "rich_text": [
                        {
                            "text": {
                                "content": chunk_data["document_id"]
                            }
                        }
                    ]
                },
                "Text": {
                    "rich_text": [
                        {
                            "text": {
                                "content": chunk_data["text"]
                            }
                        }
                    ]
                },
                "Start Index": {
                    "number": chunk_data["start_index"]
                },
                "End Index": {
                    "number": chunk_data["end_index"]
                },
                "Metadata": {
                    "rich_text": [
                        {
                            "text": {
                                "content": json.dumps(chunk_data["metadata"])
                            }
                        }
                    ]
                },
                "Document Type": {
                    "select": {
                        "name": "Text"
                    }
                },
                "Tags": {
                    "multi_select": [
                        {
                            "name": "Reference"
                        }
                    ]
                }
            }
        }
        
        response = await self.client.post("/pages", json=page_data)
        
        if response.status_code != 200:
            raise Exception(f"Failed to create sample page: {response.status_code} - {response.text}")


async def main():
    """Main setup function."""
    print("🚀 Notion Knowledge Base Database Setup")
    print("=" * 50)
    
    # Get configuration from environment or user input
    api_key = os.getenv("NOTION_API_KEY")
    parent_page_id = os.getenv("NOTION_PARENT_PAGE_ID")
    
    if not api_key:
        api_key = input("Enter your Notion API key: ").strip()
    
    if not parent_page_id:
        parent_page_id = input("Enter the parent page ID where the database will be created: ").strip()
    
    if not api_key or not parent_page_id:
        print("❌ API key and parent page ID are required!")
        return
    
    try:
        async with NotionDatabaseSetup(api_key, parent_page_id) as setup:
            # Create database
            database_id = await setup.create_knowledge_base_database()
            
            # Verify access
            db_info = await setup.verify_database_access(database_id)
            
            # Add sample data
            add_samples = input("Add sample data? (y/n): ").strip().lower()
            if add_samples in ['y', 'yes']:
                await setup.add_sample_data(database_id)
            
            print("\n✅ Setup completed successfully!")
            print(f"📊 Database ID: {database_id}")
            print(f"📝 Database Name: {db_info.get('title', [{}])[0].get('plain_text', 'Unknown')}")
            
            # Generate configuration
            print("\n📋 Configuration for your knowledge base:")
            print("=" * 50)
            print(f"NOTION_API_KEY={api_key}")
            print(f"NOTION_DATABASE_ID={database_id}")
            
            print("\n🔧 Or use in your config file:")
            config_example = {
                "storage": {
                    "provider": "notion",
                    "notion_api_key": api_key,
                    "notion_database_id": database_id
                }
            }
            print(json.dumps(config_example, indent=2))
            
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        logger.error(f"Setup failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())