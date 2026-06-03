from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.user import User
from backend.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_tg_id(self, tg_id: int) -> User | None:
        result = await self._session.execute(
            select(User)
            .where(User.tg_id == tg_id)
            .options(selectinload(User.subscription))
        )
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        tg_id: int,
        first_name: str,
        username: str | None = None,
        language_code: str | None = None,
    ) -> tuple[User, bool]:
        """Повертає (user, is_created)."""
        user = await self.get_by_tg_id(tg_id)
        if user:
            return user, False
        user = await self.create(
            tg_id=tg_id,
            first_name=first_name,
            username=username,
            language_code=language_code,
        )
        return user, True

    async def get_active_users_count(self) -> int:
        from sqlalchemy import func, select
        from backend.models.message import Message
        from datetime import datetime, timedelta, timezone
        since = datetime.now(timezone.utc) - timedelta(days=30)
        result = await self._session.execute(
            select(func.count(func.distinct(Message.user_id)))
            .where(Message.created_at >= since)
        )
        return result.scalar_one()

    async def block_user(self, tg_id: int) -> bool:
        user = await self.get_by_tg_id(tg_id)
        if not user:
            return False
        user.is_blocked = True
        return True
