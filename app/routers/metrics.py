from fastapi import APIRouter

from app.observability.cache_metrics import cache_metrics
from app.schemas.common import SuccessResponse


router = APIRouter(prefix="/v1/metrics", tags=["metrics"])


@router.get("/cache", response_model=SuccessResponse)
def get_cache_metrics() -> SuccessResponse:
    return SuccessResponse(data=cache_metrics.snapshot())


__all__ = ["router"]
