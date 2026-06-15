from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from app.projects.models import ItemStatus, Phase, Project, ProjectPlanDraft, ProjectProtocol, Task
from app.projects.plan_drafts import project_plan_draft_repository
from app.protocols.repository import protocol_repository


@dataclass(frozen=True)
class PhaseTemplate:
    title: str
    start_day: int
    end_day: int
    deliverables: list[str]


class ProjectPlanGenerator:
    def generate_draft_from_protocol(self, project: Project) -> ProjectPlanDraft:
        protocol = protocol_repository.get_protocol(project.id)
        if not self._has_protocol_basis(protocol):
            raise ValueError("Protocol is too empty to generate an execution plan")

        today = date.today()
        phases = self._build_phases(project_id=project.id, today=today, protocol=protocol)
        tasks = self._build_tasks(project_id=project.id, today=today, protocol=protocol)
        return project_plan_draft_repository.create_draft(
            project=project,
            protocol=protocol,
            phases=phases,
            tasks=tasks,
        )

    def _build_phases(
        self,
        project_id: str,
        today: date,
        protocol: ProjectProtocol,
    ) -> list[Phase]:
        templates = [
            PhaseTemplate(
                title="阶段 1：细化研究假设与文献回顾",
                start_day=0,
                end_day=14,
                deliverables=[
                    "锁定研究问题与主要终点",
                    "完成核心文献矩阵",
                    self._compact(protocol.hypothesis, "研究假设确认稿"),
                ],
            ),
            PhaseTemplate(
                title="阶段 2：伦理审批/数据采集准备",
                start_day=15,
                end_day=35,
                deliverables=[
                    "完成纳入排除标准",
                    "完成数据字段字典",
                    self._compact(protocol.data_requirements, "DICOM-RT/CSV 数据需求清单"),
                ],
            ),
            PhaseTemplate(
                title="阶段 3：数据收集与整理",
                start_day=36,
                end_day=77,
                deliverables=[
                    "完成首批样本导出",
                    "完成全量病例整理",
                    "输出数据质量问题清单",
                ],
            ),
            PhaseTemplate(
                title="阶段 4：统计分析与图表生成",
                start_day=78,
                end_day=98,
                deliverables=[
                    self._compact(protocol.statistical_plan, "统计分析脚本与结果表"),
                    "生成论文级图表",
                    "输出统计方法段落草案",
                ],
            ),
            PhaseTemplate(
                title="阶段 5：论文初稿撰写",
                start_day=99,
                end_day=140,
                deliverables=[
                    "完成方法与结果初稿",
                    "完成讨论与结论初稿",
                    self._compact(protocol.target_journals, "目标期刊与格式清单"),
                ],
            ),
            PhaseTemplate(
                title="阶段 6：内部审稿与修改",
                start_day=141,
                end_day=154,
                deliverables=[
                    "完成模拟审稿意见",
                    "完成逐条修改记录",
                    "确认统计与结论一致性",
                ],
            ),
            PhaseTemplate(
                title="阶段 7：选刊、格式调整与投稿",
                start_day=155,
                end_day=168,
                deliverables=[
                    "完成投稿文件包",
                    "完成 cover letter",
                    "提交目标期刊",
                ],
            ),
        ]

        return [
            Phase(
                id=f"{project_id}-generated-phase-{index}",
                title=template.title,
                status=ItemStatus.in_progress if index == 1 else ItemStatus.not_started,
                start_date=today + timedelta(days=template.start_day),
                end_date=today + timedelta(days=template.end_day),
                deliverables=template.deliverables,
            )
            for index, template in enumerate(templates, start=1)
        ]

    def _build_tasks(
        self,
        project_id: str,
        today: date,
        protocol: ProjectProtocol,
    ) -> list[Task]:
        task_specs = [
            (
                "锁定研究问题、假设和 PECO/PICO 框架",
                7,
                "study_planner",
                self._compact(protocol.research_question, "研究问题、假设和 PECO/PICO 框架确认稿"),
                ItemStatus.in_progress,
            ),
            (
                "完成核心文献矩阵和目标期刊初筛",
                14,
                "mentor",
                self._compact(protocol.target_journals, "15 篇核心文献矩阵和 2-3 个候选期刊"),
                ItemStatus.not_started,
            ),
            (
                "确认病例标准与伦理/数据审批材料",
                24,
                "study_planner",
                self._join_parts(
                    [
                        self._compact(protocol.inclusion_criteria, "纳入标准"),
                        self._compact(protocol.exclusion_criteria, "排除标准"),
                        "伦理或数据使用审批材料清单",
                    ]
                ),
                ItemStatus.not_started,
            ),
            (
                "完成数据字段字典和导出路径确认",
                35,
                "data_analyst",
                self._compact(protocol.data_requirements, "数据字段、命名规则和导出路径清单"),
                ItemStatus.not_started,
            ),
            (
                "完成首批 10 例数据导出与质量核查",
                49,
                "data_analyst",
                "10 例样本数据包、缺失值清单和异常病例问题列表",
                ItemStatus.not_started,
            ),
            (
                "完成全量数据收集与清洗",
                77,
                "data_analyst",
                "全量分析数据集、数据质量报告和可复现清洗脚本",
                ItemStatus.not_started,
            ),
            (
                "完成统计分析和论文图表",
                98,
                "data_analyst",
                self._compact(protocol.statistical_plan, "统计结果表、300 dpi 图表和统计方法段落"),
                ItemStatus.not_started,
            ),
            (
                "完成方法和结果部分初稿",
                119,
                "writer",
                self._compact(protocol.experiment_workflow, "Methods、Results 初稿和流程图 caption"),
                ItemStatus.not_started,
            ),
            (
                "完成全文初稿",
                140,
                "writer",
                "Title page、Abstract、Introduction、Methods、Results、Discussion、Conclusion 初稿",
                ItemStatus.not_started,
            ),
            (
                "完成模拟审稿与投稿文件包",
                168,
                "reviewer",
                "模拟审稿报告、修改清单、投稿文件命名清单和 cover letter 草案",
                ItemStatus.not_started,
            ),
        ]

        return [
            Task(
                id=f"{project_id}-generated-task-{index}",
                title=title,
                due_date=today + timedelta(days=due_day),
                status=status,
                owner_agent_id=owner_agent_id,
                deliverable=deliverable,
            )
            for index, (title, due_day, owner_agent_id, deliverable, status) in enumerate(
                task_specs,
                start=1,
            )
        ]

    def _has_protocol_basis(self, protocol: ProjectProtocol) -> bool:
        required_values = [
            protocol.research_question,
            protocol.hypothesis,
            protocol.primary_endpoint,
            protocol.data_requirements,
            protocol.statistical_plan,
        ]
        return any(value.strip() for value in required_values)

    def _compact(self, value: str, fallback: str) -> str:
        cleaned_value = " ".join(value.split())
        if not cleaned_value:
            return fallback
        if len(cleaned_value) <= 160:
            return cleaned_value
        return f"{cleaned_value[:157]}..."

    def _join_parts(self, parts: list[str]) -> str:
        return "；".join(part for part in parts if part.strip())


project_plan_generator = ProjectPlanGenerator()
