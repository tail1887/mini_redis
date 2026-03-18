from pydantic import BaseModel, Field

from app.core.errors import build_error_payload
from app.schemas.common import ErrorResponse, SuccessResponse


class SetRequest(BaseModel):
    key: str = Field(min_length=1)
    value: str


class KeyQuery(BaseModel):
    key: str = Field(min_length=1)


KV_SUCCESS_EXAMPLES: dict[str, dict[str, object]] = {
    "set": {"success": True, "data": {"stored": True}},
    "get": {"success": True, "data": {"key": "user:1", "value": "kim"}},
    "del": {"success": True, "data": {"deleted": True}},
    "exists": {"success": True, "data": {"exists": True}},
}

KV_FAILURE_EXAMPLES: dict[str, dict[str, object]] = {
    "invalid_input": build_error_payload("INVALID_INPUT", "key is required"),
    "key_not_found": build_error_payload("KEY_NOT_FOUND"),
    "internal_error": build_error_payload("INTERNAL_ERROR"),
}
