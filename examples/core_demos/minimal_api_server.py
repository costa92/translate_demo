#!/usr/bin/env python
"""
最小化 API 服务器示例

这个示例展示了如何启动一个最小化的 API 服务器，不依赖于监控系统。
"""

import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel

# 添加项目根目录到 Python 路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 创建 FastAPI 应用
app = FastAPI(
    title="统一知识库系统 API",
    description="统一知识库系统的 RESTful API",
    version="1.0.0",
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 定义请求和响应模型
class QueryRequest(BaseModel):
    query: str
    filters: dict = None
    limit: int = 5

class QueryResponse(BaseModel):
    answer: str
    chunks: list = []

# 定义 API 路由
@app.get("/")
async def root():
    """API 根路径"""
    return {"message": "欢迎使用统一知识库系统 API"}

@app.get("/health")
async def health():
    """健康检查端点"""
    return {"status": "healthy"}

@app.get("/info")
async def info():
    """系统信息端点"""
    return {
        "name": "统一知识库系统",
        "version": "1.0.0",
        "description": "一个综合性的知识管理平台",
    }

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """查询知识库"""
    # 这里只是一个模拟实现
    return {
        "answer": f"这是对查询 '{request.query}' 的模拟回答。在实际实现中，这将基于检索到的文档生成。",
        "chunks": [
            {
                "text": "这是第一个检索到的文档块。",
                "metadata": {"source": "示例文档 1"}
            },
            {
                "text": "这是第二个检索到的文档块。",
                "metadata": {"source": "示例文档 2"}
            }
        ]
    }

def run_app(host="0.0.0.0", port=8000):
    """运行 API 服务器"""
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    print("启动最小化 API 服务器...")
    print("API 文档将在 http://localhost:8000/docs 可用")
    run_app()