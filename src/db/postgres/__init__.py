import contextlib
from typing import Any, AsyncGenerator, AsyncIterator, Dict

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.declarative import declarative_base

from config import settings


class DatabaseSessionManager:
    def __init__(self, host: str, engine_kwargs: dict[str, Any]):
        self._engine = create_async_engine(host, **engine_kwargs)
        self._sessionmaker = async_sessionmaker(
            autoflush=False, expire_on_commit=True, bind=self._engine
        )

    async def close(self) -> None:
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")
        await self._engine.dispose()
        self._engine = None  # type: ignore
        self._sessionmaker = None  # type: ignore

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")

        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._sessionmaker is None:
            raise Exception("DatabaseSessionManager is not initialized")

        session = self._sessionmaker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


pt_sessionmanager = DatabaseSessionManager(
    host=f"{settings.SQLALCHEMY_DATABASE_URL}/organise",
    engine_kwargs={"echo": settings.SQLALCHEMY_ECHO_SQL},
)


async def get_pt_postgres_session() -> AsyncGenerator[AsyncSession, None]:
    async with pt_sessionmanager.session() as session:
        yield session


sessionmanager = DatabaseSessionManager(
    host=f"{settings.SQLALCHEMY_DATABASE_URL}/organise",
    engine_kwargs={"echo": settings.SQLALCHEMY_ECHO_SQL},
)


async def get_postgres_session() -> AsyncGenerator[AsyncSession, None]:
    async with sessionmanager.session() as session:
        yield session


POSTGRES_NAMING_CONVENTION: Dict[str, str] = {
    "ix": "%(table_name)s_%(column_0_name)s_idx",
    "uq": "%(table_name)s_%(column_0_name)s_key",
    "ck": "%(table_name)s_%(column_0_name)s_check",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_%(column_0_name)s_pkey",
}


# See https://docs.sqlalchemy.org/en/14/orm/declarative_mixins.html#augmenting-the-base
Base = declarative_base()

Base.metadata = MetaData(naming_convention=POSTGRES_NAMING_CONVENTION)
