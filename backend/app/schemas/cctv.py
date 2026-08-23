from typing import Optional, List
from pydantic import BaseModel, Field


class CCTVJobResponse(BaseModel):
    id: str
    job_code: str
    filename: str
    video_url: Optional[str] = None
    location: str
    camera_id: str
    capture_time: str
    status: str  # queued, extracting, matching, complete, failed
    total_frames: int = 0
    processed_frames: int = 0
    faces_detected: int = 0
    matches_found: int = 0
    error_message: Optional[str] = None
    created_at: str


class CCTVJobListResponse(BaseModel):
    total: int
    items: List[CCTVJobResponse]
