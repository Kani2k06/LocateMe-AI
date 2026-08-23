from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    """Health check endpoint for service status verification."""
    return {
        "status": "ok",
        "service": "LocateMe API"
    }
