from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import (
    ChatMessageRecord,
    DataAnalysisRecordRecord,
    DataAuditLogRecord,
    MentorEvidenceReviewRecord,
    PhaseRecord,
    ProjectAccessRecord,
    ProjectPlanDraftRecord,
    ProjectProtocolRecord,
    ProjectRecord,
    TaskRecord,
    TaskReminderRecord,
    UserRecord,
)
from app.db.session import Base, SessionLocal, engine
from app.projects.models import Project
from app.projects.seed_data import build_seed_projects
from app.users.repository import user_repository


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        project_count = session.scalar(select(func.count(ProjectRecord.id))) or 0
        if project_count == 0:
            _seed_projects(session, build_seed_projects())
            session.commit()
        user_repository.seed_default_users_and_access(session)
        session.commit()

    from app.projects.repository import project_repository

    project_repository.refresh_all_project_states()


def _seed_projects(session: Session, projects: list[Project]) -> None:
    for project in projects:
        session.add(
            ProjectRecord(
                id=project.id,
                name=project.name,
                title=project.title,
                topic=project.topic,
                current_phase=project.current_phase,
                progress_percent=project.progress_percent,
                risk_level=project.risk_level.value,
                stage_days_remaining=project.stage_days_remaining,
                next_milestone=project.next_milestone,
                next_due_date=project.next_due_date,
                phases=[
                    PhaseRecord(
                        id=phase.id,
                        title=phase.title,
                        status=phase.status.value,
                        start_date=phase.start_date,
                        end_date=phase.end_date,
                        deliverables="\n".join(phase.deliverables),
                    )
                    for phase in project.phases
                ],
                tasks=[
                    TaskRecord(
                        id=task.id,
                        title=task.title,
                        due_date=task.due_date,
                        status=task.status.value,
                        owner_agent_id=task.owner_agent_id,
                        deliverable=task.deliverable,
                    )
                    for task in project.tasks
                ],
            )
        )


__all__ = [
    "ChatMessageRecord",
    "DataAnalysisRecordRecord",
    "DataAuditLogRecord",
    "MentorEvidenceReviewRecord",
    "PhaseRecord",
    "ProjectAccessRecord",
    "ProjectPlanDraftRecord",
    "ProjectProtocolRecord",
    "ProjectRecord",
    "TaskRecord",
    "TaskReminderRecord",
    "UserRecord",
    "initialize_database",
]
