from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.subscription import Subscription
from backend.repositories.base import BaseRepository

TIER_CONFIG = {
    "free":    {"requests_limit": 10,  "days": None},
    "basic":   {"requests_limit": 50,  "days": 30},
    "premium": {"requests_limit": -1,  "days": 30},
}


class SubscriptionRepository(BaseRepository[Subscription]):
    model = Subscription

    async def get_by_user_id(self, user_id: int) -> Subscription | None:
        result = await self._session.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_or_upgrade(self, user_id: int, tier: str) -> Subscription:
        config = TIER_CONFIG.get(tier, TIER_CONFIG["free"])
        expires_at = None
        if config["days"]:
            expires_at = datetime.now(timezone.utc) + timedelta(days=config["days"])

        sub = await self.get_by_user_id(user_id)
        if sub:
            sub.tier = tier
            sub.requests_limit = config["requests_limit"]
            sub.requests_used = 0
            sub.expires_at = expires_at
            return sub

        return await self.create(
            user_id=user_id,
            tier=tier,
            requests_limit=config["requests_limit"],
            expires_at=expires_at,
        )

    async def increment_usage(self, user_id: int) -> None:
        sub = await self.get_by_user_id(user_id)
        if sub and sub.requests_limit != -1:
            sub.requests_used += 1
