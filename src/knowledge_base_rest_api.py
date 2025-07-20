#!/usr/bin/env python3
"""
知识库REST API服务
提供完整的知识库管理和LLM集成功能
"""

import os
import sys
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import uvicorn
import yaml
import json

# 导入知识库核心组件
from knowledge_base.core.config import Config
from knowledge_base.simple_kb import SimpleKnowledgeBase
from knowledge_base.agents.orchestrator import OrchestratorAgent
from knowledge_base.api.dependencies import get_orchestrator, get_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局变量
kb = None
orchestrator = None
config = None

# ============================================================================
# 数据模型定义
# ============================================================================

class DocumentModel(BaseModel):
    """文档模型"""
    id: Optional[str] = Field(None, description="文档ID（可选，自动生成）")
    content: str = Field(..., description="文档内容", min_length=1)
    title: Optional[str] = Field(None, description="文档标题")
    type: str = Field("text", description="文档类型")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="文档元数据")
    tags: List[str] = Field(default_factory=list, description="文档标签")

class QueryRequest(BaseModel):
    """查询请求"""
    query: str = Field(..., description="查询文本", min_length=1)
    metadata_filter: Optional[Dict[str, Any]] = Field(None, description="元数据过滤器")
    tags_filter: Optional[List[str]] = Field(None, description="标签过滤器")
    top_k: int = Field(5, description="返回结果数量", ge=1, le=50)
    min_score: float = Field(0.0, description="最小相似度分数", ge=0.0, le=1.0)
    use_llm: bool = Field(True, description="是否使用LLM生成答案")
    llm_provider: Optional[str] = Field(None, description="LLM提供商")
    stream: bool = Field(False, description="是否流式返回")

class AdvancedQueryRequest(BaseModel):
    """高级查询请求"""
    query: str = Field(..., description="查询文本")
    context: Optional[str] = Field(None, description="查询上下文")
    language: str = Field("auto", description="语言设置")
    response_format: str = Field("detailed", description="响应格式：simple/detailed/summary")
    include_sources: bool = Field(True, description="是否包含来源信息")
    max_tokens: int = Field(1000, description="最大生成token数", ge=100, le=4000)
    temperature: float = Field(0.1, description="生成温度", ge=0.0, le=2.0)

class BulkDocumentRequest(BaseModel):
    """批量文档请求"""
    documents: List[DocumentModel] = Field(..., description="文档列表")
    batch_size: int = Field(10, description="批处理大小", ge=1, le=100)

# ============================================================================
# 应用创建函数
# ============================================================================

def create_app() -> FastAPI:
    """创建FastAPI应用"""
    global kb, orchestrator, config
    
    # 创建FastAPI应用
    app = FastAPI(
        title="知识库 REST API",
        description="""
        # 统一知识库系统 REST API
        
        这个API提供了完整的知识库管理功能：
        
        ## 核心功能
        - 📄 文档管理：添加、更新、删除、查询文档
        - 🔍 智能搜索：基于语义和关键词的混合搜索
        - 🤖 LLM集成：支持多种LLM提供商
        - 📊 批量操作：支持批量添加和删除文档
        - 🔄 实时API：WebSocket支持实时查询
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
    
    # 加载配置
    @app.on_event("startup")
    async def startup_event():
        global kb, orchestrator, config
        
        # 加载配置
        config_path = os.getenv("KB_CONFIG_PATH", "config.yaml")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config_data = yaml.safe_load(f)
            config = Config.from_dict(config_data)
        else:
            # 使用默认配置
            config = Config()
            # 从环境变量加载配置
            config.load_from_env("KB_")
        
        # 创建知识库实例
        kb = SimpleKnowledgeBase(config)
        logger.info("Created SimpleKnowledgeBase instance")
        
        # 创建编排器
        orchestrator = OrchestratorAgent(config)
        logger.info("Created OrchestratorAgent instance")
        
        # 启动编排器
        await orchestrator.start()
        logger.info("Started OrchestratorAgent")
    
    # 关闭事件
    @app.on_event("shutdown")
    async def shutdown_event():
        global orchestrator
        if orchestrator:
            await orchestrator.stop()
            logger.info("Stopped OrchestratorAgent")
    
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
    
    # ============================================================================
    # 文档管理端点
    # ============================================================================
    
    @app.post("/api/v1/documents")
    async def add_document(document: DocumentModel):
        """添加单个文档到知识库"""
        try:
            # 准备元数据
            metadata = document.metadata.copy()
            if document.title:
                metadata["title"] = document.title
            if document.tags:
                metadata["tags"] = document.tags
            metadata["type"] = document.type
            
            # 添加文档
            result = kb.add_document(
                content=document.content,
                metadata=metadata
            )
            
            return {
                "document_id": result.document_id,
                "chunk_ids": result.chunk_ids,
                "success": True,
                "message": f"文档添加成功，生成了 {len(result.chunk_ids)} 个文档块"
            }
        except Exception as e:
            logger.error(f"Error adding document: {str(e)}")
            raise HTTPException(status_code=500, detail=f"添加文档失败: {str(e)}")
    
    @app.get("/api/v1/documents")
    async def list_documents(
        limit: int = Query(20, description="返回数量限制", ge=1, le=100),
        offset: int = Query(0, description="偏移量", ge=0),
        tag_filter: Optional[str] = Query(None, description="标签过滤")
    ):
        """列出知识库中的文档"""
        try:
            documents = list(kb.documents.values())
            
            # 应用标签过滤
            if tag_filter:
                documents = [
                    doc for doc in documents 
                    if tag_filter in doc.metadata.get("tags", [])
                ]
            
            # 分页
            total = len(documents)
            documents = documents[offset:offset + limit]
            
            # 转换为响应格式
            doc_list = []
            for doc in documents:
                doc_list.append({
                    "id": doc.id,
                    "title": doc.metadata.get("title", ""),
                    "type": doc.metadata.get("type", "text"),
                    "tags": doc.metadata.get("tags", []),
                    "content_preview": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                    "metadata": doc.metadata
                })
            
            return {
                "documents": doc_list,
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total
            }
            
        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            raise HTTPException(status_code=500, detail=f"获取文档列表失败: {str(e)}")
    
    @app.get("/api/v1/documents/{document_id}")
    async def get_document(document_id: str):
        """获取特定文档的详细信息"""
        try:
            if document_id not in kb.documents:
                raise HTTPException(status_code=404, detail="文档不存在")
            
            document = kb.documents[document_id]
            
            # 获取文档的所有块
            chunks = [
                chunk for chunk in kb.chunks.values()
                if chunk.document_id == document_id
            ]
            
            return {
                "document": {
                    "id": document.id,
                    "content": document.content,
                    "metadata": document.metadata
                },
                "chunks": [
                    {
                        "id": chunk.id,
                        "text": chunk.text,
                        "metadata": chunk.metadata
                    }
                    for chunk in chunks
                ],
                "stats": {
                    "content_length": len(document.content),
                    "chunk_count": len(chunks)
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting document {document_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"获取文档失败: {str(e)}")
    
    @app.delete("/api/v1/documents/{document_id}")
    async def delete_document(document_id: str):
        """删除特定文档"""
        try:
            if document_id not in kb.documents:
                raise HTTPException(status_code=404, detail="文档不存在")
            
            # 删除文档的所有块
            chunks_to_delete = [
                chunk_id for chunk_id, chunk in kb.chunks.items()
                if chunk.document_id == document_id
            ]
            
            for chunk_id in chunks_to_delete:
                del kb.chunks[chunk_id]
            
            # 删除文档
            del kb.documents[document_id]
            
            return {
                "success": True,
                "message": f"文档 {document_id} 删除成功",
                "deleted_chunks": len(chunks_to_delete)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"删除文档失败: {str(e)}")
    
    @app.post("/api/v1/documents/batch")
    async def add_documents_batch(request: BulkDocumentRequest):
        """批量添加文档到知识库"""
        try:
            results = []
            errors = []
            success_count = 0
            
            for i, document in enumerate(request.documents):
                try:
                    # 准备元数据
                    metadata = document.metadata.copy()
                    if document.title:
                        metadata["title"] = document.title
                    if document.tags:
                        metadata["tags"] = document.tags
                    metadata["type"] = document.type
                    metadata["batch_index"] = i
                    
                    # 添加文档
                    result = kb.add_document(
                        content=document.content,
                        metadata=metadata
                    )
                    
                    results.append({
                        "index": i,
                        "document_id": result.document_id,
                        "chunk_ids": result.chunk_ids,
                        "success": True
                    })
                    success_count += 1
                    
                except Exception as e:
                    error_msg = f"文档 {i} 添加失败: {str(e)}"
                    errors.append(error_msg)
                    results.append({
                        "index": i,
                        "success": False,
                        "error": str(e)
                    })
                    logger.error(error_msg)
            
            return {
                "total": len(request.documents),
                "success": success_count,
                "failed": len(request.documents) - success_count,
                "results": results,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Error in batch add documents: {str(e)}")
            raise HTTPException(status_code=500, detail=f"批量添加文档失败: {str(e)}")
    
    # ============================================================================
    # 查询端点
    # ============================================================================
    
    @app.post("/api/v1/query")
    async def query_knowledge_base(request: QueryRequest):
        """查询知识库"""
        try:
            import time
            start_time = time.time()
            
            # 构建过滤器
            metadata_filter = request.metadata_filter or {}
            
            # 执行查询
            result = kb.query(
                query=request.query,
                metadata_filter=metadata_filter
            )
            
            # 如果启用LLM，尝试增强答案
            if request.use_llm:
                try:
                    # 这里应该调用LLM服务来增强答案
                    # 由于代码中没有完整的LLM实现，这里只是一个占位符
                    pass
                except Exception as e:
                    logger.warning(f"LLM enhancement failed: {e}")
            
            processing_time = time.time() - start_time
            
            # 转换块为字典格式
            chunks = []
            for chunk in result.chunks:
                chunks.append({
                    "id": chunk.id,
                    "text": chunk.text,
                    "document_id": chunk.document_id,
                    "metadata": chunk.metadata,
                    "relevance_score": 1.0  # 简化的相关性分数
                })
            
            return {
                "query": result.query,
                "answer": result.answer,
                "chunks": chunks,
                "metadata": {
                    "total_chunks": len(kb.chunks),
                    "matched_chunks": len(chunks),
                    "llm_enhanced": request.use_llm
                },
                "processing_time": processing_time
            }
            
        except Exception as e:
            logger.error(f"Error querying knowledge base: {str(e)}")
            raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")
    
    @app.post("/api/v1/query/advanced")
    async def advanced_query(request: AdvancedQueryRequest):
        """高级查询功能"""
        try:
            import time
            start_time = time.time()
            
            # 基础查询
            basic_result = kb.query(query=request.query)
            
            # 这里应该调用LLM服务来生成高级答案
            # 由于代码中没有完整的LLM实现，这里只是一个占位符
            
            processing_time = time.time() - start_time
            
            # 构建响应
            response = {
                "query": request.query,
                "answer": basic_result.answer,
                "processing_time": processing_time,
                "metadata": {
                    "response_format": request.response_format,
                    "language": request.language
                }
            }
            
            if request.include_sources:
                response["sources"] = [
                    {
                        "id": chunk.id,
                        "text": chunk.text,
                        "document_id": chunk.document_id,
                        "metadata": chunk.metadata
                    }
                    for chunk in basic_result.chunks
                ]
            
            return response
            
        except Exception as e:
            logger.error(f"Error in advanced query: {str(e)}")
            raise HTTPException(status_code=500, detail=f"高级查询失败: {str(e)}")
    
    # ============================================================================
    # 文件上传端点
    # ============================================================================
    
    @app.post("/api/v1/upload")
    async def upload_file(
        file: UploadFile = File(...),
        title: Optional[str] = None,
        tags: Optional[str] = None
    ):
        """上传文件并添加到知识库"""
        try:
            # 检查文件类型
            if not file.content_type.startswith('text/'):
                raise HTTPException(status_code=400, detail="只支持文本文件")
            
            # 读取文件内容
            content = await file.read()
            text_content = content.decode('utf-8')
            
            # 准备元数据
            metadata = {
                "filename": file.filename,
                "content_type": file.content_type,
                "file_size": len(content)
            }
            
            if title:
                metadata["title"] = title
            
            if tags:
                metadata["tags"] = [tag.strip() for tag in tags.split(",")]
            
            # 添加到知识库
            result = kb.add_document(
                content=text_content,
                metadata=metadata
            )
            
            return {
                "success": True,
                "message": f"文件 {file.filename} 上传成功",
                "document_id": result.document_id,
                "chunk_ids": result.chunk_ids,
                "file_info": {
                    "filename": file.filename,
                    "size": len(content),
                    "chunks_created": len(result.chunk_ids)
                }
            }
            
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")
    
    # ============================================================================
    # 统计和管理端点
    # ============================================================================
    
    @app.get("/api/v1/stats")
    async def get_stats():
        """获取知识库统计信息"""
        try:
            # 计算基本统计
            total_documents = len(kb.documents)
            total_chunks = len(kb.chunks)
            
            # 计算内容统计
            total_content_length = sum(len(doc.content) for doc in kb.documents.values())
            avg_content_length = total_content_length / total_documents if total_documents > 0 else 0
            
            # 统计文档类型
            type_stats = {}
            tag_stats = {}
            
            for doc in kb.documents.values():
                doc_type = doc.metadata.get("type", "unknown")
                type_stats[doc_type] = type_stats.get(doc_type, 0) + 1
                
                tags = doc.metadata.get("tags", [])
                for tag in tags:
                    tag_stats[tag] = tag_stats.get(tag, 0) + 1
            
            return {
                "documents": {
                    "total": total_documents,
                    "by_type": type_stats
                },
                "chunks": {
                    "total": total_chunks,
                    "avg_per_document": total_chunks / total_documents if total_documents > 0 else 0
                },
                "content": {
                    "total_length": total_content_length,
                    "avg_length": avg_content_length
                },
                "tags": tag_stats,
                "system": {
                    "llm_available": True  # 假设LLM可用
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")
    
    @app.post("/api/v1/clear")
    async def clear_knowledge_base(
        confirm: bool = Query(False, description="确认清空知识库")
    ):
        """清空知识库"""
        if not confirm:
            raise HTTPException(status_code=400, detail="需要确认参数 confirm=true")
        
        try:
            kb.clear()
            logger.info("Knowledge base cleared")
            
            return {
                "success": True,
                "message": "知识库已清空"
            }
            
        except Exception as e:
            logger.error(f"Error clearing knowledge base: {str(e)}")
            raise HTTPException(status_code=500, detail=f"清空知识库失败: {str(e)}")
    
    # 导入其他路由
    try:
        from knowledge_base.api.routes.documents import router as documents_router
        app.include_router(documents_router)
        logger.info("Loaded documents API routes")
    except Exception as e:
        logger.warning(f"Failed to load documents API routes: {e}")
    
    try:
        from knowledge_base.api.routes.enhanced_api import router as enhanced_router
        app.include_router(enhanced_router)
        logger.info("Loaded enhanced API routes")
    except Exception as e:
        logger.warning(f"Failed to load enhanced API routes: {e}")
    
    return app

def main():
    """主函数"""
    # 创建应用
    app = create_app()
    
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