from typing import Any

from pydantic import BaseModel, field_validator

from app.services.key_namespace import validate_namespaced_key


class ErrorDetail(BaseModel):
    code: str
    message: str


class SuccessResponse(BaseModel):
    success: bool = True
    data: dict[str, Any]


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail


class SetRequest(BaseModel):
    key: str
    value: str

    @field_validator("key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        return validate_namespaced_key(value)


class KeyQuery(BaseModel):
    key: str

    @field_validator("key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        return validate_namespaced_key(value)


KV_SUCCESS_EXAMPLES: dict[str, dict[str, Any]] = {
    "set": {"success": True, "data": {"stored": True}},
    "get": {"success": True, "data": {"key": "user:1", "value": "kim"}},
    "del": {"success": True, "data": {"deleted": True}},
    "exists": {"success": True, "data": {"exists": True}},
}

KV_FAILURE_EXAMPLES: dict[str, dict[str, Any]] = {
    "invalid_input": {
        "success": False,
        "error": {
            "code": "INVALID_INPUT",
            "message": "key must use namespace format (<prefix>:<name>)",
        },
    },
    "key_not_found": {
        "success": False,
        "error": {"code": "KEY_NOT_FOUND", "message": "key not found"},
    },
    "not_implemented": {
        "success": False,
        "error": {
            "code": "NOT_IMPLEMENTED",
            "message": "KV feature scaffolded only. Implementation is pending.",
        },
    },
}
