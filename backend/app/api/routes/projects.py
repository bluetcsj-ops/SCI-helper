from fastapi import APIRouter, HTTPException

from app.projects.models import (
    Project,
    ProjectPlanDraft,
    ProjectProtocol,
    ProjectProtocolExtractRequest,
    ProjectProtocolUpdate,
    TaskStatusUpdate,
)
from app.projects.plan_drafts import project_plan_draft_repository
from app.projects.plan_generator import project_plan_generator
from app.projects.repository import project_repository
from app.protocols.extractor import protocol_extractor
from app.protocols.repository import protocol_repository


router = APIRouter()


@router.get("/", response_model=list[Project])
def list_projects() -> list[Project]:
    return project_repository.list_projects()


@router.get("/{project_id}", response_model=Project)
def get_project(project_id: str) -> Project:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}/tasks/{task_id}", response_model=Project)
def update_task_status(project_id: str, task_id: str, request: TaskStatusUpdate) -> Project:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    updated_project = project_repository.update_task_status(
        project_id=project_id,
        task_id=task_id,
        status=request.status,
    )
    if updated_project is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return updated_project


@router.get("/{project_id}/protocol", response_model=ProjectProtocol)
def get_project_protocol(project_id: str) -> ProjectProtocol:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return protocol_repository.get_protocol(project_id)


@router.put("/{project_id}/protocol", response_model=ProjectProtocol)
def save_project_protocol(project_id: str, request: ProjectProtocolUpdate) -> ProjectProtocol:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return protocol_repository.save_protocol(project_id=project_id, payload=request)


@router.post("/{project_id}/protocol/draft", response_model=ProjectProtocol)
def create_project_protocol_draft(project_id: str) -> ProjectProtocol:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return protocol_repository.create_draft(project)


@router.post("/{project_id}/protocol/extract", response_model=ProjectProtocol)
def extract_project_protocol(
    project_id: str,
    request: ProjectProtocolExtractRequest,
) -> ProjectProtocol:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    if not request.source_text.strip():
        raise HTTPException(status_code=400, detail="Source text is required")

    return protocol_extractor.extract_and_save(project=project, source_text=request.source_text)


@router.get("/{project_id}/plan/drafts", response_model=list[ProjectPlanDraft])
def list_project_plan_drafts(project_id: str) -> list[ProjectPlanDraft]:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    return project_plan_draft_repository.list_drafts(project_id)


@router.post("/{project_id}/plan/drafts/from-protocol", response_model=ProjectPlanDraft)
def generate_project_plan_draft_from_protocol(project_id: str) -> ProjectPlanDraft:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        return project_plan_generator.generate_draft_from_protocol(project)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{project_id}/plan/drafts/{draft_id}/apply", response_model=Project)
def apply_project_plan_draft(project_id: str, draft_id: int) -> Project:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    updated_project = project_plan_draft_repository.apply_draft(project_id, draft_id)
    if updated_project is None:
        raise HTTPException(status_code=404, detail="Plan draft not found")

    return updated_project


@router.post("/{project_id}/plan/from-protocol", response_model=ProjectPlanDraft)
def generate_project_plan_from_protocol(project_id: str) -> ProjectPlanDraft:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        return project_plan_generator.generate_draft_from_protocol(project)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
