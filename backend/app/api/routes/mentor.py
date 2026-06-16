from fastapi import APIRouter

from app.agents.mentor_models import (
    MentorQuestionnaireRequest,
    MentorRecommendationResponse,
    MentorTrendSnapshot,
)
from app.agents.mentor_service import mentor_service


router = APIRouter()


@router.get("/trends", response_model=MentorTrendSnapshot)
def get_mentor_trends() -> MentorTrendSnapshot:
    return mentor_service.get_trend_snapshot()


@router.post("/recommendations", response_model=MentorRecommendationResponse)
def create_mentor_recommendations(
    payload: MentorQuestionnaireRequest,
) -> MentorRecommendationResponse:
    return mentor_service.generate_recommendations(payload)
