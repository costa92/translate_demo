#!/usr/bin/env python3
"""
知识库 API 使用示例
"""

import os
import sys
import json
import asyncio
import httpx
from pathlib import Path

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# API 基础 URL
BASE_URL = "http://localhost:8000"

async def main():
    """主函数"""
    async with httpx.AsyncClient() as client:
        # 检查 API 健康状态
        print("检查 API 健康状态...")
        response = await client.get(f"{BASE_URL}/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        print()
        
        # 添加文档
        print("添加文档...")
        document = {
            "content": "知识库是一个存储和检索知识的系统。它可以帮助组织管理和共享知识，提高工作效率。",
            "title": "知识库简介",
            "type": "text",
            "tags": ["知识库", "系统", "知识管理"]
        }
        response = await client.post(
            f"{BASE_URL}/api/v1/documents",
            json=document
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        document_id = response.json()["document_id"]
        print()
        
        # 添加另一个文档
        print("添加另一个文档...")
        document = {
            "content": "LLM（大型语言模型）是一种基于深度学习的自然语言处理模型，可以生成人类语言文本。它通过在大量文本数据上训练，学习语言的模式和规律。",
            "title": "LLM 简介",
            "type": "text",
            "tags": ["LLM", "AI", "自然语言处理"]
        }
        response = await client.post(
            f"{BASE_URL}/api/v1/documents",
            json=document
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        print()
        
        # 列出文档
        print("列出文档...")
        response = await client.get(f"{BASE_URL}/api/v1/documents")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        print()
        
        # 获取文档
        print(f"获取文档 {document_id}...")
        response = await client.get(f"{BASE_URL}/api/v1/documents/{document_id}")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        print()
        
        # 查询知识库
        print("查询知识库...")
        query = {
            "query": "什么是知识库",
            "top_k": 5,
            "use_llm": True
        }
        response = await client.post(
            f"{BASE_URL}/api/v1/query",
            json=query
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        print()
        
        # 高级查询
        print("高级查询...")
        query = {
            "query": "LLM 是什么",
            "context": "我想了解人工智能技术",
            "response_format": "detailed",
            "include_sources": True,
            "max_tokens": 500,
            "temperature": 0.1
        }
        response = await client.post(
            f"{BASE_URL}/api/v1/query/advanced",
            json=query
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        print()
        
        # 获取统计信息
        print("获取统计信息...")
        response = await client.get(f"{BASE_URL}/api/v1/stats")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        print()

if __name__ == "__main__":
    asyncio.run(main())