"""ProductService unit tests."""

import io

import pytest

from app.models.product import Product
from app.repositories.product import ProductRepository
from app.services.product import (
    PRIORITY_HIGH,
    PRIORITY_LOW,
    PRIORITY_MEDIUM,
    ProductService,
)


@pytest.fixture
def service_with_mock_repo():
    """ProductService with mocked repository for calculate_popularity_score (no DB)."""

    class MockRepo:
        async def check_duplicate(self, url):
            return False

        async def bulk_create(self, products):
            pass

    return ProductService(repository=MockRepo())


def test_calculate_popularity_score_high(service_with_mock_repo):
    """price < 500 → high (1.0)."""
    svc = service_with_mock_repo
    assert svc.calculate_popularity_score(100) == PRIORITY_HIGH
    assert svc.calculate_popularity_score(499) == PRIORITY_HIGH


def test_calculate_popularity_score_medium(service_with_mock_repo):
    """500 <= price <= 800 → medium (0.5)."""
    svc = service_with_mock_repo
    assert svc.calculate_popularity_score(500) == PRIORITY_MEDIUM
    assert svc.calculate_popularity_score(800) == PRIORITY_MEDIUM


def test_calculate_popularity_score_low(service_with_mock_repo):
    """price > 800 → low (0.2)."""
    svc = service_with_mock_repo
    assert svc.calculate_popularity_score(801) == PRIORITY_LOW
    assert svc.calculate_popularity_score(1000) == PRIORITY_LOW


def test_calculate_popularity_score_zero(service_with_mock_repo):
    """price <= 0 → 0.0."""
    svc = service_with_mock_repo
    assert svc.calculate_popularity_score(0) == 0.0
    assert svc.calculate_popularity_score(-1) == 0.0


@pytest.mark.asyncio
async def test_import_from_csv_success(product_service):
    """Successful CSV import."""
    csv_content = """name,description,category,price,marketplace_url
Product A,Desc A,Cat A,100,https://example.com/1
Product B,Desc B,Cat B,600,https://example.com/2
"""
    result = await product_service.import_from_csv(io.BytesIO(csv_content.encode("utf-8")))
    assert result["imported"] == 2
    assert result["skipped"] == 0
    assert result["total_rows"] == 2
    assert len(result["errors"]) == 0


@pytest.mark.asyncio
async def test_import_from_csv_duplicates(product_service):
    """Duplicates are skipped."""
    csv_content = """name,description,category,price,marketplace_url
Product A,Desc,Cat,100,https://example.com/same
Product B,Desc,Cat,200,https://example.com/same
"""
    result = await product_service.import_from_csv(io.BytesIO(csv_content.encode("utf-8")))
    assert result["imported"] == 1
    assert result["skipped"] == 1
    assert result["total_rows"] == 2


@pytest.mark.asyncio
async def test_import_from_csv_invalid_price(product_service):
    """Invalid price in CSV."""
    csv_content = """name,description,category,price,marketplace_url
Product A,Desc,Cat,invalid,https://example.com/1
"""
    result = await product_service.import_from_csv(io.BytesIO(csv_content.encode("utf-8")))
    assert result["imported"] == 0
    assert result["skipped"] == 1
    assert "invalid price" in result["errors"][0].lower()


@pytest.mark.asyncio
async def test_import_from_csv_missing_columns(product_service):
    """Missing required columns."""
    csv_content = """name,price
Product,100
"""
    result = await product_service.import_from_csv(io.BytesIO(csv_content.encode("utf-8")))
    assert result["imported"] == 0
    assert result["skipped"] == 0
    assert "missing columns" in result["errors"][0].lower()


@pytest.mark.asyncio
async def test_import_from_csv_empty_file(product_service):
    """Empty file."""
    result = await product_service.import_from_csv(io.BytesIO(b""))
    assert result["imported"] == 0
    assert result["skipped"] == 0
    assert "empty" in result["errors"][0].lower()
