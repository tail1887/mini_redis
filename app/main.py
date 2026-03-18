from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.routers.kv import router as kv_router


app = FastAPI(title="mini_redis", version="0.1.0")
app.include_router(kv_router)


def _invalid_input_response(message: str) -> JSONResponse:
    if message.startswith("Value error, "):
        message = message.removeprefix("Value error, ")

    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": {"code": "INVALID_INPUT", "message": message},
        },
    )


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    message = "invalid input"
    errors = exc.errors()
    if errors:
        message = str(errors[0].get("msg", message))

    return _invalid_input_response(message)


@app.exception_handler(ValidationError)
async def model_validation_exception_handler(_: Request, exc: ValidationError) -> JSONResponse:
    message = "invalid input"
    errors = exc.errors()
    if errors:
        message = str(errors[0].get("msg", message))

    return _invalid_input_response(message)


@app.get("/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
