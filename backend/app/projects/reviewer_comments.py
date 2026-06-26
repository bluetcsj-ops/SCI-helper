from __future__ import annotations

import re
import json
from datetime import datetime

from sqlalchemy import delete, inspect, select, text

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
        cleaned_text = self._normalize_raw_text(raw_text)
        comments = self._split_raw_comments(raw_text)
        with SessionLocal() as session:
            records: list[ReviewerCommentThreadRecord] = []
            for index, comment in enumerate(comments, start=1):
                comment_type = self._infer_comment_type(comment)
                reviewer_label = self._infer_reviewer_label(comment) or f"未识别审稿人 {index}"
                split_warnings = self._detect_split_warnings(
                    cleaned_text,
                    comments,
                    comment,
                    reviewer_label,
                )
                record = ReviewerCommentThreadRecord(
                    project_id=project_id,
                    reviewer_label=reviewer_label,
                    comment_type=comment_type,
                    status="draft",
                    comment_text=comment,
                    response_draft=self._build_response_draft(comment, comment_type),
                    manuscript_change=self._build_manuscript_change(comment, comment_type, split_warnings),
                    manual_revision_sections_json="[]",
                )
                session.add(record)
                records.append(record)
            session.commit()
            for record in records:
                session.refresh(record)
            return [self._to_thread(record) for record in records]

    def clear_threads(self, project_id: str) -> int:
        self._ensure_schema()
        with SessionLocal() as session:
            result = session.execute(
                delete(ReviewerCommentThreadRecord).where(
                    ReviewerCommentThreadRecord.project_id == project_id,
                )
            )
            session.commit()
            return int(result.rowcount or 0)

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

    def _detect_split_warnings(
        self,
        cleaned_text: str,
        comments: list[str],
        comment: str,
        reviewer_label: str,
    ) -> list[str]:
        warnings: list[str] = []
        if len(comments) == 1 and len(cleaned_text) > 900:
            warnings.append("长审稿信只识别出 1 条意见，可能需要手动拆分。")
        if len(comment.strip()) < 45:
            warnings.append("该条意见过短，可能只是标题片段。")
        if reviewer_label.startswith("未识别审稿人"):
            warnings.append("未能从导入文本中识别审稿人标签。")
        return warnings

    def _build_response_draft(self, comment: str, comment_type: str) -> str:
        theme = self._infer_response_theme(comment)
        opening = self._response_opening(comment_type, theme)
        concern = self._response_concern(comment, theme)
        action = self._response_action(theme)
        return (
            f"{opening} {concern} {action} "
            "After revision, we will add the exact page and line references below. "
            "Page: [to be completed manually]. "
            "Lines: [to be completed manually]. "
            "Manuscript location: [to be completed manually]."
        )

    def _response_concern(self, comment: str, theme: str) -> str:
        normalized = re.sub(r"\s+", " ", comment).strip()
        normalized = re.sub(r"(?i)^(reviewer|referee)\s*#?\s*\d+\s*:?\s*", "", normalized)
        normalized = re.sub(
            r"(?i)^(major|minor|editorial)\s+(comment|point|concern|issue)s?\s*(#?\s*\d+)?\s*[:.)-]?\s*",
            "",
            normalized,
        )
        if normalized:
            first_sentence = re.split(r"(?<=[.!?])\s+", normalized, maxsplit=1)[0].strip()
            if 18 <= len(first_sentence) <= 220:
                if not re.search(r"[.!?]$", first_sentence):
                    first_sentence = f"{first_sentence}."
                return f"We understand the concern to be that {first_sentence[0].lower()}{first_sentence[1:]}"
        concern_by_theme = {
            "statistics_model": "We understand that the main concern is the statistical boundary of the current analysis.",
            "data_privacy": "We understand that the main concern is the transparency and traceability of the data source.",
            "radiotherapy_methods": "We understand that the main concern is whether the radiotherapy planning workflow is sufficiently reproducible.",
            "literature_reference": "We understand that the main concern is whether the manuscript is anchored in recent and traceable literature.",
            "methods_reporting": "We understand that the main concern is whether the study methods and reporting pathway are specific enough.",
            "ethics_submission": "We understand that the main concern is whether the submission statements are complete.",
            "figures_tables": "We understand that the main concern is whether the figures, tables, or supplements are traceable.",
            "language_editorial": "We understand that the main concern is clarity and presentation.",
        }
        return concern_by_theme.get(
            theme,
            "We understand that the main concern is whether the revised manuscript addresses this point specifically.",
        )

    def _infer_response_theme(self, comment: str) -> str:
        text_value = comment.lower()
        if re.search(
            r"\b(statistic|statistics|p value|p-value|confidence interval|ci\b|"
            r"odds ratio|or-based|hazard ratio|\bhr\b|regression|model|calibration|"
            r"roc|auc|validation|separation|convergence|schoenfeld|mixed[- ]effects?|"
            r"event coding|binary endpoint|endpoint coding|outlier|causal|causality|"
            r"exploratory|predictive claim|prediction claim)\b",
            text_value,
        ):
            return "statistics_model"
        if re.search(
            r"\b(ethic|irb|consent|conflict of interest|funding|data availability|"
            r"generative ai|ai assistance|cover letter|submission|disclosure|"
            r"response letter|point-by-point|manuscript location|page and line|page/line)\b",
            text_value,
        ):
            return "ethics_submission"
        if re.search(
            r"\b(reference|citation|literature|introduction|background|recent study|"
            r"prior work|supporting evidence)\b",
            text_value,
        ):
            return "literature_reference"
        if re.search(
            r"\b(treatment planning system|planning system|tps|dose calculation|"
            r"gamma criteria|gamma pass|structure naming|rt dose|rtdose|rtstruct|"
            r"rtplan|dicom|qa failure|patient-specific qa|plan-quality|plan quality)\b",
            text_value,
        ):
            return "radiotherapy_methods"
        if re.search(
            r"\b(data|dataset|csv|missing|privacy|de-identif|anonym|patient id|"
            r"raw data|dicom|rtdose|rtstruct|rtplan|tps|gamma|qa)\b",
            text_value,
        ):
            return "data_privacy"
        if re.search(
            r"\b(method|methods|materials|endpoint|outcome|inclusion|exclusion|"
            r"cohort|sample|eligibility|workflow|protocol)\b",
            text_value,
        ):
            return "methods_reporting"
        if re.search(r"\b(figure|table|legend|resolution|reference|supplement)\b", text_value):
            return "figures_tables"
        if re.search(
            r"\b(editorial|typo|grammar|language|wording|format|formatting|proofread|"
            r"generic|abstract|tighten)\b",
            text_value,
        ):
            return "language_editorial"
        return "general"

    def _response_opening(self, comment_type: str, theme: str) -> str:
        if comment_type == "editorial" or theme == "language_editorial":
            return "Thank you for identifying this wording and presentation issue."
        if theme == "statistics_model":
            return "We appreciate the reviewer highlighting the statistical interpretation of this analysis."
        if theme == "data_privacy":
            return "We appreciate the reviewer drawing attention to the data source and traceability."
        if theme == "radiotherapy_methods":
            return "We appreciate the reviewer asking for a clearer account of the radiotherapy planning details."
        if theme == "literature_reference":
            return "Thank you for pointing out the need to strengthen the literature support."
        if theme == "ethics_submission":
            return "Thank you for pointing out this submission and disclosure requirement."
        if comment_type == "minor":
            return "Thank you for this helpful suggestion."
        return "Thank you for raising this important point."

    def _response_action(self, theme: str) -> str:
        if theme == "statistics_model":
            return (
                "We will revise the Methods and Results to state the model purpose, event coding, "
                "sample-size limitations, convergence checks, and manual statistical review status. "
                "Any OR, HR, or mixed-effects output will be described as exploratory unless it has "
                "been externally validated, and we will avoid causal or validated predictive claims."
            )
        if theme == "data_privacy":
            return (
                "We will clarify the data source, field definitions, missing-field handling, "
                "de-identification safeguards, and whether raw clinical or DICOM data were retained. "
                "The revision will separate auditable sample-data workflow details from any claims "
                "that require authorized real-world data."
            )
        if theme == "radiotherapy_methods":
            return (
                "We will revise the Methods to report the treatment planning system version, dose "
                "calculation algorithm, QA or gamma criteria, structure-naming rules, and the way "
                "plan-quality outliers or QA failures were defined. The Results will avoid extending "
                "these workflow checks beyond the verified dataset."
            )
        if theme == "literature_reference":
            return (
                "We will add recent and traceable references in the Introduction or Discussion, explain "
                "how they support the specific workflow claim, and verify the citation metadata and "
                "journal reference style before resubmission."
            )
        if theme == "methods_reporting":
            return (
                "We will expand the relevant Methods text to define the study population, endpoints, "
                "analysis workflow, and reproducibility checks, and will align the Results wording "
                "with the verified outputs actually generated by the system."
            )
        if theme == "ethics_submission":
            return (
                "We will add or revise the required ethics, consent, conflict-of-interest, funding, "
                "data-availability, and AI-assistance statements according to the target journal "
                "requirements before final submission."
            )
        if theme == "figures_tables":
            return (
                "We will check the relevant figures, tables, captions, references, and supplementary "
                "materials against the journal instructions, and will revise the presentation so that "
                "each item is traceable to the underlying analysis."
            )
        if theme == "language_editorial":
            return (
                "We will revise the affected sentence or section for clarity, terminology, and journal "
                "style while preserving the scientific meaning and the verified evidence boundary."
            )
        return (
            "We will revise the relevant manuscript text so that the response is specific to the "
            "reviewer's concern, supported by traceable evidence, and consistent with the final "
            "Methods, Results, and submission materials."
        )

    def _build_manuscript_change(
        self,
        comment: str,
        comment_type: str,
        split_warnings: list[str] | None = None,
    ) -> str:
        theme = self._infer_response_theme(comment)
        if theme == "statistics_model":
            change = "补充统计模型目的、事件/终点编码、样本量限制和外部统计复核边界，避免因果化或已验证预测表述。"
        elif theme == "data_privacy":
            change = "补充数据来源、字段定义、缺失值处理、脱敏边界和原始数据保留状态。"
        elif theme == "radiotherapy_methods":
            change = "补充 TPS/计划系统版本、剂量计算算法、QA/gamma criteria、结构命名和计划质量异常定义。"
        elif theme == "literature_reference":
            change = "补充近期且可追溯的引用，并核对 citation metadata、引用位置和期刊格式。"
        elif theme == "methods_reporting":
            change = "补充研究对象、纳排标准、终点定义、分析流程和可复现性说明。"
        elif theme == "ethics_submission":
            change = "补充伦理、知情同意、利益冲突、资助、数据可用性或 AI 使用披露等投稿声明。"
        elif theme == "figures_tables":
            change = "核对相关图表、图注、补充材料和数据来源，确保展示内容可追溯。"
        elif theme == "language_editorial":
            change = "润色相关句子或段落，降低模板化表达并保持科学含义不变。"
        elif comment_type == "editorial":
            change = "修改相关章节的措辞、术语或格式。"
        elif comment_type == "minor":
            change = "澄清相关句子或段落，并核对其与最终稿件一致。"
        else:
            change = "修改相关的 Methods、Results 或 Discussion 内容，并为回复补充可追溯证据。"
        if split_warnings:
            return (
                f"{change} 拆分提醒：{'；'.join(split_warnings)} "
                "终稿回复前需要人工校正。"
            )
        return change

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
