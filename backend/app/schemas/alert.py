from typing import Optional, List
from pydantic import BaseModel


class AlertResponse(BaseModel):
    id: str
    alert_code: str
    detection_id: Optional[str] = None
    case_id: str
    title: str
    detail: str
    severity: str  # critical, high, info
    is_read: bool = False
    created_at: str


class AlertListResponse(BaseModel):
    total: int
    items: List[AlertResponse]
