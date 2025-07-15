#!/usr/bin/env python3
"""
测试脚本：验证知识库多智能体系统的基本功能
"""

import os
import sys
import time
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from orchestrator_agent import OrchestratorAgent

def test_basic_functionality():
    """测试基本功能"""
    print("=== 测试知识库多智能体系统 ===")
    
    # 初始化协调智能体
    print("\n1. 初始化协调智能体...")
    orchestrator = OrchestratorAgent(
        storage_provider='memory',
        storage_config={}
    )
    
    # 检查系统状态
    print("\n2. 检查系统状态...")
    status = orchestrator.get_agent_status()
    print(f"已注册的智能体: {status['registered_agents']}")
    print(f"存储提供者: {status['storage_provider']}")
    
    # 测试知识添加
    print("\n3. 测试知识添加...")
    test_knowledge = {
        "sources": [
            {
                "type": "text",
                "location": "Python是一种高级编程语言，由Guido van Rossum于1991年首次发布。Python设计哲学强调代码的可读性和简洁性。",
                "metadata": {"topic": "programming", "language": "python"}
            },
            {
                "type": "text", 
                "location": "FastAPI是一个现代、快速（高性能）的Web框架，用于构建Python API。它基于标准Python类型提示，支持异步编程。",
                "metadata": {"topic": "web_framework", "language": "python"}
            }
        ],
        "processing_options": {}
    }
    
    result = orchestrator.receive_request("test", "add_knowledge", test_knowledge)
    print(f"添加知识结果: {result}")
    
    if result.get("status") == "success":
        print(f"成功处理了 {result.get('chunks_count', 0)} 个知识块")
    
    # 测试知识查询
    print("\n4. 测试知识查询...")
    queries = [
        "什么是Python？",
        "FastAPI有什么特点？",
        "编程语言的设计哲学是什么？"
    ]
    
    for query in queries:
        print(f"\n查询: {query}")
        query_payload = {
            "query": query,
            "search_params": {}
        }
        
        result = orchestrator.receive_request("test", "query", query_payload)
        
        if result.get("status") == "success":
            print(f"答案: {result.get('answer', 'No answer')[:200]}...")
            print(f"找到 {result.get('sources_count', 0)} 个相关源")
        else:
            print(f"查询失败: {result.get('message', 'Unknown error')}")
    
    # 测试存储状态
    print("\n5. 检查存储状态...")
    storage_agent = orchestrator.agents.get('KnowledgeStorageAgent')
    if storage_agent:
        chunk_ids = storage_agent.get_all_chunk_ids()
        print(f"存储的知识块数量: {len(chunk_ids)}")
        if chunk_ids:
            print(f"前3个知识块ID: {chunk_ids[:3]}")
    
    print("\n=== 测试完成 ===")

def test_file_processing():
    """测试文件处理功能"""
    print("\n=== 测试文件处理功能 ===")
    
    # 创建测试文件
    test_file = Path("test_knowledge.txt")
    test_content = """
    知识库多智能体系统
    
    本系统包含以下智能体：
    1. 协调智能体(OrchestratorAgent) - 总指挥
    2. 数据收集智能体(DataCollectionAgent) - 收集数据
    3. 知识处理智能体(KnowledgeProcessingAgent) - 处理数据
    4. 知识存储智能体(KnowledgeStorageAgent) - 存储数据
    5. 知识检索智能体(KnowledgeRetrievalAgent) - 检索数据
    6. 知识维护智能体(KnowledgeMaintenanceAgent) - 维护数据
    
    系统特点：
    - 模块化设计
    - 可扩展架构
    - 支持多种存储后端
    - 实现RAG（检索增强生成）
    """
    
    try:
        # 写入测试文件
        test_file.write_text(test_content.strip(), encoding='utf-8')
        print(f"创建测试文件: {test_file}")
        
        # 初始化系统
        orchestrator = OrchestratorAgent(storage_provider='memory', storage_config={})
        
        # 测试文件收集
        file_payload = {
            "sources": [
                {
                    "type": "file",
                    "path": str(test_file),
                    "metadata": {"source": "test_file"}
                }
            ]
        }
        
        result = orchestrator.receive_request("test", "add_knowledge", file_payload)
        print(f"文件处理结果: {result}")
        
        if result.get("status") == "success":
            # 测试基于文件内容的查询
            queries = [
                "系统包含哪些智能体？",
                "协调智能体的作用是什么？",
                "系统有什么特点？"
            ]
            
            for query in queries:
                print(f"\n查询: {query}")
                query_result = orchestrator.receive_request("test", "query", {"query": query})
                if query_result.get("status") == "success":
                    print(f"答案: {query_result.get('answer', 'No answer')[:150]}...")
                    
    except Exception as e:
        print(f"文件处理测试失败: {e}")
    finally:
        # 清理测试文件
        if test_file.exists():
            test_file.unlink()
            print(f"删除测试文件: {test_file}")

def test_error_handling():
    """测试错误处理"""
    print("\n=== 测试错误处理 ===")
    
    orchestrator = OrchestratorAgent(storage_provider='memory', storage_config={})
    
    # 测试无效请求类型
    result = orchestrator.receive_request("test", "invalid_type", {})
    print(f"无效请求类型: {result}")
    
    # 测试空查询
    result = orchestrator.receive_request("test", "query", {"query": ""})
    print(f"空查询: {result}")
    
    # 测试不存在的文件
    result = orchestrator.receive_request("test", "add_knowledge", {
        "sources": [{"type": "file", "path": "non_existent_file.txt"}]
    })
    print(f"不存在的文件: {result}")

if __name__ == "__main__":
    print("开始测试知识库多智能体系统...")
    
    try:
        test_basic_functionality()
        test_file_processing()
        test_error_handling()
        print("\n✅ 所有测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()