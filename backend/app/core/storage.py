import os
import uuid
from pathlib import Path
from typing import Optional, Union
import cv2
import numpy as np
from app.config import settings


class StorageService:
    def __init__(self):
        self.base_dir = Path(settings.STORAGE_DIR).resolve()
        self.photos_dir = self.base_dir / "photos"
        self.videos_dir = self.base_dir / "videos"
        self.frames_dir = self.base_dir / "frames"

        # Ensure local storage directories exist
        for d in [self.photos_dir, self.videos_dir, self.frames_dir]:
            d.mkdir(parents=True, exist_ok=True)

        self.supabase_client = None
        if settings.SUPABASE_URL and settings.SUPABASE_KEY:
            try:
                from supabase import create_client
                self.supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            except Exception as e:
                print(f"[Storage] Note: Supabase Storage initialization skipped: {e}")

    def save_photo(self, data: bytes, filename: str, case_id: str) -> str:
        """Saves a reference person photograph and returns its accessible URL."""
        clean_ext = Path(filename).suffix.lower() or ".jpg"
        unique_name = f"{case_id}_{uuid.uuid4().hex[:8]}{clean_ext}"

        # 1. Try Supabase Storage if configured
        if self.supabase_client:
            try:
                storage_path = f"{case_id}/{unique_name}"
                self.supabase_client.storage.from_(settings.SUPABASE_BUCKET_PHOTOS).upload(
                    path=storage_path,
                    file=data,
                    file_options={"content-type": "image/jpeg"}
                )
                return self.supabase_client.storage.from_(settings.SUPABASE_BUCKET_PHOTOS).get_public_url(storage_path)
            except Exception as e:
                print(f"[Storage] Supabase upload failed, falling back to local storage: {e}")

        # 2. Local fallback
        dest_path = self.photos_dir / unique_name
        with open(dest_path, "wb") as f:
            f.write(data)
        return f"/static/photos/{unique_name}"

    def save_video(self, data: bytes, filename: str, job_code: str) -> tuple[str, str]:
        """Saves an uploaded CCTV video file locally and returns (url, local_file_path)."""
        clean_ext = Path(filename).suffix.lower() or ".mp4"
        unique_name = f"{job_code}_{uuid.uuid4().hex[:8]}{clean_ext}"
        dest_path = self.videos_dir / unique_name

        with open(dest_path, "wb") as f:
            f.write(data)

        local_path = str(dest_path)
        url = f"/static/videos/{unique_name}"
        return url, local_path

    def save_frame(self, frame_img: np.ndarray, job_code: str, frame_idx: int) -> str:
        """Encodes and saves a matched video frame as JPG and returns accessible URL."""
        unique_name = f"{job_code}_frame_{frame_idx:06d}_{uuid.uuid4().hex[:6]}.jpg"
        dest_path = self.frames_dir / unique_name

        cv2.imwrite(str(dest_path), frame_img, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        return f"/static/frames/{unique_name}"


storage = StorageService()
