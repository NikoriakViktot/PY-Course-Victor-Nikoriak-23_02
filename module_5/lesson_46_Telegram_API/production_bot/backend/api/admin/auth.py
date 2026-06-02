from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.core.config import settings
from backend.core.security import create_access_token, verify_password, hash_password

router = APIRouter(prefix="/admin/auth", tags=["Admin Auth"])

# У production — зберігати хеш у БД або env
_ADMIN_PASSWORD_HASH = hash_password(settings.ADMIN_PASSWORD)


class TokenRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/token", response_model=TokenResponse)
async def login(body: TokenRequest) -> TokenResponse:
    if body.username != settings.ADMIN_USERNAME:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(body.password, _ADMIN_PASSWORD_HASH):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": body.username, "role": "admin"})
    return TokenResponse(access_token=token)
