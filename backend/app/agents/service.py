from dataclasses import dataclass

from app.agents.schemas import AgentId, AgentProfile
from app.llm.client import llm_client
from app.projects.models import Project


@dataclass(frozen=True)
class AgentReply:
    reply: str
    suggested_next_actions: list[str]
    response_source: str
    fallback_reason: str | None = None


class AgentService:
    def create_reply(
        self,
        agent: AgentProfile,
        message: str,
        project: Project | None,
    ) -> AgentReply:
        if llm_client.is_configured:
            try:
                result = llm_client.create_agent_reply(
                    agent=agent,
                    message=message,
                    project=project,
                )
                return AgentReply(
                    reply=result.text,
                    suggested_next_actions=self._default_actions(agent.id),
                    response_source=result.source,
                )
            except Exception as exc:
                mock_reply, actions = self._create_mock_reply(agent=agent, project=project)
                return AgentReply(
                    reply=mock_reply,
                    suggested_next_actions=actions,
                    response_source="mock",
                    fallback_reason=f"{llm_client.source_name} 调用失败，已回退到模拟回复：{exc}",
                )

        mock_reply, actions = self._create_mock_reply(agent=agent, project=project)
        return AgentReply(
            reply=mock_reply,
            suggested_next_actions=actions,
            response_source="mock",
            fallback_reason=f"未配置 {llm_client.source_name} API key，使用模拟回复。",
        )

    def _create_mock_reply(
        self,
        agent: AgentProfile,
        project: Project | None,
    ) -> tuple[str, list[str]]:
        project_line = ""
        if project is not None:
            project_line = (
                f"\n\n当前关联项目：{project.name}，阶段：{project.current_phase}，"
                f"进度：{project.progress_percent}%。"
            )

        if agent.id == AgentId.mentor:
            return (
                "我已经收到你的问题。原型阶段我会先从研究趋势、设备条件、可获得数据和发表可行性四个维度帮你判断课题价值。"
                f"{project_line}\n\n下一步建议先补充：设备型号、计划系统、可导出的 DICOM-RT 数据类型、每周科研时间和你最感兴趣的方向。",
                self._default_actions(agent.id),
            )

        if agent.id == AgentId.project_manager:
            return (
                "我正在监控整个论文工场的实施情况，不作为普通咨询角色提供开放式讨论。"
                f"{project_line}\n\n请优先查看仪表盘、任务状态和下一里程碑；如果出现受阻或延误，我会把风险推到页面最前面。",
                self._default_actions(agent.id),
            )

        if agent.id == AgentId.study_planner:
            return (
                "我会把已确认的课题转化为具体的论文和实验方案，包括研究假设、终点、病例标准、数据字段、实验流程和统计路线。"
                f"{project_line}\n\n下一步建议先确认研究问题、主要终点、可获得数据和目标期刊层级。",
                self._default_actions(agent.id),
            )

        if agent.id == AgentId.data_analyst:
            return (
                "我会先生成《数据需求规格说明书》，明确变量、格式、分组逻辑和最低样本量。"
                f"{project_line}\n\n请优先准备 CSV 字段字典、DICOM-RT 导出说明和分组规则；在真实分析前，我不会对缺失或异常数据做任何未经确认的假设。",
                self._default_actions(agent.id),
            )

        if agent.id == AgentId.writer:
            return (
                "我会先基于课题方案生成论文大纲和摘要草稿，等数据分析结果完成后再写结果和讨论。"
                f"{project_line}\n\n后续我可以读取你的 `My SCI article` 目录来学习写作风格，但引用文献必须来自真实可查来源。",
                self._default_actions(agent.id),
            )

        if agent.id == AgentId.reviewer:
            return (
                "我会从科学性、创新性和 AI 痕迹三个维度审查稿件。"
                f"{project_line}\n\n如果结论超出数据支持范围，我会直接指出并要求修改；每条批评都会附带具体修复路径。",
                self._default_actions(agent.id),
            )

        return (
            f"{agent.name} 已收到消息。",
            self._default_actions(agent.id),
        )

    def _default_actions(self, agent_id: AgentId) -> list[str]:
        actions = {
            AgentId.mentor: ["补充设备与软件信息", "选择 2-3 个兴趣方向", "确认是否已有可用病例数据"],
            AgentId.project_manager: ["查看风险任务", "确认最近里程碑", "必要时重新排期"],
            AgentId.study_planner: ["明确研究假设", "定义主要和次要终点", "生成实验流程草案"],
            AgentId.data_analyst: ["列出核心终点变量", "确认分组逻辑", "准备 5-10 例样例数据用于质控"],
            AgentId.writer: ["确认目标期刊", "整理方法学细节", "准备既往论文风格样本"],
            AgentId.reviewer: ["上传论文初稿", "提供目标期刊", "标记最担心被审稿人质疑的部分"],
        }
        return actions.get(agent_id, ["继续补充上下文", "选择关联项目", "确认下一步行动"])


agent_service = AgentService()
