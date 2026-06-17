from datetime import datetime

from sqlalchemy import inspect, select, text

from app.db.models import WriterIntroductionDraftRecord
from app.db.session import SessionLocal, engine
from app.projects.models import WriterIntroductionDraft, WriterIntroductionDraftUpdate


class WriterIntroductionDraftRepository:
    _schema_checked = False

    def get_draft(self, project_id: str) -> WriterIntroductionDraft:
        self._ensure_schema()
        with SessionLocal() as session:
            record = session.scalar(
                select(WriterIntroductionDraftRecord).where(
                    WriterIntroductionDraftRecord.project_id == project_id,
                )
            )
            if record is None:
                return WriterIntroductionDraft(project_id=project_id)
            return self._to_draft(record)

    def save_draft(
        self,
        project_id: str,
        payload: WriterIntroductionDraftUpdate,
    ) -> WriterIntroductionDraft:
        self._ensure_schema()
        with SessionLocal() as session:
            record = session.scalar(
                select(WriterIntroductionDraftRecord).where(
                    WriterIntroductionDraftRecord.project_id == project_id,
                )
            )
            if record is None:
                record = WriterIntroductionDraftRecord(project_id=project_id)
                session.add(record)

            record.background_paragraph = payload.background_paragraph.strip()
            record.gap_paragraph = payload.gap_paragraph.strip()
            record.objective_paragraph = payload.objective_paragraph.strip()
            record.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(record)
            return self._to_draft(record)

    def _to_draft(self, record: WriterIntroductionDraftRecord) -> WriterIntroductionDraft:
        return WriterIntroductionDraft(
            project_id=record.project_id,
            background_paragraph=record.background_paragraph or "",
            gap_paragraph=record.gap_paragraph or "",
            objective_paragraph=record.objective_paragraph or "",
            updated_at=record.updated_at,
        )

    def _ensure_schema(self) -> None:
        if self._schema_checked:
            return
        if engine.dialect.name != "sqlite":
            self._schema_checked = True
            return

        inspector = inspect(engine)
        if not inspector.has_table(WriterIntroductionDraftRecord.__tablename__):
            self._schema_checked = True
            return

        existing_columns = {
            column["name"] for column in inspector.get_columns(WriterIntroductionDraftRecord.__tablename__)
        }
        new_columns = {
            "background_paragraph": "TEXT NOT NULL DEFAULT ''",
            "gap_paragraph": "TEXT NOT NULL DEFAULT ''",
            "objective_paragraph": "TEXT NOT NULL DEFAULT ''",
            "updated_at": "DATETIME",
        }
        missing_columns = {
            column_name: column_definition
            for column_name, column_definition in new_columns.items()
            if column_name not in existing_columns
        }
        if missing_columns:
            with engine.begin() as connection:
                for column_name, column_definition in missing_columns.items():
                    connection.execute(
                        text(
                            f"ALTER TABLE {WriterIntroductionDraftRecord.__tablename__} "
                            f"ADD COLUMN {column_name} {column_definition}"
                        )
                    )
        self._schema_checked = True


writer_introduction_draft_repository = WriterIntroductionDraftRepository()
