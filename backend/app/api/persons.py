from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query

from app.core.database import db
from app.core.storage import storage
from app.services.face_engine import face_engine
from app.schemas.person import PersonResponse, PersonListResponse


router = APIRouter(prefix="/persons", tags=["Missing Persons"])


@router.post("", response_model=PersonResponse)
async def register_person(
    name: str = Form(...),
    case_id: Optional[str] = Form(None),
    age: int = Form(...),
    gender: str = Form(...),
    height: Optional[str] = Form(None),
    missing_since: Optional[str] = Form(None),
    last_known_location: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
):
    """
    Register a missing person.

    Validation order:
    1. Check duplicate case ID.
    2. Process reference photograph.
    3. Generate face embedding.
    4. Check whether the same face is already registered.
    5. Save photograph.
    6. Create database record.

    This prevents duplicate case IDs and duplicate face registrations.
    """

    # =========================================================
    # 1. VALIDATE / CHECK CASE ID FIRST
    # =========================================================

    normalized_case_id = case_id.strip() if case_id else None

    if normalized_case_id:
        existing = db.get_person_by_case_id(normalized_case_id)

        if existing:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Case ID '{normalized_case_id}' already exists. "
                    "Use a different case ID."
                ),
            )

    photo_url = None
    embedding = None

    # =========================================================
    # 2. PROCESS REFERENCE PHOTO
    # =========================================================

    if photo and photo.filename:

        photo_bytes = await photo.read()

        if not photo_bytes:
            raise HTTPException(
                status_code=400,
                detail="The uploaded photograph is empty.",
            )

        # -----------------------------------------------------
        # Generate face embedding
        # -----------------------------------------------------

        embedding, embedding_error = face_engine.process_person_photo(
            photo_bytes
        )

        if embedding_error:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Could not process reference photograph: "
                    f"{embedding_error}"
                ),
            )

        if not embedding:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No usable face embedding could be generated "
                    "from the photograph."
                ),
            )

        # =====================================================
        # 3. CHECK FOR DUPLICATE FACE
        # =====================================================

        duplicate_person = db.find_duplicate_person_by_embedding(
            embedding,
            threshold=0.95,
        )

        if duplicate_person:
            duplicate_name = duplicate_person.get(
                "name",
                "Unknown",
            )

            duplicate_case_id = duplicate_person.get(
                "case_id",
                "Unknown",
            )

            similarity = duplicate_person.get(
                "face_similarity",
                0,
            )

            similarity_percent = round(
                float(similarity) * 100,
                1,
            )

            raise HTTPException(
                status_code=409,
                detail=(
                    f"This person appears to already be registered as "
                    f"'{duplicate_name}' "
                    f"(Case ID: {duplicate_case_id}). "
                    f"Face similarity: {similarity_percent}%. "
                    "Use the existing missing-person record instead."
                ),
            )

        # =====================================================
        # 4. SAVE REFERENCE PHOTO
        # =====================================================

        # Photo is saved ONLY after:
        # - case ID validation
        # - face processing
        # - duplicate-face validation

        temp_case_id = normalized_case_id or "TEMP"

        photo_url = storage.save_photo(
            photo_bytes,
            photo.filename,
            temp_case_id,
        )

    # =========================================================
    # 5. CREATE DATABASE RECORD
    # =========================================================

    person_data = {
        "name": name,
        "case_id": normalized_case_id,
        "age": age,
        "gender": gender,
        "height": height or "Unknown",
        "missing_since": missing_since,
        "last_known_location": last_known_location or "Unknown",
        "notes": notes,
        "photo_url": photo_url,
        "embedding": embedding,
        "status": "active_alert",
    }

    try:

        record = db.create_person(person_data)

    except Exception as exc:

        # Handles the rare race condition where another request
        # creates the same case ID after our pre-check but before INSERT.

        error_text = str(exc).lower()

        if (
            "missing_persons_case_id_key" in error_text
            or "duplicate key" in error_text
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Case ID '{normalized_case_id}' already exists. "
                    "Use a different case ID."
                ),
            ) from exc

        raise

    # =========================================================
    # 6. RETURN CREATED PERSON
    # =========================================================

    return {
        **record,
        "has_embedding": record.get("embedding") is not None,
    }


# =============================================================
# LIST MISSING PERSONS
# =============================================================

@router.get("", response_model=PersonListResponse)
def list_persons(
    status: Optional[str] = Query(
        None,
        description=(
            "Filter by status: "
            "active_alert, found_safe, pending_verification"
        ),
    ),
    search: Optional[str] = Query(
        None,
        description="Search by name, case ID, or location",
    ),
):
    """List registered missing persons with optional filtering."""

    items = db.get_persons(
        status=status,
        search=search,
    )

    response_items = [
        {
            **item,
            "has_embedding": item.get("embedding") is not None,
        }
        for item in items
    ]

    return {
        "total": len(response_items),
        "items": response_items,
    }


# =============================================================
# GET SINGLE PERSON
# =============================================================

@router.get("/{person_id}", response_model=PersonResponse)
def get_person(person_id: str):
    """Retrieve a single missing-person record."""

    person = db.get_person(person_id)

    if not person:
        raise HTTPException(
            status_code=404,
            detail="Missing person record not found.",
        )

    return {
        **person,
        "has_embedding": person.get("embedding") is not None,
    }


# =============================================================
# UPDATE PERSON STATUS
# =============================================================

@router.patch("/{person_id}/status")
def update_status(
    person_id: str,
    status: str = Query(
        ...,
        description=(
            "Status values: "
            "active_alert, found_safe, pending_verification"
        ),
    ),
):
    """Update the status of a missing-person case."""

    updated = db.update_person_status(
        person_id,
        status,
    )

    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Missing person record not found.",
        )

    return updated