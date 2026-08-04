import sys
import os
import pytest

# Ensure backend root is in PYTHONPATH before importing app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from database.models import APIKey


@pytest.fixture
def override_deps():
    import main

    async def override_verify_api_key():
        return APIKey(id=1, tenant_id=1, hashed_key="sk_sentinel_demo", is_active=True)

    db_mock = MagicMock()
    db_mock.query.return_value.filter.return_value.first.return_value = None

    main.app.dependency_overrides[main.verify_api_key] = override_verify_api_key
    main.app.dependency_overrides[main.get_db] = lambda: db_mock
    yield db_mock
    main.app.dependency_overrides = {}


@pytest.fixture
def client(override_deps):
    import main

    return TestClient(main.app)