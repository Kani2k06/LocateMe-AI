from fastapi import APIRouter
from app.core.database import db
from app.schemas.settings import SettingsResponse, SettingsUpdate

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("", response_model=SettingsResponse)
def get_settings():
    """Gets current system recognition and alert threshold configurations."""
    current = db.get_settings()
    return {
        "similarity_threshold": current.get("similarity_threshold", 0.80),
        "alert_threshold": current.get("alert_threshold", 0.90),
        "frame_sample_interval": current.get("frame_sample_interval", 1.0),
        "supabase_connected": db.is_supabase_connected,
    }


@router.put("", response_model=SettingsResponse)
def update_settings(payload: SettingsUpdate):
    """Updates similarity threshold and alert parameters."""
    updated = db.update_settings(payload.model_dump())
    return {
        "similarity_threshold": updated.get("similarity_threshold", 0.80),
        "alert_threshold": updated.get("alert_threshold", 0.90),
        "frame_sample_interval": updated.get("frame_sample_interval", 1.0),
        "supabase_connected": db.is_supabase_connected,
    }
