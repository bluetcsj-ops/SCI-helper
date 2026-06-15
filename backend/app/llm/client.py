from dataclasses import dataclass

from openai import OpenAI

from app.agents.schemas import AgentProfile
from app.core.config import settings
from app.projects.models import ItemStatus, Project, RiskLevel


STATUS_LABELS: dict[ItemStatus, str] = {
    ItemStatus.not_started: "未开始",
    ItemStatus.in_progress: "进行中",
    ItemStatus.blocked: "受阻",
    ItemStatus.done: "已完成",
}

RISK_LABELS: dict[RiskLevel, str] = {
    RiskLevel.green: "正常",
    RiskLevel.orange: "轻微延误",
    RiskLevel.red: "严重风险",
}


@dataclass(frozen=True)
class LLMResult:
    text: str
    source: str


class LLMClient:
    def __init__(self) -> None:
        self.provider = settings.llm_provider.lower()
        self._client = self._build_client()

    @property
    def is_configured(self) -> bool:
        return self._client is not None

    @property
    def source_name(self) -> str:
        return self.provider

    def create_agent_reply(
        self,
        agent: AgentProfile,
        message: str,
        project: Project | None,
    ) -> LLMResult:
        if self._client is None:
            raise RuntimeError(f"{self.provider} is not configured")

        response = self._client.chat.completions.create(
            model=self._model_name(),
            messages=[
                {
                    "role": "system",
                    "content": self._build_system_prompt(agent=agent, project=project),
                },
                {
                    "role": "user",
                    "content": message,
                },
            ],
        )
        content = response.choices[0].message.content or ""
        return LLMResult(text=content.strip(), source=self.provider)

    def create_text_response(self, system_prompt: str, user_content: str) -> LLMResult:
        if self._client is None:
            raise RuntimeError(f"{self.provider} is not configured")

        response = self._client.chat.completions.create(
            model=self._model_name(),
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_content,
                },
            ],
            temperature=0,
        )
        content = response.choices[0].message.content or ""
        return LLMResult(text=content.strip(), source=self.provider)

    def _build_client(self) -> OpenAI | None:
        if self.provider == "deepseek":
            if not settings.deepseek_api_key:
                return None
            return OpenAI(
                api_key=settings.deepseek_api_key,
                base_url=settings.deepseek_base_url,
            )

        if self.provider == "openai":
            if not settings.openai_api_key:
                return None
            return OpenAI(api_key=settings.openai_api_key)

        return None

    def _model_name(self) -> str:
        if self.provider == "deepseek":
            return settings.deepseek_model
        return settings.openai_model

    def _build_system_prompt(self, agent: AgentProfile, project: Project | None) -> str:
        return "\n\n".join(
            [
                agent.system_prompt,
                "你正在本平台中服务一名放射治疗物理师。请始终使用简体中文回答，保持专业、具体、可执行。",
                "不要编造数据、文献、期刊要求或用户未提供的信息；不确定时请明确说明需要补充什么。",
                self._format_project_context(project),
                "回答应优先给出当前可执行的下一步，避免空泛鼓励。",
            ]
        )

    def _format_project_context(self, project: Project | None) -> str:
        if project is None:
            return "当前没有关联具体项目。请先帮助用户澄清课题、数据和下一步。"

        phase_lines = [
            f"- {phase.title}：{STATUS_LABELS[phase.status]}，周期 {phase.start_date.isoformat()} 至 {phase.end_date.isoformat()}"
            for phase in project.phases
        ]
        task_lines = [
            f"- {task.title}：{STATUS_LABELS[task.status]}，截止 {task.due_date.isoformat()}，交付物：{task.deliverable}"
            for task in project.tasks
        ]

        return "\n".join(
            [
                "当前项目上下文：",
                f"项目：{project.name} - {project.title}",
                f"课题：{project.topic}",
                f"当前阶段：{project.current_phase}",
                f"总体进度：{project.progress_percent}%",
                f"风险状态：{RISK_LABELS[project.risk_level]}",
                f"下一里程碑：{project.next_milestone}",
                f"下一截止日期：{project.next_due_date.isoformat()}",
                "阶段：",
                *phase_lines,
                "任务：",
                *task_lines,
            ]
        )


llm_client = LLMClient()
