#!/usr/bin/env python3
"""
API测试脚本：测试FastAPI接口
"""

import requests
import json
import time
from typing import Dict, Any

API_BASE_URL = "http://localhost:8000"

def test_api_endpoints():
    """测试API端点"""
    print("=== 测试FastAPI端点 ===")
    
    # 测试健康检查
    print("\n1. 测试健康检查...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"健康检查状态: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"健康检查失败: {e}")
        return False
    
    # 测试系统状态
    print("\n2. 测试系统状态...")
    try:
        response = requests.get(f"{API_BASE_URL}/status")
        print(f"系统状态: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"系统状态检查失败: {e}")
        return False
    
    # 测试添加知识
    print("\n3. 测试添加知识...")
    knowledge_data = {
        "sources": [
            {
                "type": "text",
                "location": "人工智能（AI）是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。",
                "metadata": {"topic": "AI", "language": "chinese"}
            },
            {
                "type": "text",
                "location": "机器学习是人工智能的一个子集，通过算法和统计模型使计算机能够在没有明确编程的情况下学习和改进。",
                "metadata": {"topic": "ML", "language": "chinese"}
            }
        ],
        "processing_options": {}
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/knowledge",
            json=knowledge_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"添加知识状态: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"添加知识失败: {e}")
        return False
    
    # 等待一下确保知识被处理
    time.sleep(1)
    
    # 测试查询知识
    print("\n4. 测试知识查询...")
    queries = [
        "什么是人工智能？",
        "机器学习的特点是什么？",
        "AI和ML有什么关系？"
    ]
    
    for query in queries:
        print(f"\n查询: {query}")
        query_data = {
            "query": query,
            "search_params": {}
        }
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/v1/chat/query",
                json=query_data,
                headers={"Content-Type": "application/json"}
            )
            print(f"查询状态: {response.status_code}")
            result = response.json()
            print(f"答案: {result.get('answer', 'No answer')[:200]}...")
            print(f"找到 {result.get('sources_count', 0)} 个相关源")
        except Exception as e:
            print(f"查询失败: {e}")
    
    # 测试调试端点
    print("\n5. 测试调试端点...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/debug/agents")
        print(f"调试智能体状态: {response.status_code}")
        print(f"响应: {response.json()}")
        
        response = requests.get(f"{API_BASE_URL}/api/v1/debug/storage")
        print(f"调试存储状态: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"调试端点测试失败: {e}")
    
    return True

def test_error_cases():
    """测试错误情况"""
    print("\n=== 测试错误处理 ===")
    
    # 测试空查询
    print("\n1. 测试空查询...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/chat/query",
            json={"query": ""},
            headers={"Content-Type": "application/json"}
        )
        print(f"空查询状态: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"空查询测试失败: {e}")
    
    # 测试无效数据
    print("\n2. 测试无效知识源...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/knowledge",
            json={"sources": [{"type": "invalid", "location": "test"}]},
            headers={"Content-Type": "application/json"}
        )
        print(f"无效知识源状态: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"无效知识源测试失败: {e}")

if __name__ == "__main__":
    print("开始测试FastAPI接口...")
    print("请确保API服务器正在运行: python -m src.agents.knowledge_base.api_server")
    
    # 等待用户确认
    input("按回车键继续...")
    
    try:
        if test_api_endpoints():
            test_error_cases()
            print("\n✅ API测试完成！")
        else:
            print("\n❌ API测试失败！")
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()