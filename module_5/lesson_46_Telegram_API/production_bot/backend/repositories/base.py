"""
Generic Repository — базовий CRUD для будь-якої моделі.

Патерн Repository ізолює Handler від SQL.
Handler не знає про SQLAlchemy — він викликає repo.get_by_id(), repo.create().
Замінити PostgreSQL на MongoDB → лише репозиторій, Handler не змінюється.
"""
from typing import Any, Generic, TypeVar
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, obj_id: int) -> ModelT | None:
        return await self._session.get(self.model, obj_id)

    async def get_all(self, limit: int = 100, offset: int = 0) -> list[ModelT]:
        result = await self._session.execute(
            select(self.model).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> ModelT:
        obj = self.model(**kwargs)
        self._session.add(obj)
        await self._session.flush()  # отримуємо id без commit
        return obj

    async def delete(self, obj: ModelT) -> None:
        await self._session.delete(obj)
        await self._session.flush()

    async def count(self) -> int:
        from sqlalchemy import func, select
        result = await self._session.execute(select(func.count()).select_from(self.model))
        return result.scalar_one()
