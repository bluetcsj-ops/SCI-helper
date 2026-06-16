from datetime import datetime

from sqlalchemy import select

from app.agents.mentor_models import MentorEvidenceReview, MentorEvidenceReviewUpdate
from app.db.models import MentorEvidenceReviewRecord
from app.db.session import SessionLocal


VALID_REVIEW_STATUSES = {"unreviewed", "reviewed", "rejected"}


class MentorEvidenceReviewRepository:
    def list_reviews(self, project_id: str) -> list[MentorEvidenceReview]:
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
            updated_at=record.updated_at.isoformat(),
        )


mentor_evidence_review_repository = MentorEvidenceReviewRepository()
