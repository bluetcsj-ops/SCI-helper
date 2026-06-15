from enum import StrEnum

from pydantic import BaseModel, Field


class AgentId(StrEnum):
    mentor = "mentor"
    project_manager = "project_manager"
    study_planner = "study_planner"
    data_analyst = "data_analyst"
    writer = "writer"
    reviewer = "reviewer"


class AgentProfile(BaseModel):
    id: AgentId
    name: str
    role_name: str
    tagline: str
    responsibilities: list[str]
    tools: list[str] = Field(default_factory=list)
    system_prompt: str
    is_consultant: bool = True
