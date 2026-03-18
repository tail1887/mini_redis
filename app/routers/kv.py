from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.schemas.kv import (
    ErrorResponse,
    KV_FAILURE_EXAMPLES,
    KV_SUCCESS_EXAMPLES,
    KeyQuery,
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
        400: {"model": ErrorResponse, "content": {"application/json": {"example": KV_FAILURE_EXAMPLES["invalid_input"]}}},
        404: {"model": ErrorResponse, "content": {"application/json": {"example": KV_FAILURE_EXAMPLES["key_not_found"]}}},
    },
)
def get_value(query: Annotated[KeyQuery, Depends()]) -> SuccessResponse | ErrorResponse:
    value = service.get_value(query.key)
    if value is None:
        return JSONResponse(
            status_code=404,
            content=KV_FAILURE_EXAMPLES["key_not_found"],
        )
    return SuccessResponse(data={"key": query.key, "value": value})


@router.delete(
    "/del",
    response_model=SuccessResponse,
    responses={
        400: {"model": ErrorResponse, "content": {"application/json": {"example": KV_FAILURE_EXAMPLES["invalid_input"]}}}
    },
)
def delete_value(query: Annotated[KeyQuery, Depends()]) -> SuccessResponse:
    deleted = service.delete_value(query.key)
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
        400: {"model": ErrorResponse, "content": {"application/json": {"example": KV_FAILURE_EXAMPLES["invalid_input"]}}},
    },
)
def exists_value(query: Annotated[KeyQuery, Depends()]) -> SuccessResponse:
    exists = service.exists_value(query.key)
    return SuccessResponse(data={"exists": exists})


__all__ = ["router", "KV_SUCCESS_EXAMPLES", "KV_FAILURE_EXAMPLES"]
