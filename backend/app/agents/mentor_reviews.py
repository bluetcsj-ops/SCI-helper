from datetime import datetime

from sqlalchemy import inspect, select, text

from app.agents.mentor_models import MentorEvidenceReview, MentorEvidenceReviewUpdate
from app.db.models import MentorEvidenceReviewRecord
from app.db.session import SessionLocal, engine


VALID_REVIEW_STATUSES = {"unreviewed", "reviewed", "rejected"}


class MentorEvidenceReviewRepository:
    _schema_checked = False

    def list_reviews(self, project_id: str) -> list[MentorEvidenceReview]:
        self._ensure_schema()
        with SessionLocal() as session:
            records = session.scalars(
                select(MentorEvidenceReviewRecord)
                .where(MentorEvidenceReviewRecord.project_id == project_id)
                .order_by(MentorEvidenceReviewRecord.updated_at.desc())
            ).all()
            return [self._to_review(record) for record in records]

    def upsert_review(
        self,
        project_id: str,
        payload: MentorEvidenceReviewUpdate,
    ) -> MentorEvidenceReview:
        review_status = payload.review_status.strip().lower()
        if review_status not in VALID_REVIEW_STATUSES:
            raise ValueError("Invalid mentor evidence review status")

        evidence_key = payload.evidence_key.strip()
        if not evidence_key:
            raise ValueError("Evidence key is required")

        self._ensure_schema()
        with SessionLocal() as session:
            record = session.scalar(
                select(MentorEvidenceReviewRecord).where(
                    MentorEvidenceReviewRecord.project_id == project_id,
                    MentorEvidenceReviewRecord.evidence_key == evidence_key,
                )
            )

            if record is None:
                record = MentorEvidenceReviewRecord(
                    project_id=project_id,
                    evidence_key=evidence_key,
                    card_title=payload.card_title,
                    evidence_index=payload.evidence_index,
                    pmid=payload.pmid,
                    doi=payload.doi,
                    title=payload.title,
                    search_query=payload.search_query,
                    review_status=review_status,
                    review_note=payload.review_note.strip(),
                    reviewer=payload.reviewer.strip(),
                    full_text_checked=payload.full_text_checked,
                    use_in_introduction=payload.use_in_introduction,
                    use_in_discussion=payload.use_in_discussion,
                )
                session.add(record)
            else:
                record.card_title = payload.card_title
                record.evidence_index = payload.evidence_index
                record.pmid = payload.pmid
                record.doi = payload.doi
                record.title = payload.title
                record.search_query = payload.search_query
                record.review_status = review_status
                record.review_note = payload.review_note.strip()
                record.reviewer = payload.reviewer.strip()
                record.full_text_checked = payload.full_text_checked
                record.use_in_introduction = payload.use_in_introduction
                record.use_in_discussion = payload.use_in_discussion
                record.updated_at = datetime.utcnow()

            session.commit()
            session.refresh(record)
            return self._to_review(record)

    def _to_review(self, record: MentorEvidenceReviewRecord) -> MentorEvidenceReview:
        return MentorEvidenceReview(
            id=record.id,
            project_id=record.project_id,
            evidence_key=record.evidence_key,
            card_title=record.card_title,
            evidence_index=record.evidence_index,
            pmid=record.pmid,
            doi=record.doi,
            title=record.title,
            search_query=record.search_query,
            review_status=record.review_status,
            review_note=record.review_note or "",
            reviewer=record.reviewer or "",
            full_text_checked=bool(record.full_text_checked),
            use_in_introduction=bool(record.use_in_introduction),
            use_in_discussion=bool(record.use_in_discussion),
            updated_at=record.updated_at.isoformat(),
        )

    def _ensure_schema(self) -> None:
        if self._schema_checked:
            return
        if engine.dialect.name != "sqlite":
            self._schema_checked = True
            return

        inspector = inspect(engine)
        if not inspector.has_table(MentorEvidenceReviewRecord.__tablename__):
            self._schema_checked = True
            return

        existing_columns = {
            column["name"] for column in inspector.get_columns(MentorEvidenceReviewRecord.__tablename__)
        }
        new_columns = {
            "review_note": "TEXT NOT NULL DEFAULT ''",
            "reviewer": "VARCHAR(120) NOT NULL DEFAULT ''",
            "full_text_checked": "BOOLEAN NOT NULL DEFAULT 0",
            "use_in_introduction": "BOOLEAN NOT NULL DEFAULT 0",
            "use_in_discussion": "BOOLEAN NOT NULL DEFAULT 0",
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
                            f"ALTER TABLE {MentorEvidenceReviewRecord.__tablename__} "
                            f"ADD COLUMN {column_name} {column_definition}"
                        )
                    )
        self._schema_checked = True


mentor_evidence_review_repository = MentorEvidenceReviewRepository()
