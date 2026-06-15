from fastapi import APIRouter, Depends

from app.projects.models import DashboardSummary
from app.projects.repository import project_repository
from app.users.dependencies import get_current_user
from app.users.models import UserProfile
from app.users.repository import user_repository


router = APIRouter()


@router.get("/", response_model=DashboardSummary)
def get_dashboard(current_user: UserProfile = Depends(get_current_user)) -> DashboardSummary:
    project_ids = user_repository.list_accessible_project_ids(current_user.id)
    return project_repository.get_dashboard_summary(project_ids=project_ids)
