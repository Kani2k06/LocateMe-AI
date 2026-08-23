from fastapi import APIRouter

from .health import router as health_router
from .persons import router as persons_router
from .cctv import router as cctv_router
from .detections import router as detections_router
from .detection_report import router as detection_report_router
from .alerts import router as alerts_router
from .stats import router as stats_router
from .settings import router as settings_router


api_router = APIRouter(
    prefix="/api"
)


# ============================================================
# API ROUTES
# ============================================================

api_router.include_router(
    health_router
)

api_router.include_router(
    persons_router
)

api_router.include_router(
    cctv_router
)

api_router.include_router(
    detections_router
)

api_router.include_router(
    detection_report_router
)

api_router.include_router(
    alerts_router
)

api_router.include_router(
    stats_router
)

api_router.include_router(
    settings_router
)


__all__ = [
    "api_router"
]