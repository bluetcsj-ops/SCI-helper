from __future__ import annotations

import json
import re
from typing import Any

from app.llm.client import llm_client
from app.projects.models import Project, ProjectProtocol, ProjectProtocolUpdate
from app.protocols.repository import protocol_repository


PROTOCOL_FIELDS: tuple[str, ...] = (
    "research_question",
    "hypothesis",
    "study_type",
    "primary_endpoint",
    "secondary_endpoints",
    "inclusion_criteria",
    "exclusion_criteria",
    "data_requirements",
    "experiment_workflow",
    "statistical_plan",
    "target_journals",
    "rhea_milestones",
)


FIELD_LABELS: dict[str, tuple[str, ...]] = {
    "research_question": ("研究问题", "research question"),
    "hypothesis": ("研究假设", "hypothesis"),
    "study_type": ("研究类型", "研究设计", "study type", "study design"),
    "primary_endpoint": ("主要终点", "primary endpoint"),
    "secondary_endpoints": ("次要终点", "secondary endpoint"),
    "inclusion_criteria": ("纳入标准", "纳入", "inclusion"),
    "exclusion_criteria": ("排除标准", "排除", "exclusion"),
    "data_requirements": ("数据需求", "数据字段", "导出路径", "data requirement"),
    "experiment_workflow": ("实验流程", "研究流程", "workflow"),
    "statistical_plan": ("统计路线", "统计分析", "statistical plan"),
    "target_journals": ("目标期刊", "target journal"),
    "rhea_milestones": ("里程碑", "时间计划", "下一步", "milestone"),
}


EXTRACTION_SYSTEM_PROMPT = """
你是一个医学物理科研方案结构化抽取器。你的任务是从 Dr. Vera Protocol 的中文长回复中抽取研究方案字段。

只允许输出一个 JSON 对象，不要输出 Markdown、解释、代码块或多余文本。

JSON 必须包含以下 key，缺失信息用空字符串：
research_question, hypothesis, study_type, primary_endpoint, secondary_endpoints,
inclusion_criteria, exclusion_criteria, data_requirements, experiment_workflow,
statistical_plan, target_journals, rhea_milestones。

抽取要求：
- 保留放疗物理标准术语，例如 DICOM-RT、RTDOSE、RTSTRUCT、CTV D95%、OAR、HI、CI、Gamma。
- 不要编造源文本中没有的信息。
- 如果原文把主要终点和次要终点写在同一段，请合理拆分。
- rhea_milestones 只放时间节点、交付物或下一步行动。
""".strip()


class ProtocolExtractor:
    def extract_and_save(self, project: Project, source_text: str) -> ProjectProtocol:
        normalized_text = source_text.strip()
        payload = self._extract_with_llm(project=project, source_text=normalized_text)
        if payload is None:
            payload = self._extract_with_headings(normalized_text)

        return protocol_repository.save_protocol(project_id=project.id, payload=payload)

    def _extract_with_llm(
        self,
        project: Project,
        source_text: str,
    ) -> ProjectProtocolUpdate | None:
        if not llm_client.is_configured:
            return None

        try:
            result = llm_client.create_text_response(
                system_prompt=EXTRACTION_SYSTEM_PROMPT,
                user_content="\n\n".join(
                    [
                        f"当前项目：{project.name} - {project.title}",
                        f"课题：{project.topic}",
                        "待抽取文本：",
                        source_text,
                    ]
                ),
            )
            payload = self._payload_from_json_text(result.text)
            if payload is None or not self._has_payload_content(payload):
                return None
            return payload
        except Exception:
            return None

    def _payload_from_json_text(self, text: str) -> ProjectProtocolUpdate | None:
        raw_json = self._find_json_object(text)
        if raw_json is None:
            return None

        try:
            parsed = json.loads(raw_json)
        except json.JSONDecodeError:
            return None

        if not isinstance(parsed, dict):
            return None

        return ProjectProtocolUpdate(
            **{
                field_name: self._stringify_value(parsed.get(field_name, ""))
                for field_name in PROTOCOL_FIELDS
            }
        )

    def _find_json_object(self, text: str) -> str | None:
        stripped_text = text.strip()
        if stripped_text.startswith("```"):
            stripped_text = re.sub(r"^```(?:json)?\s*", "", stripped_text)
            stripped_text = re.sub(r"\s*```$", "", stripped_text)

        if stripped_text.startswith("{") and stripped_text.endswith("}"):
            return stripped_text

        match = re.search(r"\{.*\}", stripped_text, flags=re.DOTALL)
        if match is None:
            return None
        return match.group(0)

    def _extract_with_headings(self, source_text: str) -> ProjectProtocolUpdate:
        sections: dict[str, list[str]] = {field_name: [] for field_name in PROTOCOL_FIELDS}
        current_field: str | None = None

        for raw_line in source_text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            matched_field = self._match_heading(line)
            if matched_field is not None:
                current_field = matched_field
                remainder = self._remove_heading_label(line)
                if remainder:
                    sections[current_field].append(remainder)
                continue

            if current_field is not None:
                sections[current_field].append(raw_line)

        payload = {
            field_name: "\n".join(lines).strip()
            for field_name, lines in sections.items()
        }

        if not any(payload.values()):
            payload["research_question"] = source_text[:4000]

        return ProjectProtocolUpdate(**payload)

    def _match_heading(self, line: str) -> str | None:
        normalized_line = re.sub(r"^[#\-\*\s\d.、（）()]+", "", line).lower()
        heading_prefix = normalized_line[:80]

        for field_name, labels in FIELD_LABELS.items():
            if any(label.lower() in heading_prefix for label in labels):
                return field_name

        return None

    def _remove_heading_label(self, line: str) -> str:
        if "：" not in line and ":" not in line:
            return ""
        return re.sub(r"^[#\-\*\s\d.、（）()]*[^：:]{0,30}[：:]\s*", "", line).strip()

    def _stringify_value(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, list):
            return "\n".join(self._stringify_value(item) for item in value).strip()
        if isinstance(value, dict):
            return json.dumps(value, ensure_ascii=False, indent=2)
        return str(value).strip()

    def _has_payload_content(self, payload: ProjectProtocolUpdate) -> bool:
        return any(value.strip() for value in payload.model_dump().values())


protocol_extractor = ProtocolExtractor()
