from fastapi import APIRouter, Depends

from app.users.dependencies import get_current_user
from app.users.models import UserProfile


router = APIRouter()


@router.get("/me", response_model=UserProfile)
def get_me(current_user: UserProfile = Depends(get_current_user)) -> UserProfile:
    return current_user
