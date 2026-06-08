from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import get_settings
from app.models.base import Base


settings = get_settings()

connect_args = {}
if "postgresql" in settings.database_url or "asyncpg" in settings.database_url:
    connect_args["prepared_statement_cache_size"] = 0
    connect_args["statement_cache_size"] = 0

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args=connect_args,
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
