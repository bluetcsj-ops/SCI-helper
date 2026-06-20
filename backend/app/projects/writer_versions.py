from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import func, inspect, select

from app.db.models import WriterDraftVersionRecord
from app.db.session import Base, SessionLocal, engine
from app.projects.models import (
    WriterDraftVersion,
    WriterDraftVersionCreate,
    WriterIntroductionDraft,
    WriterIntroductionDraftUpdate,
)
from app.projects.writer_drafts import writer_introduction_draft_repository


class WriterDraftVersionRepository:
    _schema_checked = False

    def create_version(self, project_id: str, payload: WriterDraftVersionCreate) -> WriterDraftVersion:
        self._ensure_schema()
        with SessionLocal() as session:
            version_count = (
                session.scalar(
                    select(func.count(WriterDraftVersionRecord.id)).where(
                        WriterDraftVersionRecord.project_id == project_id,
                    )
                )
                or 0
            )
            record = WriterDraftVersionRecord(
                project_id=project_id,
                version_label=f"Writer v{version_count + 1}",
                title=payload.title.strip() or f"Writer v{version_count + 1}",
                introduction_json=self._dump_introduction(payload.introduction),
                derived_sections_json=json.dumps(
                    self._normalize_string_map(payload.derived_sections),
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                metadata_json=json.dumps(
                    payload.metadata,
                    ensure_ascii=False,
                    sort_keys=True,
                    default=str,
                ),
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return self._to_version(record)

    def list_versions(self, project_id: str) -> list[WriterDraftVersion]:
        self._ensure_schema()
        with SessionLocal() as session:
            records = session.scalars(
                select(WriterDraftVersionRecord)
                .where(WriterDraftVersionRecord.project_id == project_id)
                .order_by(WriterDraftVersionRecord.created_at.desc())
            ).all()
            return [self._to_version(record) for record in records]

    def get_version(self, project_id: str, version_id: int) -> WriterDraftVersion | None:
        self._ensure_schema()
        with SessionLocal() as session:
            record = session.scalar(
                select(WriterDraftVersionRecord).where(
                    WriterDraftVersionRecord.project_id == project_id,
                    WriterDraftVersionRecord.id == version_id,
                )
            )
            if record is None:
                return None
            return self._to_version(record)

    def restore_version(self, project_id: str, version_id: int) -> WriterIntroductionDraft | None:
        self._ensure_schema()
        with SessionLocal() as session:
            record = session.scalar(
                select(WriterDraftVersionRecord).where(
                    WriterDraftVersionRecord.project_id == project_id,
                    WriterDraftVersionRecord.id == version_id,
                )
            )
            if record is None:
                return None

            introduction = self._parse_introduction(record.introduction_json)
            record.restored_at = datetime.utcnow()
            session.commit()

        return writer_introduction_draft_repository.save_draft(
            project_id=project_id,
            payload=introduction,
        )

    def _to_version(self, record: WriterDraftVersionRecord) -> WriterDraftVersion:
        return WriterDraftVersion(
            id=record.id,
            project_id=record.project_id,
            version_label=record.version_label,
            title=record.title,
            introduction=self._parse_introduction(record.introduction_json),
            derived_sections=self._parse_string_map(record.derived_sections_json),
            metadata=self._parse_metadata(record.metadata_json),
            created_at=record.created_at,
            restored_at=record.restored_at,
        )

    def _dump_introduction(self, introduction: WriterIntroductionDraftUpdate) -> str:
        return json.dumps(
            introduction.model_dump(),
            ensure_ascii=False,
            sort_keys=True,
        )

    def _parse_introduction(self, raw_value: str | None) -> WriterIntroductionDraftUpdate:
        if not raw_value:
            return WriterIntroductionDraftUpdate()
        try:
            parsed = json.loads(raw_value)
        except json.JSONDecodeError:
            return WriterIntroductionDraftUpdate()
        if not isinstance(parsed, dict):
            return WriterIntroductionDraftUpdate()
        return WriterIntroductionDraftUpdate(
            background_paragraph=str(parsed.get("background_paragraph") or ""),
            gap_paragraph=str(parsed.get("gap_paragraph") or ""),
            objective_paragraph=str(parsed.get("objective_paragraph") or ""),
            citation_bindings=self._normalize_citation_bindings(parsed.get("citation_bindings")),
        )

    def _normalize_citation_bindings(self, value: object) -> dict[str, list[str]]:
        if not isinstance(value, dict):
            return {}
        normalized: dict[str, list[str]] = {}
        for field_name, keys in value.items():
            if not isinstance(field_name, str) or not isinstance(keys, list):
                continue
            clean_keys = [key.strip() for key in keys if isinstance(key, str) and key.strip()]
            if clean_keys:
                normalized[field_name] = list(dict.fromkeys(clean_keys))
        return normalized

    def _normalize_string_map(self, value: dict[str, str] | None) -> dict[str, str]:
        if not value:
            return {}
        normalized: dict[str, str] = {}
        for key, section_value in value.items():
            clean_key = key.strip()
            if clean_key:
                normalized[clean_key] = str(section_value or "").strip()
        return normalized

    def _parse_string_map(self, raw_value: str | None) -> dict[str, str]:
        if not raw_value:
            return {}
        try:
            parsed = json.loads(raw_value)
        except json.JSONDecodeError:
            return {}
        if not isinstance(parsed, dict):
            return {}
        return self._normalize_string_map(
            {str(key): str(value or "") for key, value in parsed.items()},
        )

    def _parse_metadata(self, raw_value: str | None) -> dict[str, str | int | float | bool | None]:
        if not raw_value:
            return {}
        try:
            parsed = json.loads(raw_value)
        except json.JSONDecodeError:
            return {}
        if not isinstance(parsed, dict):
            return {}
        return {
            str(key): value
            for key, value in parsed.items()
            if isinstance(value, (str, int, float, bool)) or value is None
        }

    def _ensure_schema(self) -> None:
        if self._schema_checked:
            return
        if engine.dialect.name == "sqlite":
            inspector = inspect(engine)
            if not inspector.has_table(WriterDraftVersionRecord.__tablename__):
                Base.metadata.tables[WriterDraftVersionRecord.__tablename__].create(
                    bind=engine,
                    checkfirst=True,
                )
        else:
            Base.metadata.tables[WriterDraftVersionRecord.__tablename__].create(
                bind=engine,
                checkfirst=True,
            )
        self._schema_checked = True


writer_draft_version_repository = WriterDraftVersionRepository()
