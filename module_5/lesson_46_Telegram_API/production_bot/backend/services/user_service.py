"""
User Service — бізнес-логіка роботи з користувачами.

Service ізолює Handler від Repository.
Handler → Service → Repository → DB
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.user import User
from backend.repositories.user_repo import UserRepository
from backend.repositories.subscription_repo import SubscriptionRepository

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self._users = UserRepository(session)
        self._subs = SubscriptionRepository(session)

    async def register_or_get(
        self,
        tg_id: int,
        first_name: str,
        username: str | None = None,
        language_code: str | None = None,
        referrer_tg_id: int | None = None,
    ) -> tuple[User, bool]:
        user, is_new = await self._users.get_or_create(
            tg_id=tg_id,
            first_name=first_name,
            username=username,
            language_code=language_code,
        )

        if is_new:
            # Безкоштовна підписка при реєстрації
            await self._subs.create_or_upgrade(user.id, "free")
            logger.info("Новий user: tg_id=%s username=%s", tg_id, username)

            # Реферальний бонус
            if referrer_tg_id and referrer_tg_id != tg_id:
                referrer = await self._users.get_by_tg_id(referrer_tg_id)
                if referrer:
                    await self._process_referral(referrer.id, user.id)

        return user, is_new

    async def _process_referral(self, referrer_id: int, referred_id: int) -> None:
        from backend.models.referral import Referral
        from backend.repositories.base import BaseRepository

        logger.info("Реферал: referrer_id=%s → referred_id=%s", referrer_id, referred_id)

    async def is_blocked(self, tg_id: int) -> bool:
        user = await self._users.get_by_tg_id(tg_id)
        return user.is_blocked if user else False

    async def get_stats(self) -> dict:
        total = await self._users.count()
        active = await self._users.get_active_users_count()
        return {"total_users": total, "active_30d": active}
