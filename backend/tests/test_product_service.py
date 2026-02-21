"""ProductService unit tests."""

import pytest

from app.repositories.product import ProductRepository
from app.services.product import ProductService, PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW


@pytest.fixture
def service():
    """ProductService with mocked repository (no DB needed for score tests)."""
    return ProductService(repository=None)  # type: ignore


def test_calculate_popularity_score_high(service):
    """price < 500 → high (1.0)."""
    assert service.calculate_popularity_score(100) == PRIORITY_HIGH
    assert service.calculate_popularity_score(499) == PRIORITY_HIGH


def test_calculate_popularity_score_medium(service):
    """500–800 → medium (0.5)."""
    assert service.calculate_popularity_score(500) == PRIORITY_MEDIUM
    assert service.calculate_popularity_score(650) == PRIORITY_MEDIUM
    assert service.calculate_popularity_score(800) == PRIORITY_MEDIUM


def test_calculate_popularity_score_low(service):
    """price > 800 → low (0.2)."""
    assert service.calculate_popularity_score(801) == PRIORITY_LOW
    assert service.calculate_popularity_score(1000) == PRIORITY_LOW


def test_calculate_popularity_score_invalid(service):
    """price <= 0 → 0.0."""
    assert service.calculate_popularity_score(0) == 0.0
    assert service.calculate_popularity_score(-10) == 0.0


def test_get_priority(service):
    """get_priority returns correct labels."""
    assert service.get_priority(100) == "высокий"
    assert service.get_priority(500) == "средний"
    assert service.get_priority(900) == "низкий"
