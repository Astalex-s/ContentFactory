"""Pytest configuration and fixtures. Test database is separate from production."""

import os

# When running tests, pass DATABASE_URL or TEST_DATABASE_URL pointing to contentfactory_test
# e.g. -e DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/contentfactory_test

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import create_app
from app.repositories.product import ProductRepository
from app.services.product import ProductService
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


def _get_test_database_url() -> str:
    """Get test database URL. Prefer TEST_DATABASE_URL to avoid conflicts with app's DATABASE_URL."""
    url = os.environ.get("TEST_DATABASE_URL")
    if url:
        return url
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        pytest.skip("TEST_DATABASE_URL or DATABASE_URL required for tests")
    # If DATABASE_URL points to main DB, derive test DB (avoid doubling: contentfactory_test -> contentfactory_test_test)
    if "contentfactory_test" in url:
        return url
    # Replace only when path ends with /contentfactory (not contentfactory_test)
    if url.rstrip("/").endswith("/contentfactory"):
        return url.rstrip("/")[:-len("/contentfactory")] + "/contentfactory_test"
    return url


@pytest.fixture(scope="session")
def test_db_url() -> str:
    return _get_test_database_url()


@pytest_asyncio.fixture
async def test_engine(test_db_url):
    """Create test engine. Tables are created fresh for each test module."""
    engine = create_async_engine(
        test_db_url,
        echo=False,
        pool_pre_ping=True,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Test session. Data is cleared after each test via fresh tables."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest_asyncio.fixture
async def product_repository(test_session: AsyncSession) -> ProductRepository:
    return ProductRepository(test_session)


@pytest_asyncio.fixture
async def product_service(product_repository: ProductRepository) -> ProductService:
    return ProductService(product_repository)


@pytest_asyncio.fixture
async def app(test_session: AsyncSession) -> FastAPI:
    """FastAPI app with overridden get_db for tests."""

    async def _get_db():
        try:
            yield test_session
            await test_session.commit()
        except Exception:
            await test_session.rollback()
            raise

    fastapi_app = create_app()
    fastapi_app.dependency_overrides[get_db] = _get_db
    return fastapi_app


@pytest_asyncio.fixture
async def async_client(app: FastAPI):
    """Async HTTP client for integration tests."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
