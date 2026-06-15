from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models import PhaseRecord, ProjectRecord, TaskRecord
from app.db.session import SessionLocal
from app.projects.models import (
    DashboardSummary,
    ItemStatus,
    MilestoneSummary,
    Phase,
    Project,
    RiskLevel,
    Task,
)


class ProjectRepository:
    def refresh_all_project_states(self) -> None:
        with SessionLocal() as session:
            records = session.scalars(
                select(ProjectRecord).options(selectinload(ProjectRecord.tasks))
            ).all()
            for record in records:
                self._refresh_project_state(record)
            session.commit()

    def list_projects(self) -> list[Project]:
        with SessionLocal() as session:
            records = session.scalars(
                select(ProjectRecord)
                .options(
                    selectinload(ProjectRecord.phases),
                    selectinload(ProjectRecord.tasks),
                )
                .order_by(ProjectRecord.id)
            ).all()
            return [self._to_project(record) for record in records]

    def get_project(self, project_id: str) -> Project | None:
        with SessionLocal() as session:
            record = self._get_project_record(session, project_id)
            if record is None:
                return None
            return self._to_project(record)

    def update_task_status(
        self,
        project_id: str,
        task_id: str,
        status: ItemStatus,
    ) -> Project | None:
        with SessionLocal() as session:
            record = self._get_project_record(session, project_id)
            if record is None:
                return None

            task = next((item for item in record.tasks if item.id == task_id), None)
            if task is None:
                return None

            task.status = status.value
            self._refresh_project_state(record)
            session.commit()
            return self._to_project(record)

    def replace_project_plan(
        self,
        project_id: str,
        phases: list[Phase],
        tasks: list[Task],
        current_phase: str,
    ) -> Project | None:
        with SessionLocal() as session:
            record = self._get_project_record(session, project_id)
            if record is None:
                return None

            for phase in list(record.phases):
                session.delete(phase)
            for task in list(record.tasks):
                session.delete(task)
            session.flush()

            record.phases = [
                PhaseRecord(
                    id=phase.id,
                    project_id=project_id,
                    title=phase.title,
                    status=phase.status.value,
                    start_date=phase.start_date,
                    end_date=phase.end_date,
                    deliverables="\n".join(phase.deliverables),
                )
                for phase in phases
            ]
            record.tasks = [
                TaskRecord(
                    id=task.id,
                    project_id=project_id,
                    title=task.title,
                    due_date=task.due_date,
                    status=task.status.value,
                    owner_agent_id=task.owner_agent_id,
                    deliverable=task.deliverable,
                )
                for task in tasks
            ]
            record.current_phase = current_phase

            self._refresh_project_state(record)
            session.commit()
            return self._to_project(record)

    def get_dashboard_summary(self) -> DashboardSummary:
        projects = self.list_projects()
        if not projects:
            return DashboardSummary(
                overall_completion_percent=0,
                active_project_count=0,
                risk_level=RiskLevel.green,
                next_milestones=[],
                encouragement="今天可以从确定第一个课题开始。",
                manager_name="Rhea Chen",
                manager_role="全流程实施监控员",
                manager_message="当前没有活跃项目。我会在你创建项目后开始监控实施节奏。",
            )

        average_progress = round(sum(project.progress_percent for project in projects) / len(projects))
        dashboard_risk = self._combine_risk([project.risk_level for project in projects])
        milestones = [
            MilestoneSummary(
                project_id=project.id,
                project_name=project.name,
                milestone=project.next_milestone,
                due_date=project.next_due_date,
                risk_level=project.risk_level,
            )
            for project in sorted(projects, key=lambda item: item.next_due_date)
        ]

        return DashboardSummary(
            overall_completion_percent=average_progress,
            active_project_count=len(projects),
            risk_level=dashboard_risk,
            next_milestones=milestones,
            encouragement="你的论文工场已经启动。我们把复杂工作拆成小步，今天只推进下一件关键事。",
            manager_name="Rhea Chen",
            manager_role="全流程实施监控员",
            manager_message=self._build_manager_message(projects, dashboard_risk),
        )

    def _build_manager_message(self, projects: list[Project], risk: RiskLevel) -> str:
        blocked_count = sum(
            1
            for project in projects
            for task in project.tasks
            if task.status == ItemStatus.blocked
        )
        overdue_count = sum(
            1
            for project in projects
            for task in project.tasks
            if task.status != ItemStatus.done and task.due_date < date.today()
        )

        if risk == RiskLevel.red:
            return f"我正在监控 {len(projects)} 个项目。当前有 {blocked_count} 个受阻任务，需要优先排除障碍。"
        if risk == RiskLevel.orange:
            return f"我正在监控 {len(projects)} 个项目。当前有 {overdue_count} 个逾期任务，需要重新确认截止日期。"
        return f"我正在监控 {len(projects)} 个项目。当前节奏正常，请优先推进最近一个里程碑。"

    def _get_project_record(self, session, project_id: str) -> ProjectRecord | None:
        return session.scalar(
            select(ProjectRecord)
            .options(
                selectinload(ProjectRecord.phases),
                selectinload(ProjectRecord.tasks),
            )
            .where(ProjectRecord.id == project_id)
        )

    def _combine_risk(self, risks: list[RiskLevel]) -> RiskLevel:
        if RiskLevel.red in risks:
            return RiskLevel.red
        if RiskLevel.orange in risks:
            return RiskLevel.orange
        return RiskLevel.green

    def _refresh_project_state(self, project: ProjectRecord) -> None:
        today = date.today()
        incomplete_tasks = [task for task in project.tasks if task.status != ItemStatus.done.value]

        project.progress_percent = self._calculate_progress(project.tasks)
        project.risk_level = self._calculate_risk(project.tasks, today).value

        if incomplete_tasks:
            next_task = sorted(incomplete_tasks, key=lambda task: task.due_date)[0]
            project.next_milestone = next_task.deliverable
            project.next_due_date = next_task.due_date
        elif project.tasks:
            latest_task = sorted(project.tasks, key=lambda task: task.due_date)[-1]
            project.next_milestone = "所有当前任务已完成，可以进入下一阶段复盘"
            project.next_due_date = latest_task.due_date

        project.stage_days_remaining = max((project.next_due_date - today).days, 0)

    def _calculate_progress(self, tasks: list[TaskRecord]) -> int:
        if not tasks:
            return 0

        status_weights = {
            ItemStatus.not_started.value: 0.0,
            ItemStatus.in_progress.value: 0.5,
            ItemStatus.blocked.value: 0.25,
            ItemStatus.done.value: 1.0,
        }
        total = sum(status_weights[task.status] for task in tasks)
        return round(total / len(tasks) * 100)

    def _calculate_risk(self, tasks: list[TaskRecord], today: date) -> RiskLevel:
        if any(task.status == ItemStatus.blocked.value for task in tasks):
            return RiskLevel.red

        has_overdue_task = any(
            task.status != ItemStatus.done.value and task.due_date < today
            for task in tasks
        )
        if has_overdue_task:
            return RiskLevel.orange

        return RiskLevel.green

    def _to_project(self, record: ProjectRecord) -> Project:
        return Project(
            id=record.id,
            name=record.name,
            title=record.title,
            topic=record.topic,
            current_phase=record.current_phase,
            progress_percent=record.progress_percent,
            risk_level=RiskLevel(record.risk_level),
            stage_days_remaining=record.stage_days_remaining,
            next_milestone=record.next_milestone,
            next_due_date=record.next_due_date,
            phases=[self._to_phase(phase) for phase in record.phases],
            tasks=[self._to_task(task) for task in record.tasks],
        )

    def _to_phase(self, record: PhaseRecord) -> Phase:
        deliverables = [item for item in record.deliverables.splitlines() if item]
        return Phase(
            id=record.id,
            title=record.title,
            status=ItemStatus(record.status),
            start_date=record.start_date,
            end_date=record.end_date,
            deliverables=deliverables,
        )

    def _to_task(self, record: TaskRecord) -> Task:
        return Task(
            id=record.id,
            title=record.title,
            due_date=record.due_date,
            status=ItemStatus(record.status),
            owner_agent_id=record.owner_agent_id,
            deliverable=record.deliverable,
        )


project_repository = ProjectRepository()
