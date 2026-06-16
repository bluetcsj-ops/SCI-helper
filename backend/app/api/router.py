from fastapi import APIRouter

from app.api.routes import agents, chat, dashboard, data, health, mentor, projects, reminders, users


api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(agents.router, prefix="/api/agents", tags=["agents"])
api_router.include_router(mentor.router, prefix="/api/mentor", tags=["mentor"])
api_router.include_router(users.router, prefix="/api/users", tags=["users"])
api_router.include_router(projects.router, prefix="/api/projects", tags=["projects"])
api_router.include_router(data.router, prefix="/api/projects", tags=["data"])
api_router.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
api_router.include_router(chat.router, prefix="/api/chat", tags=["chat"])
api_router.include_router(reminders.router, tags=["reminders"])
