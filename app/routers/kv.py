from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

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
service = KVService(store=InMemoryKVStore())


@router.post(
    "/set",
    response_model=SuccessResponse,
    responses={
        400: {"model": ErrorResponse, "content": {"application/json": {"example": KV_FAILURE_EXAMPLES["invalid_input"]}}}
    },
)
def set_value(payload: SetRequest) -> SuccessResponse:
    stored = service.set_value(payload.key, payload.value)
    return SuccessResponse(data={"stored": stored})


@router.get(
    "/get",
    response_model=SuccessResponse,
    responses={
        404: {"model": ErrorResponse, "content": {"application/json": {"example": KV_FAILURE_EXAMPLES["key_not_found"]}}}
    },
)
def get_value(key: str = Query(min_length=1)) -> SuccessResponse | ErrorResponse:
    value = service.get_value(key)
    if value is None:
        return JSONResponse(
            status_code=404,
            content=KV_FAILURE_EXAMPLES["key_not_found"],
        )
    return SuccessResponse(data={"key": key, "value": value})


@router.delete("/del", response_model=SuccessResponse)
def delete_value(key: str = Query(min_length=1)) -> SuccessResponse:
    deleted = service.delete_value(key)
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
        }
    },
)
def exists_value(key: str = Query(min_length=1)) -> SuccessResponse:
    exists = service.exists_value(key)
    return SuccessResponse(data={"exists": exists})


__all__ = ["router", "KV_SUCCESS_EXAMPLES", "KV_FAILURE_EXAMPLES"]
