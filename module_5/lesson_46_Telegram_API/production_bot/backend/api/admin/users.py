from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_session, get_current_admin
from backend.repositories.user_repo import UserRepository
from backend.repositories.subscription_repo import SubscriptionRepository
from backend.models.audit_log import AuditLog

router = APIRouter(prefix="/admin/users", tags=["Admin Users"])


class UserOut(BaseModel):
    id: int
    tg_id: int
    username: str | None
    first_name: str
    is_blocked: bool
    is_admin: bool

    class Config:
        from_attributes = True


class BlockRequest(BaseModel):
    tg_id: int
    reason: str | None = None


@router.get("/", response_model=list[UserOut])
async def list_users(
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
    _admin: dict = Depends(get_current_admin),
) -> list[UserOut]:
    repo = UserRepository(session)
    users = await repo.get_all(limit=limit, offset=offset)
    return [UserOut.model_validate(u) for u in users]


@router.post("/block")
async def block_user(
    body: BlockRequest,
    session: AsyncSession = Depends(get_session),
    admin: dict = Depends(get_current_admin),
) -> dict:
    repo = UserRepository(session)
    success = await repo.block_user(body.tg_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    # Логуємо дію адміна
    log = AuditLog(
        admin_username=admin["sub"],
        action="block_user",
        target_user_id=body.tg_id,
        details=body.reason,
    )
    session.add(log)
    return {"ok": True, "tg_id": body.tg_id}


@router.post("/subscription")
async def grant_subscription(
    tg_id: int,
    tier: str,
    session: AsyncSession = Depends(get_session),
    admin: dict = Depends(get_current_admin),
) -> dict:
    user_repo = UserRepository(session)
    sub_repo = SubscriptionRepository(session)

    user = await user_repo.get_by_tg_id(tg_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await sub_repo.create_or_upgrade(user.id, tier)

    log = AuditLog(
        admin_username=admin["sub"],
        action="grant_subscription",
        target_user_id=tg_id,
        details=f"tier={tier}",
    )
    session.add(log)
    return {"ok": True, "tg_id": tg_id, "tier": tier}
