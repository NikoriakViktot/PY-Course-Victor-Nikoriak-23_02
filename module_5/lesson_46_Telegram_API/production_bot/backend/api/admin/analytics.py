from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_session, get_current_admin
from backend.services.user_service import UserService
from backend.repositories.subscription_repo import SubscriptionRepository

router = APIRouter(prefix="/admin/analytics", tags=["Admin Analytics"])


@router.get("/overview")
async def get_overview(
    session: AsyncSession = Depends(get_session),
    _admin: dict = Depends(get_current_admin),
) -> dict:
    user_service = UserService(session)
    stats = await user_service.get_stats()

    sub_repo = SubscriptionRepository(session)
    total_subs = await sub_repo.count()

    return {
        **stats,
        "total_subscriptions": total_subs,
    }
