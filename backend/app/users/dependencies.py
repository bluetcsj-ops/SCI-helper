from typing import Annotated

from fastapi import Header, HTTPException

from app.users.models import ProjectAccessLevel, ProjectAccessPolicy, UserProfile
from app.users.repository import DEFAULT_USER_ID, user_repository


def get_current_user(
    x_sci_user_id: Annotated[str | None, Header(alias="X-SCI-User-Id")] = None,
) -> UserProfile:
    user_id = (x_sci_user_id or DEFAULT_USER_ID).strip()
    user = user_repository.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Unknown user")
    return user


def ensure_project_access(
    project_id: str,
    user: UserProfile,
    minimum_access: ProjectAccessLevel = ProjectAccessLevel.viewer,
) -> ProjectAccessPolicy:
    access = user_repository.get_project_access(user_id=user.id, project_id=project_id)
    if access is None:
        raise HTTPException(status_code=403, detail="Project access denied")
    if not user_repository.has_project_access(
        user_id=user.id,
        project_id=project_id,
        minimum_access=minimum_access,
    ):
        raise HTTPException(status_code=403, detail="Insufficient project permission")
    return access
