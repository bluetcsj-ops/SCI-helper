from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy import select

from app.db.models import TaskReminderRecord
from app.db.session import SessionLocal
from app.projects.models import (
    ItemStatus,
    Project,
    ProjectReminderSummary,
    ReminderStatus,
    ReminderType,
    RiskLevel,
    Task,
    TaskReminder,
)
from app.projects.repository import project_repository


@dataclass(frozen=True)
class ReminderSpec:
    task: Task
    reminder_type: ReminderType
    severity: RiskLevel
    trigger_date: date
    message: str
    suggested_action: str


class ReminderRepository:
    def get_project_summary(self, project_id: str) -> ProjectReminderSummary | None:
        project = project_repository.get_project(project_id)
        if project is None:
            return None

        self.refresh_project_reminders(project)
        reminders = self.list_project_reminders(project)
        today = date.today()
        active_reminders = [
            reminder for reminder in reminders if reminder.status != ReminderStatus.dismissed
        ]
        overdue_count = sum(
            1
            for task in project.tasks
            if task.status != ItemStatus.done and task.due_date < today
        )
        blocked_count = sum(1 for task in project.tasks if task.status == ItemStatus.blocked)
        next_due_count = sum(
            1
            for task in project.tasks
            if task.status != ItemStatus.done and 0 <= (task.due_date - today).days <= 2
        )
        risk_level = self._combine_risk([reminder.severity for reminder in active_reminders])

        return ProjectReminderSummary(
            project_id=project.id,
            generated_at=datetime.utcnow(),
            risk_level=risk_level,
            active_count=len(active_reminders),
            overdue_count=overdue_count,
            blocked_count=blocked_count,
            next_due_count=next_due_count,
            manager_note=self._build_manager_note(
                project=project,
                risk_level=risk_level,
                active_count=len(active_reminders),
                overdue_count=overdue_count,
                blocked_count=blocked_count,
                next_due_count=next_due_count,
            ),
            reminders=active_reminders,
        )

    def list_project_reminders(self, project: Project) -> list[TaskReminder]:
        task_map = {task.id: task for task in project.tasks}
        with SessionLocal() as session:
            records = session.scalars(
                select(TaskReminderRecord)
                .where(TaskReminderRecord.project_id == project.id)
                .order_by(TaskReminderRecord.trigger_date, TaskReminderRecord.id)
            ).all()

            reminders = [
                self._to_reminder(record, task_map[record.task_id])
                for record in records
                if record.task_id in task_map
            ]
            return sorted(
                reminders,
                key=lambda reminder: (
                    reminder.status == ReminderStatus.dismissed,
                    reminder.trigger_date,
                    reminder.due_date,
                ),
            )

    def refresh_project_reminders(self, project: Project) -> None:
        today = date.today()
        specs = self._build_specs(project, today)
        desired_keys = {(spec.task.id, spec.reminder_type.value) for spec in specs}

        with SessionLocal() as session:
            records = session.scalars(
                select(TaskReminderRecord).where(TaskReminderRecord.project_id == project.id)
            ).all()
            record_map = {
                (record.task_id, record.reminder_type): record
                for record in records
            }

            for spec in specs:
                key = (spec.task.id, spec.reminder_type.value)
                record = record_map.get(key)
                if record is None:
                    session.add(
                        TaskReminderRecord(
                            project_id=project.id,
                            task_id=spec.task.id,
                            reminder_type=spec.reminder_type.value,
                            severity=spec.severity.value,
                            status=ReminderStatus.pending.value,
                            trigger_date=spec.trigger_date,
                            message=spec.message,
                            suggested_action=spec.suggested_action,
                        )
                    )
                    continue

                if record.status == ReminderStatus.dismissed.value:
                    continue

                record.severity = spec.severity.value
                record.trigger_date = spec.trigger_date
                record.message = spec.message
                record.suggested_action = spec.suggested_action

            for key, record in record_map.items():
                if key not in desired_keys and record.status != ReminderStatus.dismissed.value:
                    record.status = ReminderStatus.dismissed.value
                    record.dismissed_at = datetime.utcnow()

            session.commit()

    def dismiss_reminder(self, project_id: str, reminder_id: int) -> ProjectReminderSummary | None:
        project = project_repository.get_project(project_id)
        if project is None:
            return None

        with SessionLocal() as session:
            record = session.scalar(
                select(TaskReminderRecord).where(
                    TaskReminderRecord.project_id == project_id,
                    TaskReminderRecord.id == reminder_id,
                )
            )
            if record is None:
                return None

            record.status = ReminderStatus.dismissed.value
            record.dismissed_at = datetime.utcnow()
            session.commit()

        return self.get_project_summary(project_id)

    def _build_specs(self, project: Project, today: date) -> list[ReminderSpec]:
        specs: list[ReminderSpec] = []
        for task in project.tasks:
            if task.status == ItemStatus.done:
                continue

            days_until_due = (task.due_date - today).days
            if task.status == ItemStatus.blocked:
                specs.append(
                    ReminderSpec(
                        task=task,
                        reminder_type=ReminderType.blocked,
                        severity=RiskLevel.red,
                        trigger_date=today,
                        message=f"任务“{task.title}”当前处于受阻状态。我们需要先排除障碍，再继续推进。",
                        suggested_action="请记录阻塞原因，并决定是补充材料、调整截止日期，还是请求对应智能体协助。",
                    )
                )
                continue

            if days_until_due < 0:
                overdue_days = abs(days_until_due)
                specs.append(
                    ReminderSpec(
                        task=task,
                        reminder_type=ReminderType.overdue,
                        severity=RiskLevel.red,
                        trigger_date=task.due_date,
                        message=f"任务“{task.title}”已经逾期 {overdue_days} 天，需要今天重新确认处理方式。",
                        suggested_action="建议先完成最小可交付版本；如果确实无法完成，请更新任务状态或重新排期。",
                    )
                )
                continue

            if days_until_due <= 1:
                specs.append(
                    ReminderSpec(
                        task=task,
                        reminder_type=ReminderType.due_24h,
                        severity=RiskLevel.orange,
                        trigger_date=max(task.due_date, today),
                        message=f"任务“{task.title}”将在 24 小时内到期。我们一起把这个收口。",
                        suggested_action="请检查交付物是否已经齐全；若还缺材料，优先补最影响下一阶段的部分。",
                    )
                )
                continue

            if days_until_due <= 2:
                specs.append(
                    ReminderSpec(
                        task=task,
                        reminder_type=ReminderType.due_48h,
                        severity=RiskLevel.green,
                        trigger_date=today,
                        message=f"任务“{task.title}”还有约 48 小时到期，现在适合做一次轻量检查。",
                        suggested_action="建议确认文件、数据或文字草稿是否已经放到正确位置。",
                    )
                )

        return specs

    def _combine_risk(self, risks: list[RiskLevel]) -> RiskLevel:
        if RiskLevel.red in risks:
            return RiskLevel.red
        if RiskLevel.orange in risks:
            return RiskLevel.orange
        return RiskLevel.green

    def _build_manager_note(
        self,
        project: Project,
        risk_level: RiskLevel,
        active_count: int,
        overdue_count: int,
        blocked_count: int,
        next_due_count: int,
    ) -> str:
        if active_count == 0:
            return f"{project.name} 当前没有需要提醒的任务，节奏很好。请继续推进最近一个里程碑。"
        if risk_level == RiskLevel.red:
            return f"{project.name} 有 {blocked_count} 个受阻任务、{overdue_count} 个逾期任务。今天先处理风险最高的一项。"
        if risk_level == RiskLevel.orange:
            return f"{project.name} 有 {next_due_count} 个任务即将到期。现在适合做一次交付物检查。"
        return f"{project.name} 有 {active_count} 条轻量提醒。我们保持这个节奏，不让任务堆起来。"

    def _to_reminder(self, record: TaskReminderRecord, task: Task) -> TaskReminder:
        return TaskReminder(
            id=record.id,
            project_id=record.project_id,
            task_id=record.task_id,
            task_title=task.title,
            reminder_type=ReminderType(record.reminder_type),
            severity=RiskLevel(record.severity),
            status=ReminderStatus(record.status),
            trigger_date=record.trigger_date,
            due_date=task.due_date,
            message=record.message,
            suggested_action=record.suggested_action,
            created_at=record.created_at,
            updated_at=record.updated_at,
            dismissed_at=record.dismissed_at,
        )


reminder_repository = ReminderRepository()
