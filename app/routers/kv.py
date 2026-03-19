import os
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.errors import APIError
from app.schemas.kv import (
    ExpireRequest,
    ErrorResponse,
    InvalidatePrefixRequest,
    KV_FAILURE_EXAMPLES,
    KV_SUCCESS_EXAMPLES,
    KeyQuery,
    PersistRequest,
    SetRequest,
    SuccessResponse,
)
from app.services.kv_service import KVService
from app.services.cache_metrics import cache_metrics
from app.stores.kv_store import InMemoryKVStore

router = APIRouter(prefix="/v1/kv", tags=["kv"])


def _build_store() -> InMemoryKVStore:
    persistence_dir = os.getenv("KV_PERSISTENCE_DIR", "").strip()
    snapshot_every_raw = os.getenv("KV_SNAPSHOT_EVERY", "0").strip()
    try:
        snapshot_every = int(snapshot_every_raw)
    except ValueError:
        snapshot_every = 0

    if not persistence_dir:
        return InMemoryKVStore()

    base_dir = Path(persistence_dir)
    base_dir.mkdir(parents=True, exist_ok=True)
    return InMemoryKVStore(
        aof_path=base_dir / "kv.aof",
        snapshot_path=base_dir / "kv.snapshot.json",
        snapshot_every=snapshot_every,
    )


service = KVService(store=_build_store())

COMMON_ERROR_RESPONSES = {
    400: {
        "model": ErrorResponse,
        "content": {"application/json": {"example": KV_FAILURE_EXAMPLES["invalid_input"]}},
    },
    500: {
        "model": ErrorResponse,
        "content": {"application/json": {"example": KV_FAILURE_EXAMPLES["internal_error"]}},
    },
}

GET_ERROR_RESPONSES = {
    **COMMON_ERROR_RESPONSES,
    404: {
        "model": ErrorResponse,
        "content": {"application/json": {"example": KV_FAILURE_EXAMPLES["key_not_found"]}},
    },
}


@router.post(
    "/set",
    response_model=SuccessResponse,
    responses=COMMON_ERROR_RESPONSES,
)
def set_value(payload: SetRequest) -> SuccessResponse:
    stored = service.set_value(payload.key, payload.value)
    return SuccessResponse(data={"stored": stored})


@router.get(
    "/get",
    response_model=SuccessResponse,
    responses=GET_ERROR_RESPONSES,
)
def get_value(query: Annotated[KeyQuery, Depends()]) -> SuccessResponse:
    value = service.get_value(query.key)
    if value is None:
        cache_metrics.record_miss()
        raise APIError("KEY_NOT_FOUND")
    cache_metrics.record_hit()
    return SuccessResponse(data={"key": query.key, "value": value})


@router.delete(
    "/del",
    response_model=SuccessResponse,
    responses=COMMON_ERROR_RESPONSES,
)
def delete_value(query: Annotated[KeyQuery, Depends()]) -> SuccessResponse:
    deleted = service.delete_value(query.key)
    if deleted:
        cache_metrics.record_delete()
    return SuccessResponse(data={"deleted": deleted})


@router.get(
    "/exists",
    response_model=SuccessResponse,
    responses={
        200: {
            "content": {
                "application/json": {
                    "examples": {
                        "exists": {"summary": "Key exists", "value": KV_SUCCESS_EXAMPLES["exists"]},
                        "missing": {"summary": "Key missing", "value": {"success": True, "data": {"exists": False}}},
                    }
                }
            }
        },
        **COMMON_ERROR_RESPONSES,
    },
)
def exists_value(query: Annotated[KeyQuery, Depends()]) -> SuccessResponse:
    exists = service.exists_value(query.key)
    if exists:
        cache_metrics.record_hit()
    else:
        cache_metrics.record_miss()
    return SuccessResponse(data={"exists": exists})


@router.post(
    "/expire",
    response_model=SuccessResponse,
    responses={
        **COMMON_ERROR_RESPONSES,
        400: {
            "model": ErrorResponse,
            "content": {"application/json": {"example": KV_FAILURE_EXAMPLES["ttl_invalid"]}},
        },
    },
)
def expire_value(payload: ExpireRequest) -> SuccessResponse:
    updated = service.expire_value(payload.key, payload.seconds)
    return SuccessResponse(data={"updated": updated})


@router.get(
    "/ttl",
    response_model=SuccessResponse,
    responses=COMMON_ERROR_RESPONSES,
)
def ttl_value(query: Annotated[KeyQuery, Depends()]) -> SuccessResponse:
    ttl = service.ttl_value(query.key)
    return SuccessResponse(data={"ttl": ttl})


@router.post(
    "/persist",
    response_model=SuccessResponse,
    responses=COMMON_ERROR_RESPONSES,
)
def persist_value(payload: PersistRequest) -> SuccessResponse:
    updated = service.persist_value(payload.key)
    return SuccessResponse(data={"updated": updated})


@router.post(
    "/invalidate-prefix",
    response_model=SuccessResponse,
    responses={
        **COMMON_ERROR_RESPONSES,
        400: {
            "model": ErrorResponse,
            "content": {"application/json": {"example": KV_FAILURE_EXAMPLES["prefix_invalid"]}},
        },
    },
)
def invalidate_prefix_value(payload: InvalidatePrefixRequest) -> SuccessResponse:
    deleted_count = service.invalidate_prefix(payload.prefix)
    cache_metrics.record_invalidation()
    cache_metrics.record_delete(deleted_count)
    return SuccessResponse(data={"deletedCount": deleted_count})


__all__ = ["router", "KV_SUCCESS_EXAMPLES", "KV_FAILURE_EXAMPLES"]
