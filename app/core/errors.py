from __future__ import annotations

from typing import Any

from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError


ERROR_DEFINITIONS: dict[str, dict[str, Any]] = {
    "INVALID_INPUT": {"status_code": 400, "message": "invalid input"},
    "KEY_NOT_FOUND": {"status_code": 404, "message": "key not found"},
    "TTL_INVALID": {"status_code": 400, "message": "ttl is invalid"},
    "PREFIX_INVALID": {"status_code": 400, "message": "prefix is invalid"},
    "INTERNAL_ERROR": {"status_code": 500, "message": "internal server error"},
}


class APIError(Exception):
    def __init__(
        self,
        code: str,
        message: str | None = None,
        status_code: int | None = None,
    ) -> None:
        definition = ERROR_DEFINITIONS[code]
        self.code = code
        self.message = message or definition["message"]
        self.status_code = status_code or definition["status_code"]
        super().__init__(self.message)

    def to_response(self) -> dict[str, Any]:
        return build_error_payload(self.code, self.message)


def build_error_payload(code: str, message: str | None = None) -> dict[str, Any]:
    definition = ERROR_DEFINITIONS[code]
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message or definition["message"],
        },
    }


def map_validation_error(exc: RequestValidationError | ValidationError) -> APIError:
    detail = exc.errors()[0] if exc.errors() else {}
    field = _extract_field_name(detail)
    error_type = detail.get("type")
    raw_message = detail.get("msg")

    if error_type == "missing" and field:
        message = f"{field} is required"
    elif error_type in {"string_too_short", "too_short"} and field:
        message = f"{field} must not be empty"
    elif isinstance(raw_message, str) and raw_message:
        message = raw_message.removeprefix("Value error, ")
    else:
        message = ERROR_DEFINITIONS["INVALID_INPUT"]["message"]

    return APIError("INVALID_INPUT", message=message)


def _extract_field_name(detail: dict[str, Any]) -> str | None:
    location = detail.get("loc", ())
    if not location:
        return None
    field = location[-1]
    return field if isinstance(field, str) else None
