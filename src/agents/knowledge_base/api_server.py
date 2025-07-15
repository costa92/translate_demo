from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import time
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from .orchestrator_agent import OrchestratorAgent
from .api_models import (
    AddKnowledgeRequest, AddKnowledgeResponse, 
    QueryRequest, QueryResponse,
    Task, ErrorResponse, SuccessResponse,
    SystemStatus, HealthResponse
)

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局变量
orchestrator: Optional[OrchestratorAgent] = None
start_time = time.time()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global orchestrator
    
    # 启动时初始化
    logger.info("Initializing Knowledge Base Multi-Agent System...")
    try:
        orchestrator = OrchestratorAgent(
            storage_provider='memory',  # 默认使用内存存储
            storage_config={}
        )
        logger.info("Orchestrator initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}")
        raise
    
    yield
    
    # 关闭时清理
    logger.info("Shutting down Knowledge Base Multi-Agent System...")

# 创建FastAPI应用
app = FastAPI(
    title="Knowledge Base Multi-Agent System API",
    description="A multi-agent system for knowledge collection, processing, storage, and retrieval with RAG capabilities",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 依赖项：获取orchestrator实例
async def get_orchestrator() -> OrchestratorAgent:
    if orchestrator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized"
        )
    return orchestrator

# 异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Internal server error"}
    )

# --- 健康检查端点 ---
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查端点"""
    uptime = time.time() - start_time
    
    components = {
        "orchestrator": "healthy" if orchestrator else "unhealthy",
        "storage": "healthy",  # 可以添加更详细的存储检查
    }
    
    return HealthResponse(
        status="healthy" if orchestrator else "unhealthy",
        uptime=f"{uptime:.2f}s",
        components=components
    )

@app.get("/status", response_model=SystemStatus)
async def get_system_status(orch: OrchestratorAgent = Depends(get_orchestrator)):
    """获取系统状态"""
    try:
        status_info = orch.get_agent_status()
        return SystemStatus(
            status="ready",
            registered_agents=status_info["registered_agents"],
            storage_provider=status_info["storage_provider"]
        )
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get system status"
        )

# --- 知识库管理端点 ---
@app.post("/api/v1/knowledge", response_model=AddKnowledgeResponse)
async def add_knowledge(
    request: AddKnowledgeRequest,
    orch: OrchestratorAgent = Depends(get_orchestrator)
):
    """添加知识到知识库"""
    try:
        # 转换sources为orchestrator期望的格式
        sources = []
        for source in request.sources:
            source_dict = {
                "type": source.type,
                "path" if source.type == "file" else "url": source.location,
                "metadata": source.metadata
            }
            sources.append(source_dict)
        
        payload = {
            "sources": sources,
            "processing_options": request.processing_options
        }
        
        result = orch.receive_request("api", "add_knowledge", payload)
        
        if result.get("status") == "error":
            raise HTTPException(
                status_code=400,
                detail=result.get("message", "Unknown error")
            )
        
        return AddKnowledgeResponse(
            message=result.get("message", "Knowledge added successfully"),
            chunks_count=result.get("chunks_count", 0),
            sources_processed=result.get("sources_processed", 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add knowledge: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add knowledge: {str(e)}"
        )

@app.get("/api/v1/tasks/{task_id}", response_model=Task)
async def get_task_status(task_id: str):
    """获取任务状态（占位符实现）"""
    # TODO: 实现实际的任务状态跟踪
    return Task(
        task_id=task_id,
        status="success",
        details="Task completed successfully"
    )

# --- 问答端点 ---
@app.post("/api/v1/chat/query", response_model=QueryResponse)
async def query_knowledge(
    request: QueryRequest,
    orch: OrchestratorAgent = Depends(get_orchestrator)
):
    """查询知识库（RAG）"""
    try:
        payload = {
            "query": request.query,
            "search_params": request.search_params
        }
        
        result = orch.receive_request("api", "query", payload)
        
        if result.get("status") == "error":
            raise HTTPException(
                status_code=400,
                detail=result.get("message", "Query failed")
            )
        
        return QueryResponse(
            answer=result.get("answer", "No answer available"),
            session_id=request.session_id,
            retrieved_sources=result.get("retrieved_sources", []),
            sources_count=result.get("sources_count", 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to query knowledge: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {str(e)}"
        )

# --- 调试端点 ---
@app.get("/api/v1/debug/agents")
async def debug_agents(orch: OrchestratorAgent = Depends(get_orchestrator)):
    """调试：获取所有智能体信息"""
    try:
        return orch.get_agent_status()
    except Exception as e:
        logger.error(f"Debug agents failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get debug information"
        )

@app.get("/api/v1/debug/storage")
async def debug_storage(orch: OrchestratorAgent = Depends(get_orchestrator)):
    """调试：获取存储信息"""
    try:
        storage_agent = orch.agents.get('KnowledgeStorageAgent')
        if not storage_agent:
            raise HTTPException(status_code=404, detail="Storage agent not found")
        
        chunk_ids = storage_agent.get_all_chunk_ids()
        return {
            "provider_type": type(storage_agent.provider).__name__,
            "total_chunks": len(chunk_ids),
            "chunk_ids": chunk_ids[:10]  # 只返回前10个以避免响应过大
        }
    except Exception as e:
        logger.error(f"Debug storage failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get storage information"
        )

# --- 根路径 ---
@app.get("/")
async def root():
    """根路径信息"""
    return {
        "message": "Knowledge Base Multi-Agent System API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "status": "/status"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)