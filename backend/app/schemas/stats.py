from typing import List, Dict, Any
from pydantic import BaseModel


class StatCardItem(BaseModel):
    label: str
    value: str
    hint: str
    icon: str


class DashboardStatsResponse(BaseModel):
    stats: List[StatCardItem]
    active_cases: int
    matches_today: int
    open_alerts: int
    cctv_jobs: int


class CategoryCount(BaseModel):
    label: str
    value: int


class AnalyticsResponse(BaseModel):
    match_rate: str
    avg_confidence: str
    median_time_to_match: str
    cameras_online: str
    by_status: List[CategoryCount]
    by_location: List[CategoryCount]
