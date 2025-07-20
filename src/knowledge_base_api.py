#!/usr/bin/env python3
"""
知识库REST API服务器
基于现有的knowledge_base模块实现完整的REST API服务
支持LLM集成和多种存储后端
"""

import os
import sys
import logging
import asyncio
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from knowledge_base.core.config import Config
from knowledge_base.simple_kb import SimpleKnowledgeBase

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局知识库实例
kb = None

def create_knowledge_base_app() -> FastAPI:
    """创建知识库API应用"""
    global kb
    
    # 创建配置
    config = Config()
    
    # 从环境变量加载配置
    config.load_from_env("KB_")
    
    # 创建简单知识库实例（用于快速开始）
    kb = SimpleKnowledgeBase(config)
    logger.info("Created SimpleKnowledgeBase instance")
    
    # 创建FastAPI应用
    app = FastAPI(
        title="知识库 REST API",
        description="""
        # 统一知识库系统 REST API
        
        这个API提供了完整的知识库管理功能：
        
        ## 核心功能
        - 📄 文档管理：添加、更新、删除、查询文档
        - 🔍 智能搜索：基于语义和关键词的混合搜索
        - 🤖 LLM集成：支持多种LLM提供商（OpenAI、DeepSeek、SiliconFlow等）
        - 📊 批量操作：支持批量添加和删除文档
        - 🔄 实时API：WebSocket支持实时查询
        
        ## 支持的存储后端
        - 内存存储（开发测试）
        - ChromaDB（向量数据库）
        - Pinecone（云向量数据库）
        - Weaviate（开源向量数据库）
        - Notion（文档管理）
        
        ## 认证
        大部分端点需要API密钥认证，通过 `X-API-Key` 头部传递。
        """,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # 添加CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 导入并包含API路由
    try:
        from knowledge_base.api.routes.enhanced_api import router as enhanced_router
        app.include_router(enhanced_router)
        logger.info("Loaded enhanced API routes")
    except Exception as e:
        logger.warning(f"Failed to load enhanced API routes: {e}")
        # 回退到简单API路由
        try:
            from knowledge_base.api.routes.simple_api import router as simple_router
            app.include_router(simple_router, prefix="/api/v1")
            logger.info("Loaded simple API routes")
        except Exception as e2:
            logger.error(f"Failed to load simple API routes: {e2}")
    
    # 添加健康检查端点
    @app.get("/health")
    async def health_check():
        """健康检查端点"""
        return {
            "status": "healthy",
            "service": "knowledge_base_api",
            "version": "1.0.0",
            "documents": len(kb.documents) if kb else 0,
            "chunks": len(kb.chunks) if kb else 0
        }
    
    # 添加根端点
    @app.get("/")
    async def root():
        """根端点"""
        return {
            "message": "知识库 REST API 服务",
            "docs": "/docs",
            "health": "/health",
            "api_version": "v1",
            "endpoints": {
                "add_document": "POST /api/v1/documents",
                "query": "POST /api/v1/query",
                "list_documents": "GET /api/v1/documents",
                "get_document": "GET /api/v1/documents/{document_id}",
                "delete_document": "DELETE /api/v1/documents/{document_id}",
                "batch_add": "POST /api/v1/documents/batch",
                "upload_file": "POST /api/v1/upload",
                "stats": "GET /api/v1/stats"
            }
        }
    
    return app

def main():
    """主函数"""
    # 创建应用
    app = create_knowledge_base_app()
    
    # 从环境变量获取配置
    host = os.getenv("KB_API_HOST", "0.0.0.0")
    port = int(os.getenv("KB_API_PORT", "8000"))
    debug = os.getenv("KB_API_DEBUG", "false").lower() == "true"
    
    logger.info(f"Starting Knowledge Base API server on {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"API documentation: http://{host}:{port}/docs")
    
    # 启动服务器
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info" if not debug else "debug",
        reload=debug
    )

if __name__ == "__main__":
    main()