from fastapi import APIRouter, Depends, HTTPException

from app.projects.models import ProjectReminderSummary
from app.projects.repository import project_repository
from app.reminders.repository import reminder_repository
from app.users.dependencies import ensure_project_access, get_current_user
from app.users.models import ProjectAccessLevel, UserProfile


router = APIRouter()


@router.get("/api/projects/{project_id}/reminders", response_model=ProjectReminderSummary)
def get_project_reminders(
    project_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> ProjectReminderSummary:
    if project_repository.get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_access(project_id, current_user, ProjectAccessLevel.viewer)
    summary = reminder_repository.get_project_summary(project_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return summary


@router.post("/api/projects/{project_id}/reminders/refresh", response_model=ProjectReminderSummary)
def refresh_project_reminders(
    project_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> ProjectReminderSummary:
    if project_repository.get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_access(project_id, current_user, ProjectAccessLevel.editor)
    summary = reminder_repository.get_project_summary(project_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return summary


@router.patch(
    "/api/projects/{project_id}/reminders/{reminder_id}/dismiss",
    response_model=ProjectReminderSummary,
)
def dismiss_project_reminder(
    project_id: str,
    reminder_id: int,
    current_user: UserProfile = Depends(get_current_user),
) -> ProjectReminderSummary:
    if project_repository.get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_access(project_id, current_user, ProjectAccessLevel.editor)
    summary = reminder_repository.dismiss_reminder(project_id, reminder_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return summary
