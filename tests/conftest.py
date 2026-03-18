import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import app.routers.kv as kv_router
from app.stores.kv_store import InMemoryKVStore


@pytest.fixture(autouse=True)
def reset_store() -> None:
    kv_router.service.store = InMemoryKVStore()
