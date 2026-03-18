from typing import Any

from pydantic import BaseModel, field_validator

from app.core.errors import build_error_payload
from app.schemas.common import ErrorResponse, SuccessResponse
from app.services.key_namespace import validate_namespaced_key
from app.services.key_namespace import validate_prefix


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


class ExpireRequest(BaseModel):
    key: str
    seconds: int

    @field_validator("key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        return validate_namespaced_key(value)


class PersistRequest(BaseModel):
    key: str

    @field_validator("key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        return validate_namespaced_key(value)


class InvalidatePrefixRequest(BaseModel):
    prefix: str

    @field_validator("prefix")
    @classmethod
    def validate_prefix_value(cls, value: str) -> str:
        return validate_prefix(value)


KV_SUCCESS_EXAMPLES: dict[str, dict[str, object]] = {
    "set": {"success": True, "data": {"stored": True}},
    "get": {"success": True, "data": {"key": "user:1", "value": "kim"}},
    "del": {"success": True, "data": {"deleted": True}},
    "exists": {"success": True, "data": {"exists": True}},
    "expire": {"success": True, "data": {"updated": True}},
    "ttl": {"success": True, "data": {"ttl": -1}},
    "persist": {"success": True, "data": {"updated": True}},
    "invalidate_prefix": {"success": True, "data": {"deletedCount": 2}},
}

KV_FAILURE_EXAMPLES: dict[str, dict[str, Any]] = {
    "invalid_input": build_error_payload("INVALID_INPUT"),
    "key_not_found": build_error_payload("KEY_NOT_FOUND"),
    "ttl_invalid": build_error_payload("TTL_INVALID", "seconds must be a positive integer"),
    "internal_error": build_error_payload("INTERNAL_ERROR"),
}
