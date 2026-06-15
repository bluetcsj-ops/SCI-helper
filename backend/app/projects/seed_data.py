from datetime import date, timedelta

from app.projects.models import ItemStatus, Phase, Project, RiskLevel, Task


def build_seed_projects() -> list[Project]:
    today = date.today()
    return [
        Project(
            id="project-a",
            name="Project A",
            title="MR 引导自适应放疗剂量学评估",
            topic="基于每日 MR 引导在线自适应计划的累积剂量与计划质量分析",
            current_phase="阶段 1：细化研究假设与文献回顾",
            progress_percent=18,
            risk_level=RiskLevel.green,
            stage_days_remaining=9,
            next_milestone="完成研究假设、PICO 问题和 15 篇核心文献矩阵",
            next_due_date=today + timedelta(days=9),
            phases=[
                Phase(
                    id="a-phase-1",
                    title="细化研究假设与文献回顾",
                    status=ItemStatus.in_progress,
                    start_date=today - timedelta(days=5),
                    end_date=today + timedelta(days=9),
                    deliverables=["研究假设", "PICO 问题", "核心文献矩阵"],
                ),
                Phase(
                    id="a-phase-2",
                    title="伦理审批/数据采集准备",
                    status=ItemStatus.not_started,
                    start_date=today + timedelta(days=10),
                    end_date=today + timedelta(days=31),
                    deliverables=["伦理材料清单", "数据导出规范", "病例筛选标准"],
                ),
            ],
            tasks=[
                Task(
                    id="a-task-1",
                    title="整理 MR-linac 自适应放疗核心文献",
                    due_date=today + timedelta(days=4),
                    status=ItemStatus.in_progress,
                    owner_agent_id="mentor",
                    deliverable="15 篇文献的研究对象、终点和统计方法矩阵",
                ),
                Task(
                    id="a-task-2",
                    title="确认可导出的 DICOM-RT 数据字段",
                    due_date=today + timedelta(days=7),
                    status=ItemStatus.not_started,
                    owner_agent_id="data_analyst",
                    deliverable="数据字段与导出路径清单",
                ),
            ],
        ),
        Project(
            id="project-b",
            name="Project B",
            title="VMAT 计划质量预测模型",
            topic="结合患者解剖特征与计划参数预测 VMAT 三维剂量分布",
            current_phase="阶段 0：课题候选与资源评估",
            progress_percent=8,
            risk_level=RiskLevel.orange,
            stage_days_remaining=14,
            next_milestone="确认样本来源、建模输入变量和最低可行样本量",
            next_due_date=today + timedelta(days=14),
            phases=[
                Phase(
                    id="b-phase-0",
                    title="课题候选与资源评估",
                    status=ItemStatus.in_progress,
                    start_date=today - timedelta(days=2),
                    end_date=today + timedelta(days=14),
                    deliverables=["样本来源说明", "输入变量候选表", "最低样本量估计"],
                ),
                Phase(
                    id="b-phase-1",
                    title="细化研究假设与文献回顾",
                    status=ItemStatus.not_started,
                    start_date=today + timedelta(days=15),
                    end_date=today + timedelta(days=28),
                    deliverables=["研究假设", "模型任务定义", "目标期刊候选"],
                ),
            ],
            tasks=[
                Task(
                    id="b-task-1",
                    title="列出可访问的 VMAT 病例和计划系统版本",
                    due_date=today + timedelta(days=6),
                    status=ItemStatus.in_progress,
                    owner_agent_id="project_manager",
                    deliverable="病例来源、纳入排除标准和软件版本记录",
                ),
                Task(
                    id="b-task-2",
                    title="定义模型输入与输出",
                    due_date=today + timedelta(days=12),
                    status=ItemStatus.not_started,
                    owner_agent_id="data_analyst",
                    deliverable="输入变量、输出剂量指标和评价指标清单",
                ),
            ],
        ),
    ]
