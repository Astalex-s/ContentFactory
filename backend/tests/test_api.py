"""Integration tests for API endpoints."""

import io

import pytest
from httpx import AsyncClient


CSV_VALID = b"""name,description,category,price,marketplace_url
Product One,Desc One,Cat A,100,https://example.com/1
Product Two,Desc Two,Cat B,500,https://example.com/2
Product Three,Desc Three,Cat A,900,https://example.com/3
"""

CSV_INVALID = b"""name,price
Bad,100
"""


@pytest.mark.asyncio
async def test_post_products_import_success(async_client: AsyncClient):
    """POST /products/import — successful import."""
    response = await async_client.post(
        "/products/import",
        files={"file": ("products.csv", io.BytesIO(CSV_VALID), "text/csv")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["imported"] == 3
    assert data["skipped"] == 0
    assert data["total_rows"] == 3
    assert len(data["errors"]) == 0


@pytest.mark.asyncio
async def test_post_products_import_duplicates(async_client: AsyncClient):
    """POST /products/import — duplicates skipped."""
    await async_client.post(
        "/products/import",
        files={"file": ("products.csv", io.BytesIO(CSV_VALID), "text/csv")},
    )
    response = await async_client.post(
        "/products/import",
        files={"file": ("products.csv", io.BytesIO(CSV_VALID), "text/csv")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["imported"] == 0
    assert data["skipped"] == 3


@pytest.mark.asyncio
async def test_post_products_import_invalid_csv(async_client: AsyncClient):
    """POST /products/import — invalid CSV returns errors."""
    response = await async_client.post(
        "/products/import",
        files={"file": ("bad.csv", io.BytesIO(CSV_INVALID), "text/csv")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["imported"] == 0
    assert len(data["errors"]) > 0


@pytest.mark.asyncio
async def test_get_products_filtering(async_client: AsyncClient):
    """GET /products — filtering by category."""
    await async_client.post(
        "/products/import",
        files={"file": ("products.csv", io.BytesIO(CSV_VALID), "text/csv")},
    )

    response = await async_client.get("/products", params={"category": "Cat A"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(item["category"] == "Cat A" for item in data["items"])


@pytest.mark.asyncio
async def test_get_products_pagination(async_client: AsyncClient):
    """GET /products — pagination."""
    await async_client.post(
        "/products/import",
        files={"file": ("products.csv", io.BytesIO(CSV_VALID), "text/csv")},
    )

    response = await async_client.get("/products", params={"page": 1, "page_size": 2})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2


@pytest.mark.asyncio
async def test_get_products_sort_by_price(async_client: AsyncClient):
    """GET /products — sort by price."""
    await async_client.post(
        "/products/import",
        files={"file": ("products.csv", io.BytesIO(CSV_VALID), "text/csv")},
    )

    response = await async_client.get("/products", params={"sort_by": "price"})
    assert response.status_code == 200
    data = response.json()
    prices = [item["price"] for item in data["items"]]
    assert prices == sorted(prices)


@pytest.mark.asyncio
async def test_get_product_by_id(async_client: AsyncClient):
    """GET /products/{id} — get single product."""
    await async_client.post(
        "/products/import",
        files={"file": ("products.csv", io.BytesIO(CSV_VALID), "text/csv")},
    )
    list_resp = await async_client.get("/products", params={"page_size": 1})
    product_id = list_resp.json()["items"][0]["id"]

    response = await async_client.get(f"/products/{product_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == product_id
    assert "name" in data


@pytest.mark.asyncio
async def test_get_product_not_found(async_client: AsyncClient):
    """GET /products/{id} — 404 for non-existent."""
    response = await async_client.get(
        "/products/00000000-0000-0000-0000-000000000000"
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_product(async_client: AsyncClient):
    """DELETE /products/{id} — delete single product."""
    await async_client.post(
        "/products/import",
        files={"file": ("products.csv", io.BytesIO(CSV_VALID), "text/csv")},
    )
    list_resp = await async_client.get("/products", params={"page_size": 1})
    product_id = list_resp.json()["items"][0]["id"]

    response = await async_client.delete(f"/products/{product_id}")
    assert response.status_code == 204

    get_resp = await async_client.get(f"/products/{product_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_product_not_found(async_client: AsyncClient):
    """DELETE /products/{id} — 404 for non-existent."""
    response = await async_client.delete(
        "/products/00000000-0000-0000-0000-000000000000"
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_all_products(async_client: AsyncClient):
    """DELETE /products/all — delete all products."""
    await async_client.post(
        "/products/import",
        files={"file": ("products.csv", io.BytesIO(CSV_VALID), "text/csv")},
    )
    response = await async_client.delete("/products/all")
    assert response.status_code == 200
    data = response.json()
    assert data["deleted"] == 3

    list_resp = await async_client.get("/products")
    assert list_resp.json()["total"] == 0
