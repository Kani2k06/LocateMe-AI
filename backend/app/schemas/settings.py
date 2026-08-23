from pydantic import BaseModel, Field


class SettingsResponse(BaseModel):
    similarity_threshold: float = Field(..., example=0.80)
    alert_threshold: float = Field(..., example=0.90)
    frame_sample_interval: float = Field(..., example=1.0)
    supabase_connected: bool = False


class SettingsUpdate(BaseModel):
    similarity_threshold: float = Field(..., ge=0.5, le=0.99, example=0.80)
    alert_threshold: float = Field(default=0.90, ge=0.5, le=1.0, example=0.90)
    frame_sample_interval: float = Field(default=1.0, ge=0.1, le=10.0, example=1.0)
