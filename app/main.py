from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.core.errors import APIError, map_validation_error
from app.routers.kv import router as kv_router
from app.schemas.common import SuccessResponse


app = FastAPI(title="mini_redis", version="0.1.0")
app.include_router(kv_router)


@app.exception_handler(APIError)
async def handle_api_error(_: Request, exc: APIError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.to_response())


@app.exception_handler(RequestValidationError)
async def handle_request_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    api_error = map_validation_error(exc)
    return JSONResponse(status_code=api_error.status_code, content=api_error.to_response())


@app.exception_handler(ValidationError)
async def handle_model_validation_error(_: Request, exc: ValidationError) -> JSONResponse:
    api_error = map_validation_error(exc)
    return JSONResponse(status_code=api_error.status_code, content=api_error.to_response())


@app.exception_handler(Exception)
async def handle_unexpected_error(_: Request, __: Exception) -> JSONResponse:
    api_error = APIError("INTERNAL_ERROR")
    return JSONResponse(status_code=api_error.status_code, content=api_error.to_response())


@app.get("/v1/health", response_model=SuccessResponse)
def health() -> SuccessResponse:
    return SuccessResponse(data={"status": "ok"})
