from __future__ import annotations

import os
from dataclasses import dataclass

from app.services.cache_metrics import cache_metrics


@dataclass
class ReadinessResult:
    ready: bool
    stage: int
    summary: str


def evaluate_readiness() -> ReadinessResult:
    """
    Stage-5 readiness is intentionally explicit.
    RELEASE_READY=true is required to mark a release candidate as ready.
    """
    release_ready = os.getenv("RELEASE_READY", "false").lower() == "true"
    metrics = cache_metrics.snapshot()

    if not release_ready:
        return ReadinessResult(
            ready=False,
            stage=5,
            summary="release gate is closed: set RELEASE_READY=true after checklist and load verification",
        )

    return ReadinessResult(
        ready=True,
        stage=5,
        summary=(
            "release gate is open; "
            f"runtime metrics snapshot hits={metrics.hits}, misses={metrics.misses}, "
            f"errors={metrics.errors}"
        ),
    )
