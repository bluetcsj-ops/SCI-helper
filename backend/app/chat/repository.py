from app.db.models import ChatMessageRecord
from app.db.session import SessionLocal


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


chat_repository = ChatRepository()
