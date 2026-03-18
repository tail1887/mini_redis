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
service = KVService(store=InMemoryKVStore())

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
    responses=COMMON_ERROR_RESPONSES,
)
def invalidate_prefix_value(payload: InvalidatePrefixRequest) -> SuccessResponse:
    deleted_count = service.invalidate_prefix_value(payload.prefix)
    cache_metrics.record_invalidation()
    cache_metrics.record_delete(deleted_count)
    return SuccessResponse(data={"deletedCount": deleted_count})


__all__ = ["router", "KV_SUCCESS_EXAMPLES", "KV_FAILURE_EXAMPLES"]
