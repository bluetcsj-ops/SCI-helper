from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import func, select

from app.db.models import ProjectPlanDraftRecord
from app.db.session import SessionLocal
from app.projects.models import Phase, Project, ProjectPlanDraft, ProjectProtocol, Task
from app.projects.repository import project_repository


class ProjectPlanDraftRepository:
    def create_draft(
        self,
        project: Project,
        protocol: ProjectProtocol,
        phases: list[Phase],
        tasks: list[Task],
    ) -> ProjectPlanDraft:
        with SessionLocal() as session:
            draft_count = (
                session.scalar(
                    select(func.count(ProjectPlanDraftRecord.id)).where(
                        ProjectPlanDraftRecord.project_id == project.id
                    )
                )
                or 0
            )
            record = ProjectPlanDraftRecord(
                project_id=project.id,
                version_label=f"Plan v{draft_count + 1}",
                phases_json=self._dump_models(phases),
                tasks_json=self._dump_models(tasks),
                protocol_snapshot_json=json.dumps(
                    protocol.model_dump(),
                    ensure_ascii=False,
                    default=str,
                ),
            )
            session.add(record)
            session.commit()
            return self._to_draft(record)

    def list_drafts(self, project_id: str) -> list[ProjectPlanDraft]:
        with SessionLocal() as session:
            records = session.scalars(
                select(ProjectPlanDraftRecord)
                .where(ProjectPlanDraftRecord.project_id == project_id)
                .order_by(ProjectPlanDraftRecord.created_at.desc())
            ).all()
            return [self._to_draft(record) for record in records]

    def get_draft(self, project_id: str, draft_id: int) -> ProjectPlanDraft | None:
        with SessionLocal() as session:
            record = session.scalar(
                select(ProjectPlanDraftRecord).where(
                    ProjectPlanDraftRecord.project_id == project_id,
                    ProjectPlanDraftRecord.id == draft_id,
                )
            )
            if record is None:
                return None
            return self._to_draft(record)

    def apply_draft(self, project_id: str, draft_id: int) -> Project | None:
        with SessionLocal() as session:
            record = session.scalar(
                select(ProjectPlanDraftRecord).where(
                    ProjectPlanDraftRecord.project_id == project_id,
                    ProjectPlanDraftRecord.id == draft_id,
                )
            )
            if record is None:
                return None

            draft = self._to_draft(record)
            record.applied_at = datetime.utcnow()
            session.commit()

        return project_repository.replace_project_plan(
            project_id=project_id,
            phases=draft.phases,
            tasks=draft.tasks,
            current_phase=draft.phases[0].title if draft.phases else "未生成执行计划",
        )

    def _dump_models(self, values: list[Phase] | list[Task]) -> str:
        return json.dumps(
            [value.model_dump() for value in values],
            ensure_ascii=False,
            default=str,
        )

    def _to_draft(self, record: ProjectPlanDraftRecord) -> ProjectPlanDraft:
        return ProjectPlanDraft(
            id=record.id,
            project_id=record.project_id,
            version_label=record.version_label,
            phases=[Phase(**item) for item in json.loads(record.phases_json)],
            tasks=[Task(**item) for item in json.loads(record.tasks_json)],
            created_at=record.created_at,
            applied_at=record.applied_at,
        )


project_plan_draft_repository = ProjectPlanDraftRepository()
