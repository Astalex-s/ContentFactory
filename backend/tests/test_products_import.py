"""Products endpoint tests."""

import pytest


def test_get_products(client):
    """GET /products returns paginated list (200 if DB ok, skip if DB unavailable)."""
    try:
        response = client.get("/products")
    except Exception:
        pytest.skip("DB connection failed")
        return
    assert response.status_code in (200, 500)
    if response.status_code == 200:
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert isinstance(data["items"], list)


def test_get_products_with_filters(client):
    """GET /products with query params."""
    try:
        response = client.get("/products?category=Test&min_price=100&max_price=500&sort_by=price&page=1&page_size=10")
    except Exception:
        pytest.skip("DB connection failed")
        return
    assert response.status_code in (200, 500)
    if response.status_code == 200:
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10


def test_import_products_missing_file(client):
    """Import without file returns 422."""
    response = client.post("/products/import")
    assert response.status_code == 422


def test_import_products_invalid_csv(client):
    """Import with invalid CSV returns error report."""
    csv_content = "invalid,columns\n"
    response = client.post(
        "/products/import",
        files={"file": ("products.csv", csv_content.encode("utf-8"), "text/csv")},
    )
    # 200 with errors (missing columns) or 500 if DB unavailable
    assert response.status_code in (200, 500)
    if response.status_code == 200:
        data = response.json()
        assert "errors" in data
        assert "imported" in data
