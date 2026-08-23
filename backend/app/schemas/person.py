from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class PersonBase(BaseModel):
    name: str = Field(..., example="Mateo Reyes")
    case_id: Optional[str] = Field(None, example="MP-24-0891")
    age: int = Field(..., ge=0, le=150, example=17)
    gender: str = Field(..., example="M")
    height: Optional[str] = Field(None, example="5'9\"")
    missing_since: str = Field(..., example="2026-08-06")
    last_known_location: str = Field(..., example="Downtown Transit Center, Sector 4")
    notes: Optional[str] = Field(None, example="Last seen wearing blue jacket")
    status: Optional[str] = Field(default="active_alert", example="active_alert")


class PersonCreate(PersonBase):
    pass


class PersonUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[str] = None
    missing_since: Optional[str] = None
    last_known_location: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class PersonResponse(PersonBase):
    id: str
    photo_url: Optional[str] = None
    created_at: str
    has_embedding: bool = False


class PersonListResponse(BaseModel):
    total: int
    items: List[PersonResponse]
