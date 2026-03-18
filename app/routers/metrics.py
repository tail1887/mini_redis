from fastapi import APIRouter

from app.schemas.common import SuccessResponse
from app.services.cache_metrics import cache_metrics

router = APIRouter(prefix="/v1/metrics", tags=["metrics"])


@router.get("/cache", response_model=SuccessResponse)
def get_cache_metrics() -> SuccessResponse:
    snapshot = cache_metrics.snapshot()
    return SuccessResponse(
        data={
            "hits": snapshot.hits,
            "misses": snapshot.misses,
            "deletes": snapshot.deletes,
            "invalidations": snapshot.invalidations,
            "errors": snapshot.errors,
        }
    )


__all__ = ["router"]
