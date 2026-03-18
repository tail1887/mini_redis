from typing import Any

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str


class SuccessResponse(BaseModel):
    success: bool = True
    data: dict[str, Any]


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
