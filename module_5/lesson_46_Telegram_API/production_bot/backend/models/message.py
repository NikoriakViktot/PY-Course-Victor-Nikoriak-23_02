from datetime import datetime
from sqlalchemy import ForeignKey, String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base


class Message(Base):
    """Лог повідомлень для аналітики та аудиту."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    # 'text' | 'photo' | 'voice' | 'command'
    content_type: Mapped[str] = mapped_column(String(32))
    text: Mapped[str | None] = mapped_column(Text)
    command: Mapped[str | None] = mapped_column(String(64))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    user: Mapped["User"] = relationship(back_populates="messages")
