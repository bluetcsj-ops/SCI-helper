from enum import StrEnum

from pydantic import BaseModel


class UserRole(StrEnum):
    admin = "admin"
    researcher = "researcher"
    reviewer = "reviewer"


class ProjectAccessLevel(StrEnum):
    viewer = "viewer"
    editor = "editor"
    owner = "owner"


class UserProfile(BaseModel):
    id: str
    display_name: str
    email: str
    role: UserRole


class ProjectAccessPolicy(BaseModel):
    project_id: str
    user_id: str
    access_level: ProjectAccessLevel
    can_view: bool
    can_edit: bool
    can_manage_data: bool
    can_manage_access: bool
