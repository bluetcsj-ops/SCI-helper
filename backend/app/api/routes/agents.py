from fastapi import APIRouter

from app.agents.registry import agent_registry
from app.agents.schemas import AgentProfile


router = APIRouter()


@router.get("/", response_model=list[AgentProfile])
def list_agents() -> list[AgentProfile]:
    return agent_registry.list_agents()
