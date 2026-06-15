from fastapi import APIRouter

from app.projects.models import DashboardSummary
from app.projects.repository import project_repository


router = APIRouter()


@router.get("/", response_model=DashboardSummary)
def get_dashboard() -> DashboardSummary:
    return project_repository.get_dashboard_summary()
