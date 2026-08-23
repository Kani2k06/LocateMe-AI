from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DetectionResponse(BaseModel):
    id: str
    detection_code: str
    person_id: str
    person_name: str
    person_photo: Optional[str] = None
    cctv_job_id: Optional[str] = None
    confidence: float
    frame_url: str
    location: str
    camera_id: str
    detected_at: str
    verification_status: str  # pending, verified, rejected
    bounding_box: Optional[Dict[str, Any]] = None
    created_at: str


class DetectionListResponse(BaseModel):
    total: int
    items: List[DetectionResponse]


class VerificationUpdate(BaseModel):
    status: str = Field(..., example="verified")  # verified, rejected, pending
