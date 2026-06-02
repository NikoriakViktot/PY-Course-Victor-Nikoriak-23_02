from datetime import datetime
from sqlalchemy import ForeignKey, String, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)

    # 'free' | 'basic' | 'premium'
    tier: Mapped[str] = mapped_column(String(16), default="free")

    # AI запити: -1 = безліміт
    requests_limit: Mapped[int] = mapped_column(Integer, default=10)
    requests_used: Mapped[int] = mapped_column(Integer, default=0)

    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="subscription")

    @property
    def is_active(self) -> bool:
        if self.expires_at is None:
            return True
        from datetime import timezone
        return self.expires_at > datetime.now(timezone.utc)

    @property
    def has_requests_left(self) -> bool:
        if self.requests_limit == -1:
            return True
        return self.requests_used < self.requests_limit
