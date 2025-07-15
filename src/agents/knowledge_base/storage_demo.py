#!/usr/bin/env python3
"""
存储提供者使用示例
演示如何使用不同的存储提供者（Notion、OSS）
"""

import sys
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from orchestrator_agent import OrchestratorAgent

def demo_notion_storage():
    """演示Notion存储提供者"""
    print("🔗 Notion存储提供者演示")
    print("=" * 50)
    
    # Notion配置示例
    notion_config = {
        "notion_token": "your_notion_integration_token",
        "database_id": "your_database_id"
    }
    
    print("📝 配置要求:")
    print("1. 创建Notion集成：https://www.notion.so/my-integrations")
    print("2. 获取Integration Token")
    print("3. 创建数据库并获取Database ID")
    print("4. 确保数据库包含以下属性：")
    print("   - chunk_id (标题)")
    print("   - content (富文本)")
    print("   - category (选择)")
    print("   - metadata (富文本)")
    print("5. 将集成添加到数据库")
    
    print("\n💡 使用示例:")
    print("notion_config = {")
    print('    "notion_token": "secret_xxxxxxxxxxxx",')
    print('    "database_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"')
    print("}")
    print("orchestrator = OrchestratorAgent(")
    print('    storage_provider="notion",')
    print("    storage_config=notion_config")
    print(")")
    
    # 如果配置已设置，尝试初始化
    if notion_config["notion_token"] != "your_notion_integration_token":
        try:
            orchestrator = OrchestratorAgent(
                storage_provider="notion",
                storage_config=notion_config
            )
            print("✅ Notion存储提供者初始化成功")
            
            # 演示添加知识
            sample_data = {
                "sources": [
                    {
                        "type": "text",
                        "location": "这是存储在Notion中的示例知识块",
                        "metadata": {"source": "demo"}
                    }
                ]
            }
            
            result = orchestrator.receive_request("demo", "add_knowledge", sample_data)
            print(f"添加知识结果: {result}")
            
        except Exception as e:
            print(f"❌ 初始化失败: {e}")
    else:
        print("⚠️  请先配置Notion token和database_id")

def demo_oss_storage():
    """演示OSS存储提供者"""
    print("\n🗄️  OSS存储提供者演示")
    print("=" * 50)
    
    # OSS配置示例
    oss_config = {
        "endpoint": "https://oss-cn-beijing.aliyuncs.com",
        "access_key_id": "your_access_key_id",
        "access_key_secret": "your_access_key_secret",
        "bucket_name": "your_bucket_name",
        "prefix": "knowledge_base/"
    }
    
    print("📝 配置要求:")
    print("1. 安装OSS2库：pip install oss2")
    print("2. 创建阿里云OSS Bucket")
    print("3. 获取AccessKey ID和Secret")
    print("4. 配置Bucket权限")
    
    print("\n💡 使用示例:")
    print("oss_config = {")
    print('    "endpoint": "https://oss-cn-beijing.aliyuncs.com",')
    print('    "access_key_id": "LTAI4GxxxxxxxxxxxxxxxxxxE",')
    print('    "access_key_secret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",')
    print('    "bucket_name": "my-knowledge-base",')
    print('    "prefix": "knowledge_chunks/"')
    print("}")
    print("orchestrator = OrchestratorAgent(")
    print('    storage_provider="oss",')
    print("    storage_config=oss_config")
    print(")")
    
    # 如果配置已设置，尝试初始化
    if oss_config["access_key_id"] != "your_access_key_id":
        try:
            orchestrator = OrchestratorAgent(
                storage_provider="oss",
                storage_config=oss_config
            )
            print("✅ OSS存储提供者初始化成功")
            
            # 演示添加知识
            sample_data = {
                "sources": [
                    {
                        "type": "text",
                        "location": "这是存储在OSS中的示例知识块",
                        "metadata": {"source": "demo"}
                    }
                ]
            }
            
            result = orchestrator.receive_request("demo", "add_knowledge", sample_data)
            print(f"添加知识结果: {result}")
            
        except Exception as e:
            print(f"❌ 初始化失败: {e}")
    else:
        print("⚠️  请先配置OSS访问凭证")

def demo_memory_storage():
    """演示内存存储提供者（默认）"""
    print("\n🧠 内存存储提供者演示")
    print("=" * 50)
    
    try:
        # 内存存储不需要配置
        orchestrator = OrchestratorAgent(storage_provider="memory")
        print("✅ 内存存储提供者初始化成功")
        
        # 演示完整流程
        sample_data = {
            "sources": [
                {
                    "type": "text",
                    "location": "内存存储是最简单的存储方式，数据存储在内存中，应用重启后会丢失。适合开发和测试使用。",
                    "metadata": {"type": "storage", "category": "memory"}
                },
                {
                    "type": "text",
                    "location": "Notion存储将知识块存储为Notion数据库中的页面，支持丰富的元数据和搜索功能。",
                    "metadata": {"type": "storage", "category": "notion"}
                },
                {
                    "type": "text",
                    "location": "OSS存储将知识块存储为对象存储中的JSON文件，提供持久化和高可用性。",
                    "metadata": {"type": "storage", "category": "oss"}
                }
            ]
        }
        
        # 添加知识
        result = orchestrator.receive_request("demo", "add_knowledge", sample_data)
        print(f"添加知识结果: {result}")
        
        if result.get("status") == "success":
            # 查询知识
            queries = [
                "什么是内存存储？",
                "Notion存储的特点是什么？",
                "OSS存储有什么优势？"
            ]
            
            for query in queries:
                print(f"\n🔍 查询: {query}")
                result = orchestrator.receive_request("demo", "query", {"query": query})
                if result.get("status") == "success":
                    print(f"💡 答案: {result.get('answer', '')[:100]}...")
                    print(f"📚 相关源数量: {result.get('sources_count', 0)}")
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")

def main():
    """主演示函数"""
    print("🚀 知识库存储提供者演示")
    print("=" * 60)
    
    # 演示不同的存储提供者
    demo_memory_storage()
    demo_notion_storage()
    demo_oss_storage()
    
    print("\n📋 总结:")
    print("1. 内存存储 - 开发测试，即开即用")
    print("2. Notion存储 - 团队协作，可视化管理")
    print("3. OSS存储 - 生产环境，高可用性")
    print("4. Google Drive存储 - 个人使用，易于分享")
    
    print("\n💡 选择建议:")
    print("- 开发阶段：使用内存存储")
    print("- 团队协作：使用Notion存储")
    print("- 生产部署：使用OSS存储")
    print("- 个人项目：使用Google Drive存储")
    
    print("\n🔧 下一步:")
    print("1. 根据需求选择合适的存储提供者")
    print("2. 配置相应的访问凭证")
    print("3. 集成到您的应用中")

if __name__ == "__main__":
    main()