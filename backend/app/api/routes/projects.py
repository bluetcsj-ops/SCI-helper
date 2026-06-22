from fastapi import APIRouter, Depends, HTTPException

from app.agents.mentor_models import MentorEvidenceReview, MentorEvidenceReviewUpdate
from app.agents.mentor_reviews import mentor_evidence_review_repository
from app.projects.models import (
    Project,
    ProjectPlanDraft,
    ProjectProtocol,
    ProjectProtocolExtractRequest,
    ProjectProtocolUpdate,
    ReviewerCommentImportRequest,
    ReviewerCommentThread,
    ReviewerCommentThreadUpdate,
    TaskStatusUpdate,
    WriterDraftVersion,
    WriterDraftVersionCreate,
    WriterIntroductionDraft,
    WriterIntroductionDraftUpdate,
)
from app.projects.plan_drafts import project_plan_draft_repository
from app.projects.plan_generator import project_plan_generator
from app.projects.repository import project_repository
from app.projects.reviewer_comments import reviewer_comment_repository
from app.projects.writer_drafts import writer_introduction_draft_repository
from app.projects.writer_versions import writer_draft_version_repository
from app.protocols.extractor import protocol_extractor
from app.protocols.repository import protocol_repository
from app.users.dependencies import ensure_project_access, get_current_user
from app.users.models import ProjectAccessLevel, ProjectAccessPolicy, UserProfile
from app.users.repository import user_repository


router = APIRouter()


@router.get("/", response_model=list[Project])
def list_projects(current_user: UserProfile = Depends(get_current_user)) -> list[Project]:
    project_ids = user_repository.list_accessible_project_ids(current_user.id)
    return project_repository.list_projects(project_ids=project_ids)


@router.get("/{project_id}", response_model=Project)
def get_project(
    project_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> Project:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_access(project_id, current_user, ProjectAccessLevel.viewer)
    return project


@router.get("/{project_id}/access", response_model=ProjectAccessPolicy)
def get_project_access(
    project_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> ProjectAccessPolicy:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ensure_project_access(project_id, current_user, ProjectAccessLevel.viewer)


@router.patch("/{project_id}/tasks/{task_id}", response_model=Project)
def update_task_status(
    project_id: str,
    task_id: str,
    request: TaskStatusUpdate,
    current_user: UserProfile = Depends(get_current_user),
) -> Project:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_access(project_id, current_user, ProjectAccessLevel.editor)

    updated_project = project_repository.update_task_status(
        project_id=project_id,
        task_id=task_id,
        status=request.status,
    )
    if updated_project is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return updated_project


@router.get("/{project_id}/protocol", response_model=ProjectProtocol)
def get_project_protocol(
    project_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> ProjectProtocol:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_access(project_id, current_user, ProjectAccessLevel.viewer)
    return protocol_repository.get_protocol(project_id)


@router.put("/{project_id}/protocol", response_model=ProjectProtocol)
def save_project_protocol(
    project_id: str,
    request: ProjectProtocolUpdate,
    current_user: UserProfile = Depends(get_current_user),
) -> ProjectProtocol:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_access(project_id, current_user, ProjectAccessLevel.editor)
    return protocol_repository.save_protocol(project_id=project_id, payload=request)


@router.post("/{project_id}/protocol/draft", response_model=ProjectProtocol)
def create_project_protocol_draft(
    project_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> ProjectProtocol:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_access(project_id, current_user, ProjectAccessLevel.editor)
    return protocol_repository.create_draft(project)


@router.post("/{project_id}/protocol/extract", response_model=ProjectProtocol)
def extract_project_protocol(
    project_id: str,
    request: ProjectProtocolExtractRequest,
    current_user: UserProfile = Depends(get_current_user),
) -> ProjectProtocol:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_access(project_id, current_user, ProjectAccessLevel.editor)

    if not request.source_text.strip():
        raise HTTPException(status_code=400, detail="Source text is required")

    return protocol_extractor.extract_and_save(project=project, source_text=request.source_text)


@router.get("/{project_id}/mentor/evidence-reviews", response_model=list[MentorEvidenceReview])
def list_mentor_evidence_reviews(
    project_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> list[MentorEvidenceReview]:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_access(project_id, current_user, ProjectAccessLevel.viewer)
    return mentor_evidence_review_repository.list_reviews(project_id)


@router.put("/{project_id}/mentor/evidence-reviews", response_model=MentorEvidenceReview)
def save_mentor_evidence_review(
    project_id: str,
    request: MentorEvidenceReviewUpdate,
    current_user: UserProfile = Depends(get_current_user),
) -> MentorEvidenceReview:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_access(project_id, current_user, ProjectAccessLevel.editor)

    try:
        return mentor_evidence_review_repository.upsert_review(project_id=project_id, payload=request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{project_id}/writer/introduction-draft", response_model=WriterIntroductionDraft)
def get_writer_introduction_draft(
    project_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> WriterIntroductionDraft:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_access(project_id, current_user, ProjectAccessLevel.viewer)
    return writer_introduction_draft_repository.get_draft(project_id)


@router.put("/{project_id}/writer/introduction-draft", response_model=WriterIntroductionDraft)
def save_writer_introduction_draft(
    project_id: str,
    request: WriterIntroductionDraftUpdate,
    current_user: UserProfile = Depends(get_current_user),
) -> WriterIntroductionDraft:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_access(project_id, current_user, ProjectAccessLevel.editor)
    return writer_introduction_draft_repository.save_draft(project_id=project_id, payload=request)


@router.get("/{project_id}/writer/versions", response_model=list[WriterDraftVersion])
def list_writer_draft_versions(
    project_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> list[WriterDraftVersion]:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_access(project_id, current_user, ProjectAccessLevel.viewer)
    return writer_draft_version_repository.list_versions(project_id)


@router.post("/{project_id}/writer/versions", response_model=WriterDraftVersion)
def create_writer_draft_version(
    project_id: str,
    request: WriterDraftVersionCreate,
    current_user: UserProfile = Depends(get_current_user),
) -> WriterDraftVersion:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_access(project_id, current_user, ProjectAccessLevel.editor)
    return writer_draft_version_repository.create_version(project_id=project_id, payload=request)


@router.get("/{project_id}/writer/versions/{version_id}", response_model=WriterDraftVersion)
def get_writer_draft_version(
    project_id: str,
    version_id: int,
    current_user: UserProfile = Depends(get_current_user),
) -> WriterDraftVersion:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_access(project_id, current_user, ProjectAccessLevel.viewer)

    version = writer_draft_version_repository.get_version(project_id, version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Writer version not found")
    return version


@router.post(
    "/{project_id}/writer/versions/{version_id}/restore",
    response_model=WriterIntroductionDraft,
)
def restore_writer_draft_version(
    project_id: str,
    version_id: int,
    current_user: UserProfile = Depends(get_current_user),
) -> WriterIntroductionDraft:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_access(project_id, current_user, ProjectAccessLevel.editor)

    restored_draft = writer_draft_version_repository.restore_version(project_id, version_id)
    if restored_draft is None:
        raise HTTPException(status_code=404, detail="Writer version not found")
    return restored_draft


@router.get("/{project_id}/reviewer/comment-threads", response_model=list[ReviewerCommentThread])
def list_reviewer_comment_threads(
    project_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> list[ReviewerCommentThread]:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_access(project_id, current_user, ProjectAccessLevel.viewer)
    return reviewer_comment_repository.list_threads(project_id)


@router.post("/{project_id}/reviewer/comment-threads/import", response_model=list[ReviewerCommentThread])
def import_reviewer_comment_threads(
    project_id: str,
    request: ReviewerCommentImportRequest,
    current_user: UserProfile = Depends(get_current_user),
) -> list[ReviewerCommentThread]:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_access(project_id, current_user, ProjectAccessLevel.editor)
    if not request.raw_text.strip():
        raise HTTPException(status_code=400, detail="Reviewer comment text is required")
    return reviewer_comment_repository.import_threads(project_id, request.raw_text)


@router.delete("/{project_id}/reviewer/comment-threads", response_model=dict[str, int])
def clear_reviewer_comment_threads(
    project_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> dict[str, int]:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_access(project_id, current_user, ProjectAccessLevel.editor)
    deleted_count = reviewer_comment_repository.clear_threads(project_id)
    return {"deleted_count": deleted_count}


@router.put("/{project_id}/reviewer/comment-threads/{thread_id}", response_model=ReviewerCommentThread)
def update_reviewer_comment_thread(
    project_id: str,
    thread_id: int,
    request: ReviewerCommentThreadUpdate,
    current_user: UserProfile = Depends(get_current_user),
) -> ReviewerCommentThread:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_access(project_id, current_user, ProjectAccessLevel.editor)

    updated_thread = reviewer_comment_repository.update_thread(project_id, thread_id, request)
    if updated_thread is None:
        raise HTTPException(status_code=404, detail="Reviewer comment thread not found")
    return updated_thread


@router.get("/{project_id}/plan/drafts", response_model=list[ProjectPlanDraft])
def list_project_plan_drafts(
    project_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> list[ProjectPlanDraft]:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_access(project_id, current_user, ProjectAccessLevel.viewer)

    return project_plan_draft_repository.list_drafts(project_id)


@router.post("/{project_id}/plan/drafts/from-protocol", response_model=ProjectPlanDraft)
def generate_project_plan_draft_from_protocol(
    project_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> ProjectPlanDraft:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_access(project_id, current_user, ProjectAccessLevel.editor)

    try:
        return project_plan_generator.generate_draft_from_protocol(project)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{project_id}/plan/drafts/{draft_id}/apply", response_model=Project)
def apply_project_plan_draft(
    project_id: str,
    draft_id: int,
    current_user: UserProfile = Depends(get_current_user),
) -> Project:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_access(project_id, current_user, ProjectAccessLevel.editor)

    updated_project = project_plan_draft_repository.apply_draft(project_id, draft_id)
    if updated_project is None:
        raise HTTPException(status_code=404, detail="Plan draft not found")

    return updated_project


@router.post("/{project_id}/plan/from-protocol", response_model=ProjectPlanDraft)
def generate_project_plan_from_protocol(
    project_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> ProjectPlanDraft:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_access(project_id, current_user, ProjectAccessLevel.editor)

    try:
        return project_plan_generator.generate_draft_from_protocol(project)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
