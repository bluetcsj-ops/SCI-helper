from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ProjectAccessRecord, ProjectRecord, UserRecord
from app.db.session import SessionLocal
from app.users.models import ProjectAccessLevel, ProjectAccessPolicy, UserProfile, UserRole


DEFAULT_USER_ID = "user-primary"
ACCESS_WEIGHT = {
    ProjectAccessLevel.viewer: 1,
    ProjectAccessLevel.editor: 2,
    ProjectAccessLevel.owner: 3,
}


class UserRepository:
    def get_user(self, user_id: str) -> UserProfile | None:
        with SessionLocal() as session:
            record = session.scalar(select(UserRecord).where(UserRecord.id == user_id))
            return self._to_user(record) if record is not None else None

    def list_accessible_project_ids(self, user_id: str) -> list[str]:
        with SessionLocal() as session:
            records = session.scalars(
                select(ProjectAccessRecord)
                .where(ProjectAccessRecord.user_id == user_id)
                .order_by(ProjectAccessRecord.project_id)
            ).all()
            return [record.project_id for record in records]

    def get_project_access(
        self,
        user_id: str,
        project_id: str,
    ) -> ProjectAccessPolicy | None:
        with SessionLocal() as session:
            record = session.scalar(
                select(ProjectAccessRecord).where(
                    ProjectAccessRecord.user_id == user_id,
                    ProjectAccessRecord.project_id == project_id,
                )
            )
            return self._to_project_access(record) if record is not None else None

    def has_project_access(
        self,
        user_id: str,
        project_id: str,
        minimum_access: ProjectAccessLevel,
    ) -> bool:
        policy = self.get_project_access(user_id=user_id, project_id=project_id)
        if policy is None:
            return False
        return ACCESS_WEIGHT[policy.access_level] >= ACCESS_WEIGHT[minimum_access]

    def seed_default_users_and_access(self, session: Session) -> None:
        self._ensure_user(
            session=session,
            user_id=DEFAULT_USER_ID,
            display_name="Dr. Chen",
            email="chen.sci@example.local",
            role=UserRole.researcher,
        )
        session.flush()

        project_ids = session.scalars(select(ProjectRecord.id).order_by(ProjectRecord.id)).all()
        for project_id in project_ids:
            self._ensure_access(
                session=session,
                user_id=DEFAULT_USER_ID,
                project_id=project_id,
                access_level=ProjectAccessLevel.owner,
            )

    def _ensure_user(
        self,
        session: Session,
        user_id: str,
        display_name: str,
        email: str,
        role: UserRole,
    ) -> None:
        existing = session.scalar(select(UserRecord).where(UserRecord.id == user_id))
        if existing is not None:
            existing.email = self._normalize_email(existing.email or email)
            existing.role = existing.role or role.value
            return
        session.add(
            UserRecord(
                id=user_id,
                display_name=display_name,
                email=self._normalize_email(email),
                role=role.value,
            )
        )

    def _ensure_access(
        self,
        session: Session,
        user_id: str,
        project_id: str,
        access_level: ProjectAccessLevel,
    ) -> None:
        existing = session.scalar(
            select(ProjectAccessRecord).where(
                ProjectAccessRecord.user_id == user_id,
                ProjectAccessRecord.project_id == project_id,
            )
        )
        if existing is not None:
            return
        session.add(
            ProjectAccessRecord(
                user_id=user_id,
                project_id=project_id,
                access_level=access_level.value,
            )
        )

    def _to_user(self, record: UserRecord) -> UserProfile:
        return UserProfile(
            id=record.id,
            display_name=record.display_name,
            email=record.email,
            role=UserRole(record.role),
        )

    def _to_project_access(self, record: ProjectAccessRecord) -> ProjectAccessPolicy:
        access_level = ProjectAccessLevel(record.access_level)
        return ProjectAccessPolicy(
            project_id=record.project_id,
            user_id=record.user_id,
            access_level=access_level,
            can_view=ACCESS_WEIGHT[access_level] >= ACCESS_WEIGHT[ProjectAccessLevel.viewer],
            can_edit=ACCESS_WEIGHT[access_level] >= ACCESS_WEIGHT[ProjectAccessLevel.editor],
            can_manage_data=ACCESS_WEIGHT[access_level] >= ACCESS_WEIGHT[ProjectAccessLevel.editor],
            can_manage_access=access_level == ProjectAccessLevel.owner,
        )

    def _normalize_email(self, email: str) -> str:
        return email.strip().lower()


user_repository = UserRepository()
