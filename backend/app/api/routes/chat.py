from fastapi import APIRouter, Depends, HTTPException

from app.orchestrator.orchestrator import orchestrator
from app.orchestrator.schemas import ChatRequest, ChatResponse
from app.projects.repository import project_repository
from app.users.dependencies import ensure_project_access, get_current_user
from app.users.models import ProjectAccessLevel, UserProfile


router = APIRouter()


@router.post("/", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    current_user: UserProfile = Depends(get_current_user),
) -> ChatResponse:
    if request.project_id is not None:
        project = project_repository.get_project(request.project_id)
        if project is None:
            raise HTTPException(status_code=400, detail="Unknown project")
        ensure_project_access(request.project_id, current_user, ProjectAccessLevel.viewer)

    try:
        return orchestrator.handle_chat(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
