from __future__ import annotations

import re
from datetime import datetime

from sqlalchemy import inspect, select

from app.db.models import ReviewerCommentThreadRecord
from app.db.session import Base, SessionLocal, engine
from app.projects.models import ReviewerCommentThread, ReviewerCommentThreadUpdate


COMMENT_TYPE_VALUES = {"major", "minor", "editorial"}
COMMENT_STATUS_VALUES = {"draft", "addressing", "resolved", "deferred"}


class ReviewerCommentRepository:
    _schema_checked = False

    def list_threads(self, project_id: str) -> list[ReviewerCommentThread]:
        self._ensure_schema()
        with SessionLocal() as session:
            records = session.scalars(
                select(ReviewerCommentThreadRecord)
                .where(ReviewerCommentThreadRecord.project_id == project_id)
                .order_by(ReviewerCommentThreadRecord.id.asc())
            ).all()
            return [self._to_thread(record) for record in records]

    def import_threads(self, project_id: str, raw_text: str) -> list[ReviewerCommentThread]:
        self._ensure_schema()
        comments = self._split_raw_comments(raw_text)
        with SessionLocal() as session:
            records: list[ReviewerCommentThreadRecord] = []
            for index, comment in enumerate(comments, start=1):
                comment_type = self._infer_comment_type(comment)
                reviewer_label = self._infer_reviewer_label(comment) or f"Reviewer import {index}"
                record = ReviewerCommentThreadRecord(
                    project_id=project_id,
                    reviewer_label=reviewer_label,
                    comment_type=comment_type,
                    status="draft",
                    comment_text=comment,
                    response_draft=self._build_response_draft(comment, comment_type),
                    manuscript_change=self._build_manuscript_change(comment_type),
                )
                session.add(record)
                records.append(record)
            session.commit()
            for record in records:
                session.refresh(record)
            return [self._to_thread(record) for record in records]

    def update_thread(
        self,
        project_id: str,
        thread_id: int,
        payload: ReviewerCommentThreadUpdate,
    ) -> ReviewerCommentThread | None:
        self._ensure_schema()
        with SessionLocal() as session:
            record = session.scalar(
                select(ReviewerCommentThreadRecord).where(
                    ReviewerCommentThreadRecord.project_id == project_id,
                    ReviewerCommentThreadRecord.id == thread_id,
                )
            )
            if record is None:
                return None

            record.reviewer_label = payload.reviewer_label.strip() or "Reviewer"
            record.comment_type = self._normalize_comment_type(payload.comment_type)
            record.status = self._normalize_status(payload.status)
            record.comment_text = payload.comment_text.strip()
            record.response_draft = payload.response_draft.strip()
            record.manuscript_change = payload.manuscript_change.strip()
            record.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(record)
            return self._to_thread(record)

    def _split_raw_comments(self, raw_text: str) -> list[str]:
        cleaned = raw_text.replace("\r\n", "\n").strip()
        if not cleaned:
            return []

        pattern = re.compile(
            r"(?im)^\s*(?=(?:reviewer\s+\d+|comment\s+\d+|major\s+comment|minor\s+comment|point\s+\d+|[0-9]+[.)])\b)"
        )
        starts = [match.start() for match in pattern.finditer(cleaned)]
        if len(starts) <= 1:
            paragraphs = [item.strip() for item in re.split(r"\n\s*\n+", cleaned) if item.strip()]
            return paragraphs if len(paragraphs) > 1 else [cleaned]

        starts.append(len(cleaned))
        comments = [
            cleaned[starts[index] : starts[index + 1]].strip()
            for index in range(len(starts) - 1)
            if cleaned[starts[index] : starts[index + 1]].strip()
        ]
        return self._merge_heading_only_comments(comments) or [cleaned]

    def _merge_heading_only_comments(self, comments: list[str]) -> list[str]:
        merged: list[str] = []
        pending_heading = ""
        heading_pattern = re.compile(r"(?i)^\s*(reviewer\s+\d+|editor|associate editor)\s*:?\s*$")
        for comment in comments:
            if heading_pattern.match(comment):
                pending_heading = comment.strip()
                continue
            if pending_heading:
                merged.append(f"{pending_heading}\n{comment}")
                pending_heading = ""
            else:
                merged.append(comment)
        if pending_heading:
            merged.append(pending_heading)
        return merged

    def _infer_comment_type(self, comment: str) -> str:
        head = comment[:180].lower()
        if "minor" in head or "editorial" in head or "typo" in head:
            return "minor" if "editorial" not in head else "editorial"
        if "major" in head or "method" in head or "statistic" in head or "sample" in head:
            return "major"
        return "major"

    def _infer_reviewer_label(self, comment: str) -> str:
        match = re.search(r"(?i)\b(reviewer\s+\d+|editor|associate editor)\b", comment[:160])
        return match.group(1).title() if match else ""

    def _build_response_draft(self, comment: str, comment_type: str) -> str:
        focus = "major methodological concern" if comment_type == "major" else "comment"
        return (
            f"Thank you for this {focus}. We agree that this point requires clarification. "
            "In the revised manuscript, we will address the comment by updating the relevant "
            "text, ensuring that the claim is supported by the verified data output, and adding "
            "page and line references after the revision is finalized. "
            f"Reviewer comment to address: \"{comment[:260].strip()}\""
        )

    def _build_manuscript_change(self, comment_type: str) -> str:
        if comment_type == "editorial":
            return "Revise wording, terminology, or formatting in the relevant manuscript section."
        if comment_type == "minor":
            return "Clarify the relevant sentence or paragraph and verify consistency with the final manuscript."
        return "Revise the relevant Methods, Results, or Discussion section and add traceable evidence for the response."

    def _normalize_comment_type(self, value: str) -> str:
        clean_value = value.strip().lower()
        return clean_value if clean_value in COMMENT_TYPE_VALUES else "major"

    def _normalize_status(self, value: str) -> str:
        clean_value = value.strip().lower()
        return clean_value if clean_value in COMMENT_STATUS_VALUES else "draft"

    def _to_thread(self, record: ReviewerCommentThreadRecord) -> ReviewerCommentThread:
        return ReviewerCommentThread(
            id=record.id,
            project_id=record.project_id,
            reviewer_label=record.reviewer_label,
            comment_type=record.comment_type,
            status=record.status,
            comment_text=record.comment_text,
            response_draft=record.response_draft,
            manuscript_change=record.manuscript_change,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def _ensure_schema(self) -> None:
        if self._schema_checked:
            return
        table = Base.metadata.tables[ReviewerCommentThreadRecord.__tablename__]
        if engine.dialect.name == "sqlite":
            inspector = inspect(engine)
            if not inspector.has_table(ReviewerCommentThreadRecord.__tablename__):
                table.create(bind=engine, checkfirst=True)
        else:
            table.create(bind=engine, checkfirst=True)
        self._schema_checked = True


reviewer_comment_repository = ReviewerCommentRepository()
