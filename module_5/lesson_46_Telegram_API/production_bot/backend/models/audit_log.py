from datetime import datetime
from sqlalchemy import BigInteger, String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.database import Base


class AuditLog(Base):
    """Журнал дій адміністратора через Admin API."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    admin_username: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(128))
    target_user_id: Mapped[int | None] = mapped_column(BigInteger)
    details: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
