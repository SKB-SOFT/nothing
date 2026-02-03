from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    model: str = Field(..., description="Model identifier (openai-gpt4, claude-3-5-sonnet, gemini-pro)")
    temperature: Optional[float] = Field(0.7, ge=0, le=2)
    max_tokens: Optional[int] = Field(1000, ge=1, le=4000)

class QueryResponse(BaseModel):
    query: str
    response: str
    model: str
    timestamp: datetime
    tokens_used: Optional[int] = None
    
class ProviderStatus(BaseModel):
    name: str
    status: Literal["online", "offline", "disabled"]
    models: List[str]
    last_checked: datetime

class HistoryItem(BaseModel):
    id: str
    query: str
    response: str
    model: str
    timestamp: datetime
    
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime
