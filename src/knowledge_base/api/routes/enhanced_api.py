"""
增强的知识库API路由
支持LLM集成、批量操作、高级查询等功能
"""

from typing import Dict, Any, List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, File, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json
import asyncio
import logging

from knowledge_base.core.config import Config
from knowledge_base.simple_kb import SimpleKnowledgeBase, Document, TextChunk, AddResult, QueryResult

# 导入LLM核心组件
try:
    from llm_core import LLMFactory, LLMClient
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    logging.warning("LLM core not available, some features will be disabled")

from ..dependencies import get_config

logger = logging.getLogger(__name__)

# 全局知识库实例
_kb = None

def get_kb(config: Config = Depends(get_config)) -> SimpleKnowledgeBase:
    """获取知识库实例"""
    global _kb
    if _kb is None:
        _kb = SimpleKnowledgeBase(config)
        logger.info("Created new SimpleKnowledgeBase instance")
    return _kb

router = APIRouter(prefix="/api/v1", tags=["Enhanced Knowledge Base API"])

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

class BulkDocumentRequest(BaseModel):
    """批量文档请求"""
    documents: List[DocumentModel] = Field(..., description="文档列表")
    batch_size: int = Field(10, description="批处理大小", ge=1, le=100)

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

class DocumentResponse(BaseModel):
    """文档响应"""
    document_id: str = Field(..., description="文档ID")
    chunk_ids: List[str] = Field(..., description="文档块ID列表")
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="响应消息")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="响应元数据")

class QueryResponse(BaseModel):
    """查询响应"""
    query: str = Field(..., description="原始查询")
    answer: str = Field(..., description="生成的答案")
    chunks: List[Dict[str, Any]] = Field(..., description="相关文档块")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="响应元数据")
    processing_time: float = Field(..., description="处理时间（秒）")

class BatchResponse(BaseModel):
    """批量操作响应"""
    total: int = Field(..., description="总数")
    success: int = Field(..., description="成功数")
    failed: int = Field(..., description="失败数")
    results: List[Dict[str, Any]] = Field(..., description="详细结果")
    errors: List[str] = Field(default_factory=list, description="错误信息")

# ============================================================================
# 文档管理端点
# ============================================================================

@router.post("/documents", response_model=DocumentResponse)
async def add_document(
    document: DocumentModel,
    kb: SimpleKnowledgeBase = Depends(get_kb)
):
    """添加单个文档到知识库"""
    try:
        import time
        start_time = time.time()
        
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
        
        processing_time = time.time() - start_time
        
        logger.info(f"Added document {result.document_id} in {processing_time:.2f}s")
        
        return DocumentResponse(
            document_id=result.document_id,
            chunk_ids=result.chunk_ids,
            success=True,
            message=f"文档添加成功，生成了 {len(result.chunk_ids)} 个文档块",
            metadata={
                "processing_time": processing_time,
                "chunks_created": len(result.chunk_ids)
            }
        )
    except Exception as e:
        logger.error(f"Error adding document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"添加文档失败: {str(e)}")

@router.post("/documents/batch", response_model=BatchResponse)
async def add_documents_batch(
    request: BulkDocumentRequest,
    background_tasks: BackgroundTasks,
    kb: SimpleKnowledgeBase = Depends(get_kb)
):
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
        
        return BatchResponse(
            total=len(request.documents),
            success=success_count,
            failed=len(request.documents) - success_count,
            results=results,
            errors=errors
        )
        
    except Exception as e:
        logger.error(f"Error in batch add documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量添加文档失败: {str(e)}")

@router.get("/documents")
async def list_documents(
    limit: int = Query(20, description="返回数量限制", ge=1, le=100),
    offset: int = Query(0, description="偏移量", ge=0),
    tag_filter: Optional[str] = Query(None, description="标签过滤"),
    kb: SimpleKnowledgeBase = Depends(get_kb)
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

@router.get("/documents/{document_id}")
async def get_document(
    document_id: str,
    kb: SimpleKnowledgeBase = Depends(get_kb)
):
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

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    kb: SimpleKnowledgeBase = Depends(get_kb)
):
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
        
        logger.info(f"Deleted document {document_id} and {len(chunks_to_delete)} chunks")
        
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

# ============================================================================
# 查询端点
# ============================================================================

@router.post("/query", response_model=QueryResponse)
async def query_knowledge_base(
    request: QueryRequest,
    kb: SimpleKnowledgeBase = Depends(get_kb)
):
    """查询知识库"""
    try:
        import time
        start_time = time.time()
        
        # 构建过滤器
        metadata_filter = request.metadata_filter or {}
        if request.tags_filter:
            # 简单的标签过滤实现
            pass  # 在实际实现中需要更复杂的过滤逻辑
        
        # 执行查询
        result = kb.query(
            query=request.query,
            metadata_filter=metadata_filter
        )
        
        # 如果启用LLM且可用，增强答案
        if request.use_llm and LLM_AVAILABLE:
            try:
                enhanced_answer = await enhance_answer_with_llm(
                    query=request.query,
                    chunks=result.chunks,
                    provider=request.llm_provider
                )
                if enhanced_answer:
                    result.answer = enhanced_answer
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
        
        return QueryResponse(
            query=result.query,
            answer=result.answer,
            chunks=chunks,
            metadata={
                "total_chunks": len(kb.chunks),
                "matched_chunks": len(chunks),
                "llm_enhanced": request.use_llm and LLM_AVAILABLE
            },
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error querying knowledge base: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

@router.post("/query/advanced")
async def advanced_query(
    request: AdvancedQueryRequest,
    kb: SimpleKnowledgeBase = Depends(get_kb)
):
    """高级查询功能"""
    try:
        import time
        start_time = time.time()
        
        # 基础查询
        basic_result = kb.query(query=request.query)
        
        # 如果有LLM支持，使用高级生成
        if LLM_AVAILABLE:
            try:
                enhanced_answer = await generate_advanced_answer(
                    query=request.query,
                    context=request.context,
                    chunks=basic_result.chunks,
                    response_format=request.response_format,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    language=request.language
                )
                if enhanced_answer:
                    basic_result.answer = enhanced_answer
            except Exception as e:
                logger.warning(f"Advanced LLM generation failed: {e}")
        
        processing_time = time.time() - start_time
        
        # 构建响应
        response = {
            "query": request.query,
            "answer": basic_result.answer,
            "processing_time": processing_time,
            "metadata": {
                "response_format": request.response_format,
                "language": request.language,
                "llm_enhanced": LLM_AVAILABLE
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

@router.post("/query/stream")
async def stream_query(
    request: QueryRequest,
    kb: SimpleKnowledgeBase = Depends(get_kb)
):
    """流式查询响应"""
    if not LLM_AVAILABLE:
        raise HTTPException(status_code=501, detail="流式查询需要LLM支持")
    
    async def generate_stream():
        try:
            # 首先获取相关文档
            result = kb.query(query=request.query)
            
            # 发送初始信息
            yield f"data: {json.dumps({'type': 'start', 'query': request.query})}\n\n"
            
            # 发送找到的文档块信息
            yield f"data: {json.dumps({'type': 'chunks', 'count': len(result.chunks)})}\n\n"
            
            # 流式生成答案
            async for chunk in stream_llm_response(request.query, result.chunks):
                yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
            
            # 发送结束信号
            yield f"data: {json.dumps({'type': 'end'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

# ============================================================================
# 文件上传端点
# ============================================================================

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    tags: Optional[str] = None,
    kb: SimpleKnowledgeBase = Depends(get_kb)
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

@router.get("/stats")
async def get_stats(kb: SimpleKnowledgeBase = Depends(get_kb)):
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
                "llm_available": LLM_AVAILABLE
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@router.post("/clear")
async def clear_knowledge_base(
    confirm: bool = Query(False, description="确认清空知识库"),
    kb: SimpleKnowledgeBase = Depends(get_kb)
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

# ============================================================================
# LLM辅助函数
# ============================================================================

async def enhance_answer_with_llm(
    query: str,
    chunks: List[TextChunk],
    provider: Optional[str] = None
) -> Optional[str]:
    """使用LLM增强答案"""
    if not LLM_AVAILABLE or not chunks:
        return None
    
    try:
        # 构建上下文
        context = "\n\n".join([chunk.text for chunk in chunks])
        
        # 构建提示
        prompt = f"""基于以下上下文信息，回答用户的问题。请提供准确、有用的答案。

上下文信息：
{context}

用户问题：{query}

请回答："""
        
        # 创建LLM客户端
        llm = LLMFactory.create(provider or "openai")
        
        # 生成答案
        messages = [{"role": "user", "content": prompt}]
        response = llm.generate_chat(messages, max_tokens=500, temperature=0.1)
        
        return response.get("content", "")
        
    except Exception as e:
        logger.error(f"LLM enhancement error: {e}")
        return None

async def generate_advanced_answer(
    query: str,
    context: Optional[str],
    chunks: List[TextChunk],
    response_format: str,
    max_tokens: int,
    temperature: float,
    language: str
) -> Optional[str]:
    """生成高级答案"""
    if not LLM_AVAILABLE:
        return None
    
    try:
        # 构建上下文
        doc_context = "\n\n".join([chunk.text for chunk in chunks])
        
        # 构建提示
        if response_format == "summary":
            format_instruction = "请提供简洁的摘要回答。"
        elif response_format == "detailed":
            format_instruction = "请提供详细的回答，包含相关的背景信息。"
        else:
            format_instruction = "请提供清晰、准确的回答。"
        
        prompt = f"""你是一个知识助手。{format_instruction}

{"额外上下文：" + context if context else ""}

相关文档：
{doc_context}

用户问题：{query}

请用{language if language != 'auto' else '中文'}回答："""
        
        # 创建LLM客户端
        llm_client = LLMFactory.create_client("openai")
        
        # 生成答案
        response = await llm_client.generate_async(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return response.get("content", "")
        
    except Exception as e:
        logger.error(f"Advanced answer generation error: {e}")
        return None

async def stream_llm_response(query: str, chunks: List[TextChunk]):
    """流式LLM响应"""
    if not LLM_AVAILABLE:
        yield "LLM不可用"
        return
    
    try:
        # 构建上下文
        context = "\n\n".join([chunk.text for chunk in chunks])
        
        # 构建提示
        prompt = f"""基于以下上下文信息，回答用户的问题：

上下文：
{context}

问题：{query}

回答："""
        
        # 创建LLM客户端
        llm_client = LLMFactory.create_client("openai")
        
        # 流式生成
        async for chunk in llm_client.stream_async(prompt=prompt):
            yield chunk
            
    except Exception as e:
        yield f"生成答案时出错：{str(e)}"