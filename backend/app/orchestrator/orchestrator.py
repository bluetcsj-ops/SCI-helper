from app.agents.registry import agent_registry
from app.agents.service import agent_service
from app.chat.repository import chat_repository
from app.orchestrator.schemas import ChatRequest, ChatResponse
from app.projects.repository import project_repository


class Orchestrator:
    def handle_chat(self, request: ChatRequest) -> ChatResponse:
        agent = agent_registry.get_agent(request.agent_id)
        if agent is None:
            raise ValueError("Unknown agent")

        project = None
        if request.project_id is not None:
            project = project_repository.get_project(request.project_id)
            if project is None:
                raise ValueError("Unknown project")

        chat_repository.save_message(
            project_id=project.id if project is not None else None,
            agent_id=agent.id.value,
            speaker="user",
            content=request.message,
        )

        agent_reply = agent_service.create_reply(
            agent=agent,
            message=request.message,
            project=project,
        )

        chat_repository.save_message(
            project_id=project.id if project is not None else None,
            agent_id=agent.id.value,
            speaker="agent",
            content=agent_reply.reply,
        )

        return ChatResponse(
            agent_id=agent.id,
            agent_name=agent.name,
            project_id=project.id if project is not None else None,
            reply=agent_reply.reply,
            suggested_next_actions=agent_reply.suggested_next_actions,
            response_source=agent_reply.response_source,
            fallback_reason=agent_reply.fallback_reason,
        )


orchestrator = Orchestrator()
