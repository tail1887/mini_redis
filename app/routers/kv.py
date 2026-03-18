from fastapi import APIRouter, Query

from app.core.errors import APIError
from app.observability.cache_metrics import cache_metrics
from app.schemas.kv import (
    ErrorResponse,
    KV_FAILURE_EXAMPLES,
    KV_SUCCESS_EXAMPLES,
    SetRequest,
    SuccessResponse,
)
from app.services.kv_service import KVService
from app.stores.kv_store import InMemoryKVStore

router = APIRouter(prefix="/v1/kv", tags=["kv"])
service = KVService(store=InMemoryKVStore(), metrics=cache_metrics)

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

GET_ERROR_RESPONSES = COMMON_ERROR_RESPONSES | {
    404: {
        "model": ErrorResponse,
        "content": {"application/json": {"example": KV_FAILURE_EXAMPLES["key_not_found"]}},
    }
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
def get_value(key: str = Query(min_length=1)) -> SuccessResponse:
    value = service.get_value(key)
    if value is None:
        raise APIError("KEY_NOT_FOUND")
    return SuccessResponse(data={"key": key, "value": value})


@router.delete("/del", response_model=SuccessResponse, responses=COMMON_ERROR_RESPONSES)
def delete_value(key: str = Query(min_length=1)) -> SuccessResponse:
    deleted = service.delete_value(key)
    return SuccessResponse(data={"deleted": deleted})


@router.get("/exists", response_model=SuccessResponse, responses=COMMON_ERROR_RESPONSES)
def exists_value(key: str = Query(min_length=1)) -> SuccessResponse:
    exists = service.exists_value(key)
    return SuccessResponse(data={"exists": exists})


__all__ = ["router", "KV_SUCCESS_EXAMPLES", "KV_FAILURE_EXAMPLES"]
