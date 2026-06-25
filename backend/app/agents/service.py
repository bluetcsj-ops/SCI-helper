from dataclasses import dataclass
from typing import Any

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
        context: dict[str, Any] | None = None,
    ) -> AgentReply:
        if llm_client.is_configured:
            try:
                result = llm_client.create_agent_reply(
                    agent=agent,
                    message=message,
                    project=project,
                    context=context,
                )
                return AgentReply(
                    reply=result.text,
                    suggested_next_actions=self._default_actions(agent.id),
                    response_source=result.source,
                )
            except Exception as exc:
                mock_reply, actions = self._create_mock_reply(agent=agent, project=project, context=context)
                return AgentReply(
                    reply=mock_reply,
                    suggested_next_actions=actions,
                    response_source="mock",
                    fallback_reason=f"{llm_client.source_name} 调用失败，已回退到模拟回复：{exc}",
                )

        mock_reply, actions = self._create_mock_reply(agent=agent, project=project, context=context)
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
        context: dict[str, Any] | None = None,
    ) -> tuple[str, list[str]]:
        project_line = ""
        if project is not None:
            project_line = (
                f"\n\n当前关联项目：{project.name}，阶段：{project.current_phase}，"
                f"进度：{project.progress_percent}%。"
            )

        context_line = self._format_context_line(context)
        if context_line:
            project_line = f"{project_line}{context_line}"

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
                "## 研究问题\n"
                "围绕用户与 Mentor 已确认的放疗物理研究方向，形成一个可用样例数据验证、后续可接入真实脱敏数据的研究问题。\n\n"
                "## 研究假设\n"
                "候选方法或流程指标能够解释计划质量、QA 结果、剂量学差异或工作流效率差异，但该假设仍需 Data Lin 和人工统计复核验证。\n\n"
                "## 研究类型\n"
                "Vera protocol 草案：单中心回顾性放疗物理研究；PICO/PECO 框架需在 Mentor 讨论后锁定对象、暴露/干预、比较组和主要结局。\n\n"
                "## 主要终点\n"
                "从 Mentor 推荐方向中选择一个最能回答研究问题的可量化终点，例如计划质量、OAR 保护、QA 结果、流程耗时或模型性能。\n\n"
                "## 次要终点\n"
                "靶区覆盖、剂量梯度、适形指数、计划复杂度、处理时间、返工率、亚组稳定性和敏感性分析。\n\n"
                "## 纳入标准\n"
                "纳入与研究问题匹配、关键计划/剂量/结构或流程字段可获得、并可在真实数据阶段完成脱敏和来源追踪的数据记录。\n\n"
                "## 排除标准\n"
                "排除关键字段缺失、计划或影像质量不可复核、治疗流程中断、数据来源不一致、以及存在直接身份标识或脱敏不充分风险的记录。\n\n"
                "## 数据需求\n"
                "先列出候选最小字段、数据来源、导出格式和字段字典草案；预备数据只能用于流程验证，不能作为最终研究证据。\n\n"
                "## 正式研究前确认\n"
                "Project A / B 是工作区样例，不代表真实机构 protocol。真实数据接入或投稿前，再人工确认 IRB/豁免、数据使用授权、脱敏规则、字段字典、CSV 导出路径、TPS/DICOM/QA 追踪和统计复核责任人。\n\n"
                "## 实验流程\n"
                "1. 与 Mentor 锁定研究方向和 PICO/PECO；2. 生成字段需求并做预备 CSV 质控；3. 收窄终点和统计路线；4. 生成 Rhea 里程碑；5. 交给 Writer/Reviewer 做写作边界和投稿前风险检查。\n\n"
                "## 统计路线\n"
                "先做描述统计、分组或配对比较和效应量；预测或高级模型只能作为 exploratory draft，正式 P 值、CI、模型诊断和样本量解释需人工复核。\n\n"
                "## 目标期刊\n"
                "待 Mentor 根据研究方向、数据可得性和方法学强度确认。\n\n"
                "## Rhea 里程碑\n"
                "方案确认；数据预检；统计预案；写作边界；投稿前复核。"
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

    def _format_context_line(self, context: dict[str, Any] | None) -> str:
        if not context:
            return ""

        lines: list[str] = []
        for key in ("project_memory_summary", "current_protocol_summary", "recent_project_messages"):
            value = context.get(key)
            if isinstance(value, list):
                for item in value:
                    line = str(item).strip()
                    if line and line not in lines:
                        lines.append(line)
                    if len(lines) >= 6:
                        break
            if len(lines) >= 6:
                break

        if not lines:
            return ""

        formatted_lines = "\n".join(f"- {line}" for line in lines[:6])
        return (
            "\n\n项目共享记录（仅作上下文参考，不等于真实数据、伦理审批、机构授权或已验证结论）：\n"
            f"{formatted_lines}"
        )


agent_service = AgentService()
