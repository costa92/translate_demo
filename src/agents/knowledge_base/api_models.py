from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal, Optional
from uuid import UUID, uuid4

# --- 通用模型 ---
class Task(BaseModel):
    task_id: UUID = Field(default_factory=uuid4)
    status: Literal["pending", "running", "success", "failed"] = "pending"
    details: Optional[str] = None

class ErrorResponse(BaseModel):
    status: Literal["error"] = "error"
    message: str

class SuccessResponse(BaseModel):
    status: Literal["success"] = "success"
    message: str

# --- 知识库管理 ---
class KnowledgeSource(BaseModel):
    type: Literal["file", "http", "text"]
    location: str  # 文件路径、URL或纯文本内容
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class AddKnowledgeRequest(BaseModel):
    sources: List[KnowledgeSource]
    processing_options: Optional[Dict[str, Any]] = Field(default_factory=dict)

class AddKnowledgeResponse(BaseModel):
    status: Literal["success"] = "success"
    message: str
    task_id: UUID = Field(default_factory=uuid4)
    chunks_count: int
    sources_processed: int

# --- 问答与聊天 ---
class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    timestamp: Optional[str] = None

class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    history: List[ChatMessage] = Field(default_factory=list)
    search_params: Optional[Dict[str, Any]] = Field(default_factory=dict)

class RetrievedSource(BaseModel):
    source_id: str
    content: str
    relevance_score: float
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class QueryResponse(BaseModel):
    status: Literal["success"] = "success"
    answer: str
    session_id: Optional[str] = None
    retrieved_sources: List[RetrievedSource] = Field(default_factory=list)
    sources_count: int = 0

# --- 系统状态 ---
class AgentStatus(BaseModel):
    agent_name: str
    status: Literal["ready", "busy", "error"]
    last_activity: Optional[str] = None

class SystemStatus(BaseModel):
    status: Literal["ready", "busy", "error"]
    registered_agents: List[str]
    storage_provider: str
    agents_status: List[AgentStatus] = Field(default_factory=list)

# --- 健康检查 ---
class HealthResponse(BaseModel):
    status: Literal["healthy", "unhealthy"]
    version: str = "1.0.0"
    uptime: Optional[str] = None
    components: Dict[str, str] = Field(default_factory=dict)