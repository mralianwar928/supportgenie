# schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(default="default")

class Source(BaseModel):
    title: str
    snippet: str

class ChatResponse(BaseModel):
    reply: str
    escalated: bool
    reason: Optional[str] = None
    sources: List[Source] = []
    latency_ms: int
    cost_usd: float

class HealthResponse(BaseModel):
    status: str