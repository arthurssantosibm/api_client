# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from api.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def internal_headers():
    return {
        "X-Internal-Key": "INTERNAL_SECRET"
    }
