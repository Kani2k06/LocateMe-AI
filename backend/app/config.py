import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Server
    PORT: int = Field(default=8000, validation_alias="PORT")
    HOST: str = Field(default="0.0.0.0", validation_alias="HOST")
    CORS_ORIGINS_RAW: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000",
        validation_alias="CORS_ORIGINS"
    )

    # Supabase credentials (optional)
    SUPABASE_URL: str = Field(default="", validation_alias="SUPABASE_URL")
    SUPABASE_KEY: str = Field(default="", validation_alias="SUPABASE_KEY")
    SUPABASE_BUCKET_PHOTOS: str = Field(default="photos", validation_alias="SUPABASE_BUCKET_PHOTOS")
    SUPABASE_BUCKET_VIDEOS: str = Field(default="cctv-videos", validation_alias="SUPABASE_BUCKET_VIDEOS")
    SUPABASE_BUCKET_FRAMES: str = Field(default="cctv-frames", validation_alias="SUPABASE_BUCKET_FRAMES")

    # Recognition defaults
    DEFAULT_SIMILARITY_THRESHOLD: float = Field(default=0.80, validation_alias="DEFAULT_SIMILARITY_THRESHOLD")
    DEFAULT_ALERT_THRESHOLD: float = Field(default=0.90, validation_alias="DEFAULT_ALERT_THRESHOLD")
    FRAME_SAMPLE_INTERVAL_SECONDS: float = Field(default=1.0, validation_alias="FRAME_SAMPLE_INTERVAL_SECONDS")

    # Local storage fallback directory
    STORAGE_DIR: str = Field(default="./storage", validation_alias="STORAGE_DIR")

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS_RAW.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
