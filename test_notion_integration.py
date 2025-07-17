#!/usr/bin/env python3
"""
Simple integration test to verify Notion storage is properly integrated.
This test doesn't require actual Notion credentials.
"""

import asyncio
import logging
from knowledge_base.core.config import Config, StorageConfig
from knowledge_base.storage.vector_store import VectorStore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_notion_integration():
    """Test that Notion storage provider is properly integrated."""
    print("🧪 Testing Notion Storage Integration")
    print("=" * 50)
    
    try:
        # Test 1: Configuration validation
        print("1. Testing configuration validation...")
        
        try:
            from knowledge_base.core.config import GenerationConfig
            config = Config(
                storage=StorageConfig(
                    provider="notion",
                    notion_api_key="test_key",
                    notion_database_id="test_db_id"
                ),
                generation=GenerationConfig(
                    provider="simple"  # Use simple provider to avoid API key requirement
                )
            )
            config.validate()
            print("   ✅ Configuration validation passed")
        except Exception as e:
            print(f"   ❌ Configuration validation failed: {e}")
            return False
        
        # Test 2: Provider registration
        print("2. Testing provider registration...")
        
        try:
            vector_store = VectorStore(config.storage)
            # This should not raise an exception for unknown provider
            print("   ✅ Notion provider is registered")
        except Exception as e:
            print(f"   ❌ Provider registration failed: {e}")
            return False
        
        # Test 3: Import test
        print("3. Testing module imports...")
        
        try:
            from knowledge_base.storage.providers.notion import NotionVectorStore
            print("   ✅ NotionVectorStore import successful")
        except ImportError as e:
            print(f"   ❌ Import failed: {e}")
            return False
        
        # Test 4: Class instantiation (without initialization)
        print("4. Testing class instantiation...")
        
        try:
            notion_store = NotionVectorStore(config.storage.__dict__)
            print("   ✅ NotionVectorStore instantiation successful")
        except Exception as e:
            print(f"   ❌ Instantiation failed: {e}")
            return False
        
        # Test 5: Configuration error handling
        print("5. Testing configuration error handling...")
        
        try:
            # Test missing API key
            invalid_config = StorageConfig(
                provider="notion",
                notion_database_id="test_db_id"
                # Missing notion_api_key
            )
            
            try:
                NotionVectorStore(invalid_config.__dict__)
                print("   ❌ Should have failed with missing API key")
                return False
            except Exception:
                print("   ✅ Properly handles missing API key")
            
            # Test missing database ID
            invalid_config2 = StorageConfig(
                provider="notion",
                notion_api_key="test_key"
                # Missing notion_database_id
            )
            
            try:
                NotionVectorStore(invalid_config2.__dict__)
                print("   ❌ Should have failed with missing database ID")
                return False
            except Exception:
                print("   ✅ Properly handles missing database ID")
                
        except Exception as e:
            print(f"   ❌ Error handling test failed: {e}")
            return False
        
        print("\n🎉 All integration tests passed!")
        print("Notion storage provider is properly integrated into the system.")
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        return False


async def test_config_validation():
    """Test configuration validation for Notion provider."""
    print("\n🔧 Testing Configuration Validation")
    print("=" * 50)
    
    test_cases = [
        {
            "name": "Valid Notion config",
            "config": {
                "provider": "notion",
                "notion_api_key": "test_key",
                "notion_database_id": "test_db_id"
            },
            "should_pass": True
        },
        {
            "name": "Missing API key",
            "config": {
                "provider": "notion",
                "notion_database_id": "test_db_id"
            },
            "should_pass": False
        },
        {
            "name": "Missing database ID",
            "config": {
                "provider": "notion",
                "notion_api_key": "test_key"
            },
            "should_pass": False
        },
        {
            "name": "Invalid provider",
            "config": {
                "provider": "invalid_provider"
            },
            "should_pass": False
        }
    ]
    
    passed = 0
    total = len(test_cases)
    
    for test_case in test_cases:
        print(f"Testing: {test_case['name']}")
        
        try:
            from knowledge_base.core.config import GenerationConfig
            config = Config(
                storage=StorageConfig(**test_case["config"]),
                generation=GenerationConfig(provider="simple")  # Use simple provider
            )
            config.validate()
            
            if test_case["should_pass"]:
                print("   ✅ Passed (as expected)")
                passed += 1
            else:
                print("   ❌ Should have failed but passed")
        
        except Exception as e:
            if not test_case["should_pass"]:
                print("   ✅ Failed (as expected)")
                passed += 1
            else:
                print(f"   ❌ Should have passed but failed: {e}")
    
    print(f"\nConfiguration validation tests: {passed}/{total} passed")
    return passed == total


async def main():
    """Main test function."""
    print("🚀 Notion Storage Integration Test Suite")
    print("=" * 60)
    
    # Run integration tests
    integration_passed = await test_notion_integration()
    
    # Run configuration tests
    config_passed = await test_config_validation()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    if integration_passed and config_passed:
        print("🎉 All tests passed! Notion storage is ready to use.")
        print("\nNext steps:")
        print("1. Set up your Notion integration and database")
        print("2. Run: python setup_notion_database.py")
        print("3. Run: python test_notion_storage.py")
    else:
        print("❌ Some tests failed. Please check the implementation.")
        
        if not integration_passed:
            print("- Integration tests failed")
        if not config_passed:
            print("- Configuration tests failed")


if __name__ == "__main__":
    asyncio.run(main())