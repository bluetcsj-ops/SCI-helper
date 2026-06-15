from app.agents.prompts import (
    DATA_ANALYST_PROMPT,
    MENTOR_PROMPT,
    PROJECT_MANAGER_PROMPT,
    REVIEWER_PROMPT,
    STUDY_PLANNER_PROMPT,
    WRITER_PROMPT,
)
from app.agents.schemas import AgentId, AgentProfile


class AgentRegistry:
    def __init__(self) -> None:
        self._agents = {
            AgentId.project_manager: AgentProfile(
                id=AgentId.project_manager,
                name="Rhea Chen",
                role_name="全流程实施监控员",
                tagline="监控项目执行、风险、里程碑与提醒",
                responsibilities=[
                    "持续监控 Project A / Project B 的实施状态",
                    "识别延误、受阻任务和资源冲突",
                    "维护里程碑、截止日期和提醒策略",
                ],
                tools=["get_project_status", "send_telegram_message", "send_email", "reschedule_project_plan"],
                system_prompt=PROJECT_MANAGER_PROMPT.strip(),
                is_consultant=False,
            ),
            AgentId.mentor: AgentProfile(
                id=AgentId.mentor,
                name="Prof. RadOnc Mentor",
                role_name="虚拟导师",
                tagline="研究趋势导航与个人能力适配",
                responsibilities=[
                    "整理放疗物理研究趋势",
                    "分析用户设备、数据和能力画像",
                    "推荐可落地的 SCI 课题",
                ],
                tools=["query_trend_database", "create_trend_chart"],
                system_prompt=MENTOR_PROMPT.strip(),
            ),
            AgentId.study_planner: AgentProfile(
                id=AgentId.study_planner,
                name="Dr. Vera Protocol",
                role_name="论文和实验方案制定员",
                tagline="把课题转化为研究设计、实验方案与论文路线",
                responsibilities=[
                    "细化研究问题、假设和终点",
                    "制定实验流程、数据字段和统计路径",
                    "输出可交给 Rhea 监控执行的论文方案",
                ],
                tools=["create_study_protocol", "create_experiment_plan", "define_endpoints"],
                system_prompt=STUDY_PLANNER_PROMPT.strip(),
            ),
            AgentId.data_analyst: AgentProfile(
                id=AgentId.data_analyst,
                name="Dr. Data Lin",
                role_name="科研数据分析师",
                tagline="从数据到 SCI 级结果",
                responsibilities=[
                    "生成数据需求规格说明书",
                    "执行数据质量检查",
                    "生成统计结果和出版级图表",
                ],
                tools=["python_repl", "generate_statistical_report", "create_figure"],
                system_prompt=DATA_ANALYST_PROMPT.strip(),
            ),
            AgentId.writer: AgentProfile(
                id=AgentId.writer,
                name="Alex Writer",
                role_name="SCI 论文助理",
                tagline="定制化写作与格式优化",
                responsibilities=[
                    "学习用户既往论文风格",
                    "撰写论文大纲、方法、结果和讨论",
                    "管理真实文献与投稿格式",
                ],
                tools=["search_literature", "read_user_papers", "generate_latex", "create_flowchart"],
                system_prompt=WRITER_PROMPT.strip(),
            ),
            AgentId.reviewer: AgentProfile(
                id=AgentId.reviewer,
                name="Rev. Dr. Helena Skov",
                role_name="论文审查官",
                tagline="模拟严苛审稿人，提升命中率",
                responsibilities=[
                    "审查科学性和创新性",
                    "识别 AI 写作痕迹",
                    "生成审稿意见和返修回复策略",
                ],
                tools=["check_ai_traces", "generate_review_report", "search_trend_database"],
                system_prompt=REVIEWER_PROMPT.strip(),
            ),
        }

    def list_agents(self) -> list[AgentProfile]:
        return [agent for agent in self._agents.values() if agent.is_consultant]

    def list_all_agents(self) -> list[AgentProfile]:
        return list(self._agents.values())

    def get_agent(self, agent_id: str) -> AgentProfile | None:
        try:
            return self._agents[AgentId(agent_id)]
        except ValueError:
            return None


agent_registry = AgentRegistry()
