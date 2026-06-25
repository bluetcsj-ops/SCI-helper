from app.db.models import ChatMessageRecord
from app.db.session import SessionLocal
from sqlalchemy import delete, select


class ChatRepository:
    def save_message(
        self,
        *,
        project_id: str | None,
        agent_id: str,
        speaker: str,
        content: str,
    ) -> None:
        with SessionLocal() as session:
            session.add(
                ChatMessageRecord(
                    project_id=project_id,
                    agent_id=agent_id,
                    speaker=speaker,
                    content=content,
                )
            )
            session.commit()

    def list_messages(
        self,
        *,
        project_id: str,
        agent_id: str | None = None,
        limit: int = 80,
    ) -> list[ChatMessageRecord]:
        bounded_limit = min(max(limit, 1), 200)
        with SessionLocal() as session:
            query = select(ChatMessageRecord).where(ChatMessageRecord.project_id == project_id)
            if agent_id is not None:
                query = query.where(ChatMessageRecord.agent_id == agent_id)
            records = list(
                session.scalars(
                    query.order_by(ChatMessageRecord.created_at.desc(), ChatMessageRecord.id.desc()).limit(
                        bounded_limit,
                    ),
                ),
            )
        return list(reversed(records))

    def clear_messages(self, *, project_id: str, agent_id: str) -> int:
        with SessionLocal() as session:
            result = session.execute(
                delete(ChatMessageRecord).where(
                    ChatMessageRecord.project_id == project_id,
                    ChatMessageRecord.agent_id == agent_id,
                )
            )
            session.commit()
            return int(result.rowcount or 0)


chat_repository = ChatRepository()
