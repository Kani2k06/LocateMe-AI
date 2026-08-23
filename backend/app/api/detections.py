from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Body

from app.core.database import db
from app.schemas.detection import (
    DetectionResponse,
    DetectionListResponse,
    VerificationUpdate,
)


router = APIRouter(
    prefix="/detections",
    tags=["Detections"],
)


# ============================================================
# LIST DETECTIONS
# ============================================================

@router.get(
    "",
    response_model=DetectionListResponse,
)
def list_detections(
    status: Optional[str] = Query(
        None,
        description=(
            "Filter by verification status: "
            "pending, verified, rejected"
        ),
    )
):
    """
    Lists detection results.

    Results come directly from Supabase through the
    DatabaseRepository.
    """

    items = db.get_detections(
        status=status
    )

    return {
        "total": len(items),
        "items": items,
    }


# ============================================================
# VERIFY / REJECT DETECTION
# ============================================================

@router.patch(
    "/{detection_id}/verify",
    response_model=DetectionResponse,
)
def verify_detection(
    detection_id: str,
    payload: VerificationUpdate = Body(...),
):
    """
    Updates the verification status of a detection.

    Accepted values:
        pending
        verified
        rejected
    """

    allowed_statuses = {
        "pending",
        "verified",
        "rejected",
    }

    if payload.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid verification status. "
                "Use pending, verified, or rejected."
            ),
        )

    updated = db.update_detection_status(
        detection_id,
        payload.status,
    )

    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Detection record not found.",
        )

    # Add person information expected by the frontend.
    person_id = updated.get("person_id")

    if person_id:
        person = db.get_person(person_id)

        if person:
            updated["person_name"] = person.get(
                "name"
            )
            updated["person_photo"] = person.get(
                "photo_url"
            )

    return updated