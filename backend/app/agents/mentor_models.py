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


class MentorEvidenceItem(BaseModel):
    source_type: str
    evidence_status: str = "local_template"
    retrieved_at: str | None = None
    external_url: str | None = None
    pmid: str | None = None
    title: str | None = None
    journal: str | None = None
    publication_year: str | None = None
    doi: str | None = None
    publication_types: list[str] = Field(default_factory=list)
    review_status: str = "unreviewed"
    search_query: str
    evidence_summary: str
    recommendation_signal: str
    limitation: str


class MentorRecommendationCard(BaseModel):
    title: str
    research_question: str
    why_fit: str
    data_pathway: str
    methods_route: str
    statistical_plan: str
    innovation_point: str
    feasibility_note: str
    risk_flags: list[str] = Field(default_factory=list)
    first_milestones: list[str] = Field(default_factory=list)
    evidence_items: list[MentorEvidenceItem] = Field(default_factory=list)
    target_journals: list[str] = Field(default_factory=list)


class MentorRecommendationResponse(BaseModel):
    profile_summary: str
    resource_diagnosis: list[str] = Field(default_factory=list)
    matched_strengths: list[str] = Field(default_factory=list)
    recommendations: list[MentorRecommendationCard] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)


class MentorEvidenceReviewUpdate(BaseModel):
    evidence_key: str
    card_title: str
    evidence_index: int = 0
    pmid: str | None = None
    doi: str | None = None
    title: str | None = None
    search_query: str = ""
    review_status: str
    review_note: str = ""
    reviewer: str = ""
    full_text_checked: bool = False
    use_in_introduction: bool = False
    use_in_discussion: bool = False


class MentorEvidenceReview(BaseModel):
    id: int
    project_id: str
    evidence_key: str
    card_title: str
    evidence_index: int
    pmid: str | None = None
    doi: str | None = None
    title: str | None = None
    search_query: str
    review_status: str
    review_note: str = ""
    reviewer: str = ""
    full_text_checked: bool = False
    use_in_introduction: bool = False
    use_in_discussion: bool = False
    updated_at: str
