"""ProductRepository tests."""

import uuid

import pytest

from app.models.product import Product
from app.repositories.product import ProductRepository


@pytest.mark.asyncio
async def test_create_and_get_by_id(product_repository):
    """Create product and get by ID."""
    product = Product(
        name="Test Product",
        description="Desc",
        category="Cat",
        price=100.0,
        popularity_score=1.0,
        marketplace_url="https://example.com/1",
    )
    created = await product_repository.create(product)
    assert created.id is not None

    found = await product_repository.get_by_id(created.id)
    assert found is not None
    assert found.name == "Test Product"
    assert found.price == 100.0


@pytest.mark.asyncio
async def test_get_by_id_not_found(product_repository):
    """Get non-existent product returns None."""
    found = await product_repository.get_by_id(uuid.uuid4())
    assert found is None


@pytest.mark.asyncio
async def test_check_duplicate(product_repository):
    """check_duplicate returns True for existing URL."""
    product = Product(
        name="Test",
        description=None,
        category=None,
        price=50.0,
        popularity_score=1.0,
        marketplace_url="https://example.com/unique",
    )
    await product_repository.create(product)

    assert await product_repository.check_duplicate("https://example.com/unique") is True
    assert await product_repository.check_duplicate("https://example.com/other") is False


@pytest.mark.asyncio
async def test_get_all_with_filters(product_repository):
    """get_all filters by category and price."""
    products = [
        Product(name="A", category="X", price=100.0, popularity_score=1.0),
        Product(name="B", category="X", price=200.0, popularity_score=1.0),
        Product(name="C", category="Y", price=150.0, popularity_score=1.0),
    ]
    await product_repository.bulk_create(products)

    items, total = await product_repository.get_all(category="X")
    assert total == 2
    assert len(items) == 2

    items, total = await product_repository.get_all(min_price=150)
    assert total == 2

    items, total = await product_repository.get_all(max_price=150)
    assert total == 2


@pytest.mark.asyncio
async def test_get_all_pagination(product_repository):
    """get_all paginates correctly."""
    products = [
        Product(name=f"Product {i}", price=100.0 + i, popularity_score=1.0)
        for i in range(5)
    ]
    await product_repository.bulk_create(products)

    items, total = await product_repository.get_all(page=1, page_size=2)
    assert total == 5
    assert len(items) == 2

    items, total = await product_repository.get_all(page=2, page_size=2)
    assert len(items) == 2
