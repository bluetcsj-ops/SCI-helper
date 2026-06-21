from __future__ import annotations

import re
import json
from datetime import datetime

from sqlalchemy import inspect, select, text

from app.db.models import ReviewerCommentThreadRecord
from app.db.session import Base, SessionLocal, engine
from app.projects.models import ReviewerCommentThread, ReviewerCommentThreadUpdate


COMMENT_TYPE_VALUES = {"major", "minor", "editorial"}
COMMENT_STATUS_VALUES = {"draft", "addressing", "resolved", "deferred"}
REVISION_SECTION_VALUES = {
    "Introduction",
    "Methods / Results",
    "Discussion",
    "Abstract",
    "Cover Letter / Submission",
}


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
                    manual_revision_sections_json="[]",
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
            record.manual_revision_sections_json = json.dumps(
                self._normalize_revision_sections(payload.manual_revision_sections),
                ensure_ascii=False,
            )
            record.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(record)
            return self._to_thread(record)

    def _split_raw_comments(self, raw_text: str) -> list[str]:
        cleaned = self._normalize_raw_text(raw_text)
        if not cleaned:
            return []

        comments: list[str] = []
        for heading, body in self._split_reviewer_blocks(cleaned):
            body_comments = self._split_comment_body(body)
            if not body_comments and heading:
                body_comments = [heading]
            for comment in body_comments:
                if heading and heading.lower() not in comment[:180].lower():
                    comments.append(f"{heading}\n{comment}".strip())
                else:
                    comments.append(comment.strip())
        return self._merge_heading_only_comments(comments) or [cleaned]

    def _normalize_raw_text(self, raw_text: str) -> str:
        cleaned = raw_text.replace("\r\n", "\n").replace("\r", "\n")
        cleaned = cleaned.replace("•", "-").replace("·", "-")
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    def _split_reviewer_blocks(self, cleaned: str) -> list[tuple[str, str]]:
        block_heading_pattern = re.compile(
            r"(?im)^\s*(?:[-*]\s*)?"
            r"((?:reviewer|referee)\s*#?\s*\d+|(?:associate|handling)?\s*editor|"
            r"editorial\s+office|decision\s+letter)"
            r"(?:\s*(?:comments?|report|remarks|recommendation))?\s*:?\s*$"
        )
        matches = list(block_heading_pattern.finditer(cleaned))
        if not matches:
            return [("", cleaned)]

        blocks: list[tuple[str, str]] = []
        if matches[0].start() > 0:
            preface = cleaned[: matches[0].start()].strip()
            if preface:
                blocks.append(("Editor", preface))
        for index, match in enumerate(matches):
            heading = match.group(1).strip()
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(cleaned)
            body = cleaned[start:end].strip()
            blocks.append((self._normalize_reviewer_heading(heading), body))
        return blocks

    def _split_comment_body(self, body: str) -> list[str]:
        body = body.strip()
        if not body:
            return []

        marker_pattern = re.compile(
            r"(?im)^\s*(?=(?:[-*]\s*)?(?:"
            r"(?:major|minor|editorial)\s+(?:comment|point|concern|issue)s?\s*(?:#?\s*\d+)?"
            r"|(?:comment|point|concern|issue|question|recommendation)\s*(?:#?\s*\d+|[A-Z])"
            r"|(?:[0-9]{1,2}|[A-Za-z])[\).\]]"
            r"|\([0-9]{1,2}\)"
            r")\s*[:.)\]-]?\s+\S)"
        )
        starts = [match.start() for match in marker_pattern.finditer(body)]
        if len(starts) > 1 or (starts and starts[0] == 0):
            starts.append(len(body))
            comments = [
                body[starts[index] : starts[index + 1]].strip()
                for index in range(len(starts) - 1)
                if body[starts[index] : starts[index + 1]].strip()
            ]
            return self._merge_short_fragments(comments)

        paragraphs = [item.strip() for item in re.split(r"\n\s*\n+", body) if item.strip()]
        if len(paragraphs) > 1 and all(len(paragraph) >= 40 for paragraph in paragraphs):
            return paragraphs
        return [body]

    def _merge_short_fragments(self, comments: list[str]) -> list[str]:
        merged: list[str] = []
        for comment in comments:
            if merged and len(comment) < 35:
                merged[-1] = f"{merged[-1]}\n{comment}"
            else:
                merged.append(comment)
        return merged

    def _normalize_reviewer_heading(self, heading: str) -> str:
        clean_heading = re.sub(r"\s+", " ", heading.strip())
        reviewer_match = re.search(r"(?i)(reviewer|referee)\s*#?\s*(\d+)", clean_heading)
        if reviewer_match:
            return f"Reviewer {reviewer_match.group(2)}"
        if re.search(r"(?i)editor", clean_heading):
            return "Editor"
        if re.search(r"(?i)decision\s+letter", clean_heading):
            return "Editor"
        return clean_heading.title()

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
        head = comment[:260].lower()
        if re.search(r"\b(editorial|typo|typographical|grammar|formatting|proofread|language)\b", head):
            return "editorial"
        if re.search(
            r"\b(minor|clarify|please add|reference|figure|table|wording|"
            r"cover letter|data availability|availability statement)\b",
            head,
        ):
            return "minor"
        if re.search(
            r"\b(major|method|statistic|sample|endpoint|outcome|bias|validity|"
            r"analysis|model|regression|data|cohort|inclusion|exclusion|limitation)\b",
            head,
        ):
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

    def _normalize_revision_sections(self, values: list[str]) -> list[str]:
        sections: list[str] = []
        for value in values:
            if value in REVISION_SECTION_VALUES and value not in sections:
                sections.append(value)
        return sections

    def _parse_revision_sections(self, value: str) -> list[str]:
        try:
            parsed = json.loads(value or "[]")
        except json.JSONDecodeError:
            return []
        if not isinstance(parsed, list):
            return []
        return self._normalize_revision_sections([str(item) for item in parsed])

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
            manual_revision_sections=self._parse_revision_sections(
                getattr(record, "manual_revision_sections_json", "[]")
            ),
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
                existing_columns = {
                    column["name"]
                    for column in inspector.get_columns(ReviewerCommentThreadRecord.__tablename__)
                }
                if "manual_revision_sections_json" not in existing_columns:
                    with engine.begin() as connection:
                        connection.execute(
                            text(
                                f"ALTER TABLE {ReviewerCommentThreadRecord.__tablename__} "
                                "ADD COLUMN manual_revision_sections_json TEXT NOT NULL DEFAULT '[]'"
                            )
                        )
        else:
            table.create(bind=engine, checkfirst=True)
        self._schema_checked = True


reviewer_comment_repository = ReviewerCommentRepository()
