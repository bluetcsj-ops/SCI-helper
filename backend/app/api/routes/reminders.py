from fastapi import APIRouter, HTTPException

from app.projects.models import ProjectReminderSummary
from app.reminders.repository import reminder_repository


router = APIRouter()


@router.get("/api/projects/{project_id}/reminders", response_model=ProjectReminderSummary)
def get_project_reminders(project_id: str) -> ProjectReminderSummary:
    summary = reminder_repository.get_project_summary(project_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return summary


@router.post("/api/projects/{project_id}/reminders/refresh", response_model=ProjectReminderSummary)
def refresh_project_reminders(project_id: str) -> ProjectReminderSummary:
    summary = reminder_repository.get_project_summary(project_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return summary


@router.patch(
    "/api/projects/{project_id}/reminders/{reminder_id}/dismiss",
    response_model=ProjectReminderSummary,
)
def dismiss_project_reminder(project_id: str, reminder_id: int) -> ProjectReminderSummary:
    summary = reminder_repository.dismiss_reminder(project_id, reminder_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return summary
