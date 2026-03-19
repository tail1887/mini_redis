from fastapi import APIRouter

import app.routers.kv as kv_router
from app.schemas.common import SuccessResponse
from app.services.readiness import evaluate_readiness

router = APIRouter(prefix="/v1/system", tags=["system"])


@router.get("/readiness", response_model=SuccessResponse)
def get_readiness() -> SuccessResponse:
    result = evaluate_readiness()
    return SuccessResponse(
        data={
            "ready": result.ready,
            "stage": result.stage,
            "summary": result.summary,
        }
    )


@router.get("/durability", response_model=SuccessResponse)
def get_durability() -> SuccessResponse:
    store = kv_router.service.store
    if not hasattr(store, "durability_status"):
        return SuccessResponse(
            data={
                "enabled": False,
                "aofPath": "",
                "snapshotPath": "",
                "aofExists": False,
                "snapshotExists": False,
                "snapshotEvery": 0,
            }
        )
    return SuccessResponse(data=store.durability_status())
