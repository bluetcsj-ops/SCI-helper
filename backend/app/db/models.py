from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class ProjectRecord(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    current_phase: Mapped[str] = mapped_column(String(255), nullable=False)
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    risk_level: Mapped[str] = mapped_column(String(24), nullable=False, default="green")
    stage_days_remaining: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_milestone: Mapped[str] = mapped_column(Text, nullable=False)
    next_due_date: Mapped[Date] = mapped_column(Date, nullable=False)

    phases: Mapped[list[PhaseRecord]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="PhaseRecord.start_date",
    )
    tasks: Mapped[list[TaskRecord]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="TaskRecord.due_date",
    )


class UserRecord(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="researcher")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class ProjectAccessRecord(Base):
    __tablename__ = "project_access"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    access_level: Mapped[str] = mapped_column(String(24), nullable=False, default="viewer")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class PhaseRecord(Base):
    __tablename__ = "phases"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    start_date: Mapped[Date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Date] = mapped_column(Date, nullable=False)
    deliverables: Mapped[str] = mapped_column(Text, nullable=False, default="")

    project: Mapped[ProjectRecord] = relationship(back_populates="phases")


class TaskRecord(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    due_date: Mapped[Date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    owner_agent_id: Mapped[str] = mapped_column(String(64), nullable=False)
    deliverable: Mapped[str] = mapped_column(Text, nullable=False)

    project: Mapped[ProjectRecord] = relationship(back_populates="tasks")


class ProjectProtocolRecord(Base):
    __tablename__ = "project_protocols"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), primary_key=True)
    research_question: Mapped[str] = mapped_column(Text, nullable=False, default="")
    hypothesis: Mapped[str] = mapped_column(Text, nullable=False, default="")
    study_type: Mapped[str] = mapped_column(Text, nullable=False, default="")
    primary_endpoint: Mapped[str] = mapped_column(Text, nullable=False, default="")
    secondary_endpoints: Mapped[str] = mapped_column(Text, nullable=False, default="")
    inclusion_criteria: Mapped[str] = mapped_column(Text, nullable=False, default="")
    exclusion_criteria: Mapped[str] = mapped_column(Text, nullable=False, default="")
    data_requirements: Mapped[str] = mapped_column(Text, nullable=False, default="")
    experiment_workflow: Mapped[str] = mapped_column(Text, nullable=False, default="")
    statistical_plan: Mapped[str] = mapped_column(Text, nullable=False, default="")
    target_journals: Mapped[str] = mapped_column(Text, nullable=False, default="")
    rhea_milestones: Mapped[str] = mapped_column(Text, nullable=False, default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class ProjectPlanDraftRecord(Base):
    __tablename__ = "project_plan_drafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    version_label: Mapped[str] = mapped_column(String(64), nullable=False)
    phases_json: Mapped[str] = mapped_column(Text, nullable=False)
    tasks_json: Mapped[str] = mapped_column(Text, nullable=False)
    protocol_snapshot_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class TaskReminderRecord(Base):
    __tablename__ = "task_reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    task_id: Mapped[str] = mapped_column(String(64), nullable=False)
    reminder_type: Mapped[str] = mapped_column(String(32), nullable=False)
    severity: Mapped[str] = mapped_column(String(24), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    trigger_date: Mapped[Date] = mapped_column(Date, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_action: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    dismissed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ChatMessageRecord(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    agent_id: Mapped[str] = mapped_column(String(64), nullable=False)
    speaker: Mapped[str] = mapped_column(String(24), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class DataAnalysisRecordRecord(Base):
    __tablename__ = "data_analysis_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    column_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    issue_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chart_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quality_report_json: Mapped[str] = mapped_column(Text, nullable=False)
    statistics_report_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class DataAuditLogRecord(Base):
    __tablename__ = "data_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    column_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    risk_level: Mapped[str] = mapped_column(String(24), nullable=False, default="green")
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    raw_data_saved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class MentorEvidenceReviewRecord(Base):
    __tablename__ = "mentor_evidence_reviews"
    __table_args__ = (
        UniqueConstraint("project_id", "evidence_key", name="uq_mentor_evidence_review_project_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    evidence_key: Mapped[str] = mapped_column(String(255), nullable=False)
    card_title: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pmid: Mapped[str | None] = mapped_column(String(64), nullable=True)
    doi: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    search_query: Mapped[str] = mapped_column(Text, nullable=False, default="")
    review_status: Mapped[str] = mapped_column(String(24), nullable=False, default="unreviewed")
    review_note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    reviewer: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    full_text_checked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    use_in_introduction: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    use_in_discussion: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class WriterIntroductionDraftRecord(Base):
    __tablename__ = "writer_introduction_drafts"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), primary_key=True)
    background_paragraph: Mapped[str] = mapped_column(Text, nullable=False, default="")
    gap_paragraph: Mapped[str] = mapped_column(Text, nullable=False, default="")
    objective_paragraph: Mapped[str] = mapped_column(Text, nullable=False, default="")
    citation_bindings_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class WriterDraftVersionRecord(Base):
    __tablename__ = "writer_draft_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    version_label: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False, default="")
    introduction_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    derived_sections_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    restored_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ReviewerCommentThreadRecord(Base):
    __tablename__ = "reviewer_comment_threads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    reviewer_label: Mapped[str] = mapped_column(String(120), nullable=False, default="Reviewer")
    comment_type: Mapped[str] = mapped_column(String(32), nullable=False, default="major")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    comment_text: Mapped[str] = mapped_column(Text, nullable=False)
    response_draft: Mapped[str] = mapped_column(Text, nullable=False, default="")
    manuscript_change: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
