from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class RiskLevel(StrEnum):
    green = "green"
    orange = "orange"
    red = "red"


class ItemStatus(StrEnum):
    not_started = "not_started"
    in_progress = "in_progress"
    blocked = "blocked"
    done = "done"


class ReminderStatus(StrEnum):
    pending = "pending"
    sent = "sent"
    dismissed = "dismissed"


class ReminderType(StrEnum):
    due_48h = "due_48h"
    due_24h = "due_24h"
    overdue = "overdue"
    blocked = "blocked"


class Phase(BaseModel):
    id: str
    title: str
    status: ItemStatus
    start_date: date
    end_date: date
    deliverables: list[str] = Field(default_factory=list)


class Task(BaseModel):
    id: str
    title: str
    due_date: date
    status: ItemStatus
    owner_agent_id: str
    deliverable: str


class TaskStatusUpdate(BaseModel):
    status: ItemStatus


class ProjectProtocol(BaseModel):
    project_id: str
    research_question: str = ""
    hypothesis: str = ""
    study_type: str = ""
    primary_endpoint: str = ""
    secondary_endpoints: str = ""
    inclusion_criteria: str = ""
    exclusion_criteria: str = ""
    data_requirements: str = ""
    experiment_workflow: str = ""
    statistical_plan: str = ""
    target_journals: str = ""
    rhea_milestones: str = ""


class ProjectProtocolUpdate(BaseModel):
    research_question: str = ""
    hypothesis: str = ""
    study_type: str = ""
    primary_endpoint: str = ""
    secondary_endpoints: str = ""
    inclusion_criteria: str = ""
    exclusion_criteria: str = ""
    data_requirements: str = ""
    experiment_workflow: str = ""
    statistical_plan: str = ""
    target_journals: str = ""
    rhea_milestones: str = ""


class ProjectProtocolExtractRequest(BaseModel):
    source_text: str


class ProjectPlanDraft(BaseModel):
    id: int
    project_id: str
    version_label: str
    phases: list[Phase]
    tasks: list[Task]
    created_at: datetime
    applied_at: datetime | None = None


class WriterIntroductionDraft(BaseModel):
    project_id: str
    background_paragraph: str = ""
    gap_paragraph: str = ""
    objective_paragraph: str = ""
    citation_bindings: dict[str, list[str]] = Field(default_factory=dict)
    updated_at: datetime | None = None


class WriterIntroductionDraftUpdate(BaseModel):
    background_paragraph: str = ""
    gap_paragraph: str = ""
    objective_paragraph: str = ""
    citation_bindings: dict[str, list[str]] = Field(default_factory=dict)


class TaskReminder(BaseModel):
    id: int
    project_id: str
    task_id: str
    task_title: str
    reminder_type: ReminderType
    severity: RiskLevel
    status: ReminderStatus
    trigger_date: date
    due_date: date
    message: str
    suggested_action: str
    created_at: datetime
    updated_at: datetime
    dismissed_at: datetime | None = None


class ProjectReminderSummary(BaseModel):
    project_id: str
    generated_at: datetime
    risk_level: RiskLevel
    active_count: int
    overdue_count: int
    blocked_count: int
    next_due_count: int
    manager_note: str
    reminders: list[TaskReminder]


class Project(BaseModel):
    id: str
    name: str
    title: str
    topic: str
    current_phase: str
    progress_percent: int
    risk_level: RiskLevel
    stage_days_remaining: int
    next_milestone: str
    next_due_date: date
    phases: list[Phase]
    tasks: list[Task]


class MilestoneSummary(BaseModel):
    project_id: str
    project_name: str
    milestone: str
    due_date: date
    risk_level: RiskLevel


class DashboardSummary(BaseModel):
    overall_completion_percent: int
    active_project_count: int
    risk_level: RiskLevel
    next_milestones: list[MilestoneSummary]
    encouragement: str
    manager_name: str
    manager_role: str
    manager_message: str
