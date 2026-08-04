import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine,
)

from app.core.config import AppSettings

logger = logging.getLogger("uvicorn.error")


@dataclass(frozen=True)
class RDB:
    engine: AsyncEngine
    session_maker: async_sessionmaker[AsyncSession]


def build_rdb(settings: AppSettings) -> RDB:
    logger.info("[RDB] build rdb")

    url = f"postgresql+asyncpg://{settings.RDB_USER}:{settings.RDB_PASSWORD}@{settings.RDB_HOST}:{settings.RDB_PORT}/{settings.RDB_DATABASE}"

    engine = create_async_engine(
        url=url,
        echo=True,
        pool_pre_ping=True,
        pool_size=20,
        max_overflow=10,
        pool_timeout=30,
    )

    session_maker = async_sessionmaker(
        bind=engine, expire_on_commit=False, autoflush=False
    )

    return RDB(engine=engine, session_maker=session_maker)
