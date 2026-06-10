from datetime import datetime
from sqlalchemy import ForeignKey, String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    # 'stars' | 'stripe' | 'manual'
    provider: Mapped[str] = mapped_column(String(32))
    amount: Mapped[int] = mapped_column(Integer)  # у найменших одиницях (Stars або cents)
    currency: Mapped[str] = mapped_column(String(8), default="XTR")  # XTR = Telegram Stars

    # 'pending' | 'completed' | 'refunded' | 'failed'
    status: Mapped[str] = mapped_column(String(16), default="pending")

    telegram_payment_charge_id: Mapped[str | None] = mapped_column(String(256))
    subscription_tier: Mapped[str | None] = mapped_column(String(16))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="payments")
