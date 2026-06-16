from pydantic import BaseModel, Field


class MentorTrendPoint(BaseModel):
    year: int
    publication_count: int


class MentorTrendItem(BaseModel):
    topic_id: str
    title: str
    heat_label: str
    summary: str
    recent_counts: list[MentorTrendPoint] = Field(default_factory=list)
    forecast_note: str


class MentorTrendSnapshot(BaseModel):
    generated_at: str
    trends: list[MentorTrendItem] = Field(default_factory=list)
    recommended_focus: str


class MentorQuestionnaireRequest(BaseModel):
    equipment_summary: str = ""
    planning_systems: str = ""
    programming_level: str = ""
    data_types: list[str] = Field(default_factory=list)
    weekly_hours: int = 0
    publication_experience: str = ""
    interest_topics: list[str] = Field(default_factory=list)


class MentorRecommendationCard(BaseModel):
    title: str
    why_fit: str
    innovation_point: str
    feasibility_note: str
    target_journals: list[str] = Field(default_factory=list)


class MentorRecommendationResponse(BaseModel):
    profile_summary: str
    matched_strengths: list[str] = Field(default_factory=list)
    recommendations: list[MentorRecommendationCard] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
