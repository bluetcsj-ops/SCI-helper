from fastapi import APIRouter, HTTPException

from app.orchestrator.orchestrator import orchestrator
from app.orchestrator.schemas import ChatRequest, ChatResponse


router = APIRouter()


@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        return orchestrator.handle_chat(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
