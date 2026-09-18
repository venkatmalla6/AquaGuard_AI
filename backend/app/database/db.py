"""
AquaGuard AI - Database Setup
Uses SQLModel (SQLAlchemy + Pydantic) with async support.

WHY SQLModel: It combines SQLAlchemy's ORM power with Pydantic's validation,
reducing boilerplate and keeping models as the single source of truth
for both database and API schemas.

WHY async: FastAPI is async-native. Using async database connections 
prevents blocking the event loop during I/O operations.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlmodel import SQLModel
from loguru import logger

from app.core.config import settings


# Create async engine
# WHY: We use SQLite for development (no installation needed) and
# can switch to PostgreSQL for production via DATABASE_URL env var
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    # SQLite-specific args (ignored by PostgreSQL)
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def create_db_and_tables() -> None:
    """
    Create all database tables on startup.
    In production, use Alembic migrations instead.
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("Database tables created/verified successfully.")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a database session per request.
    
    WHY dependency injection: Ensures sessions are properly opened/closed
    and prevents connection leaks even if a request fails.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
