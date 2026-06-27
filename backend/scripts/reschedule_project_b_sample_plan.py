from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.projects.models import ItemStatus, Phase, Task
from app.projects.repository import project_repository
from app.reminders.repository import reminder_repository


PROJECT_ID = "project-b"


def main() -> None:
    today = date.today()
    project = project_repository.get_project(PROJECT_ID)
    if project is None:
        raise SystemExit("Project B not found.")

    task_by_id = {task.id: task for task in project.tasks}
    required_task_ids = {"b-task-1", "b-task-2"}
    missing_task_ids = sorted(required_task_ids.difference(task_by_id))
    if missing_task_ids:
        raise SystemExit(f"Project B is missing expected sample tasks: {', '.join(missing_task_ids)}")

    phases = [
        Phase(
            id="b-phase-0",
            title="课题候选与资源评估",
            status=ItemStatus.in_progress,
            start_date=today,
            end_date=today + timedelta(days=14),
            deliverables=[
                "样本来源说明",
                "输入变量候选表",
                "最低样本量估计",
                "Project B 仍为预设样例工作区，不代表真实机构 protocol。",
            ],
        ),
        Phase(
            id="b-phase-1",
            title="细化研究假设与文献回顾",
            status=ItemStatus.not_started,
            start_date=today + timedelta(days=15),
            end_date=today + timedelta(days=28),
            deliverables=[
                "研究假设",
                "模型任务定义",
                "目标期刊候选",
            ],
        ),
    ]
    tasks = [
        Task(
            id="b-task-1",
            title=task_by_id["b-task-1"].title,
            due_date=today + timedelta(days=7),
            status=ItemStatus.in_progress,
            owner_agent_id=task_by_id["b-task-1"].owner_agent_id,
            deliverable=(
                f"{task_by_id['b-task-1'].deliverable}；样例计划重排后需继续人工确认真实病例来源、"
                "纳排标准、TPS 版本和数据授权。"
            ),
        ),
        Task(
            id="b-task-2",
            title=task_by_id["b-task-2"].title,
            due_date=today + timedelta(days=14),
            status=ItemStatus.not_started,
            owner_agent_id=task_by_id["b-task-2"].owner_agent_id,
            deliverable=(
                f"{task_by_id['b-task-2'].deliverable}；仅作为 Project B 预设流程演示，"
                "正式建模前仍需统计复核。"
            ),
        ),
    ]

    updated_project = project_repository.replace_project_plan(
        project_id=PROJECT_ID,
        phases=phases,
        tasks=tasks,
        current_phase="阶段 0：课题候选与资源评估（样例计划已重排）",
    )
    if updated_project is None:
        raise SystemExit("Project B plan update failed.")

    reminder_repository.refresh_project_reminders(updated_project)
    reminder_summary = reminder_repository.get_project_summary(PROJECT_ID)

    print(
        "Project B sample plan rescheduled: "
        f"progress={updated_project.progress_percent}%, "
        f"risk={updated_project.risk_level.value}, "
        f"next_due={updated_project.next_due_date.isoformat()}, "
        f"active_reminders={reminder_summary.active_count if reminder_summary else 'n/a'}, "
        f"overdue={reminder_summary.overdue_count if reminder_summary else 'n/a'}"
    )


if __name__ == "__main__":
    main()
