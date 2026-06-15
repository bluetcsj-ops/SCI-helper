from typing import Any

from pydantic import BaseModel, Field

from app.agents.schemas import AgentId


class ChatRequest(BaseModel):
    agent_id: AgentId
    message: str = Field(min_length=1)
    project_id: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    agent_id: AgentId
    agent_name: str
    project_id: str | None
    reply: str
    suggested_next_actions: list[str]
    response_source: str
    fallback_reason: str | None = None
