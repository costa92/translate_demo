"""
知识库 API 测试脚本
"""

import os
import sys
import json
import asyncio
import httpx
import pytest
from pathlib import Path

# 添加 src 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# API 基础 URL
BASE_URL = "http://localhost:8000"

@pytest.mark.asyncio
async def test_health_check():
    """测试健康检查端点"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

@pytest.mark.asyncio
async def test_add_document():
    """测试添加文档"""
    async with httpx.AsyncClient() as client:
        # 添加文档
        document = {
            "content": "这是一个测试文档",
            "title": "测试文档",
            "type": "text",
            "tags": ["测试", "示例"]
        }
        response = await client.post(
            f"{BASE_URL}/api/v1/documents",
            json=document
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "document_id" in data
        
        # 获取文档
        document_id = data["document_id"]
        response = await client.get(f"{BASE_URL}/api/v1/documents/{document_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["document"]["id"] == document_id
        assert data["document"]["content"] == "这是一个测试文档"

@pytest.mark.asyncio
async def test_query():
    """测试查询"""
    async with httpx.AsyncClient() as client:
        # 添加文档
        document = {
            "content": "知识库是一个存储和检索知识的系统",
            "title": "知识库简介",
            "type": "text",
            "tags": ["知识库", "系统"]
        }
        response = await client.post(
            f"{BASE_URL}/api/v1/documents",
            json=document
        )
        assert response.status_code == 200
        
        # 查询
        query = {
            "query": "什么是知识库",
            "top_k": 5,
            "use_llm": True
        }
        response = await client.post(
            f"{BASE_URL}/api/v1/query",
            json=query
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert len(data["chunks"]) > 0

@pytest.mark.asyncio
async def test_stats():
    """测试统计信息"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/stats")
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "chunks" in data
        assert "content" in data

if __name__ == "__main__":
    # 运行测试
    pytest.main(["-xvs", __file__])