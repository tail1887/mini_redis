from time import sleep

from app.services.kv_service import KVService
from app.stores.kv_store import InMemoryKVStore


def test_delete_treats_expired_key_as_missing() -> None:
    service = KVService(store=InMemoryKVStore())
    service.set_value("user:expired-del", "kim")
    service.expire_value("user:expired-del", 1)

    sleep(1.1)

    assert service.delete_value("user:expired-del") is False
    assert service.ttl_value("user:expired-del") == -2


def test_expire_and_persist_fail_after_key_is_expired() -> None:
    service = KVService(store=InMemoryKVStore())
    service.set_value("user:expired-state", "lee")
    service.expire_value("user:expired-state", 1)

    sleep(1.1)

    assert service.expire_value("user:expired-state", 10) is False
    assert service.persist_value("user:expired-state") is False
    assert service.exists_value("user:expired-state") is False


def test_get_cleans_up_expired_key_for_following_operations() -> None:
    service = KVService(store=InMemoryKVStore())
    service.set_value("user:expired-get", "park")
    service.expire_value("user:expired-get", 1)

    sleep(1.1)

    assert service.get_value("user:expired-get") is None
    assert service.delete_value("user:expired-get") is False
    assert service.persist_value("user:expired-get") is False
