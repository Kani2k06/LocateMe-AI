import os
import uuid
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from app.config import settings


class StorageService:
    """
    LocateMe storage service.

    Primary storage:
        Supabase Storage

    Local fallback:
        backend/storage/

    Supabase is preferred because Render's local filesystem
    should not be treated as permanent storage.
    """

    def __init__(self):
        # =========================================================
        # LOCAL DIRECTORIES
        # =========================================================

        self.base_dir = Path(settings.STORAGE_DIR).resolve()

        self.photos_dir = self.base_dir / "photos"
        self.videos_dir = self.base_dir / "videos"
        self.frames_dir = self.base_dir / "frames"

        for directory in [
            self.photos_dir,
            self.videos_dir,
            self.frames_dir,
        ]:
            directory.mkdir(
                parents=True,
                exist_ok=True,
            )

        # =========================================================
        # SUPABASE CONFIG
        # =========================================================

        self.supabase_client = None

        self.supabase_url = (
            settings.SUPABASE_URL
            or os.getenv("SUPABASE_URL")
        )

        self.supabase_key = (
            settings.SUPABASE_KEY
            or os.getenv("SUPABASE_KEY")
        )

        self.photos_bucket = (
            settings.SUPABASE_BUCKET_PHOTOS
            or os.getenv(
                "SUPABASE_BUCKET_PHOTOS",
                "photos",
            )
        )

        self.frames_bucket = (
            os.getenv(
                "SUPABASE_BUCKET_FRAMES",
                "frames",
            )
        )

        # =========================================================
        # INITIALIZE SUPABASE
        # =========================================================

        if self.supabase_url and self.supabase_key:
            try:
                from supabase import create_client

                self.supabase_client = create_client(
                    self.supabase_url,
                    self.supabase_key,
                )

                print(
                    "[Storage] Supabase client initialized successfully."
                )

                print(
                    "[Storage] Photos bucket:",
                    self.photos_bucket,
                )

                print(
                    "[Storage] Frames bucket:",
                    self.frames_bucket,
                )

            except Exception as exc:

                print(
                    "[Storage] Supabase initialization failed:",
                    exc,
                )

                self.supabase_client = None

        else:

            print(
                "[Storage] Supabase credentials not configured."
            )

            print(
                "[Storage] Local storage fallback enabled."
            )

    # =============================================================
    # MIME TYPE
    # =============================================================

    def _get_content_type(
        self,
        filename: str,
    ) -> str:

        extension = (
            Path(filename)
            .suffix
            .lower()
        )

        content_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
            ".mp4": "video/mp4",
            ".mkv": "video/x-matroska",
            ".avi": "video/x-msvideo",
        }

        return content_types.get(
            extension,
            "application/octet-stream",
        )

    # =============================================================
    # SUPABASE PUBLIC URL
    # =============================================================

    def _get_public_url(
        self,
        bucket: str,
        storage_path: str,
    ) -> Optional[str]:

        if not self.supabase_client:
            return None

        try:

            url = (
                self.supabase_client
                .storage
                .from_(bucket)
                .get_public_url(storage_path)
            )

            if isinstance(url, str):
                return url

            if isinstance(url, dict):

                return (
                    url.get("publicUrl")
                    or url.get("public_url")
                    or url.get("url")
                )

            return None

        except Exception as exc:

            print(
                "[Storage] Failed to generate Supabase "
                f"public URL: {exc}"
            )

            return None

    # =============================================================
    # SAVE PERSON PHOTO
    # =============================================================

    def save_photo(
        self,
        data: bytes,
        filename: str,
        case_id: str,
    ) -> str:
        """
        Save registered missing-person photograph.

        Supabase Storage is used as the primary location.
        """

        if not data:
            raise ValueError(
                "Cannot save an empty photograph."
            )

        clean_ext = (
            Path(filename)
            .suffix
            .lower()
            or ".jpg"
        )

        unique_name = (
            f"{case_id}_"
            f"{uuid.uuid4().hex[:8]}"
            f"{clean_ext}"
        )

        content_type = self._get_content_type(
            unique_name
        )

        print(
            "[Storage] Saving person photo:",
            unique_name,
        )

        # =========================================================
        # SUPABASE
        # =========================================================

        if self.supabase_client:

            try:

                storage_path = (
                    f"{case_id}/{unique_name}"
                )

                print(
                    "[Storage] Uploading person photo "
                    "to Supabase..."
                )

                print(
                    "[Storage] Bucket:",
                    self.photos_bucket,
                )

                print(
                    "[Storage] Path:",
                    storage_path,
                )

                response = (
                    self.supabase_client
                    .storage
                    .from_(self.photos_bucket)
                    .upload(
                        path=storage_path,
                        file=data,
                        file_options={
                            "content-type": content_type,
                            "upsert": "true",
                        },
                    )
                )

                print(
                    "[Storage] Supabase photo upload response:",
                    response,
                )

                public_url = self._get_public_url(
                    self.photos_bucket,
                    storage_path,
                )

                if public_url:

                    print(
                        "[Storage] Person photo uploaded "
                        "successfully."
                    )

                    print(
                        "[Storage] Person photo URL:",
                        public_url,
                    )

                    return public_url

            except Exception as exc:

                print(
                    "[Storage] Supabase person photo upload "
                    f"failed: {exc}"
                )

        # =========================================================
        # LOCAL FALLBACK
        # =========================================================

        destination = (
            self.photos_dir
            / unique_name
        )

        with open(
            destination,
            "wb",
        ) as file:

            file.write(data)

        print(
            "[Storage] Person photo saved locally:",
            destination,
        )

        return (
            f"/static/photos/{unique_name}"
        )

    # =============================================================
    # SAVE CCTV VIDEO
    # =============================================================

    def save_video(
        self,
        data: bytes,
        filename: str,
        job_code: str,
    ) -> tuple[str, str]:

        if not data:
            raise ValueError(
                "Cannot save an empty video."
            )

        clean_ext = (
            Path(filename)
            .suffix
            .lower()
            or ".mp4"
        )

        unique_name = (
            f"{job_code}_"
            f"{uuid.uuid4().hex[:8]}"
            f"{clean_ext}"
        )

        destination = (
            self.videos_dir
            / unique_name
        )

        with open(
            destination,
            "wb",
        ) as file:

            file.write(data)

        print(
            "[Storage] CCTV video saved:",
            destination,
        )

        url = (
            f"/static/videos/{unique_name}"
        )

        return (
            url,
            str(destination),
        )

    # =============================================================
    # SAVE CCTV FRAME
    # =============================================================

    def save_frame(
        self,
        frame_img: np.ndarray,
        job_code: str,
        frame_idx: int,
    ) -> str:
        """
        Save processed CCTV frame.

        Supabase Storage is preferred.
        Local storage is used only as fallback.
        """

        if frame_img is None:
            raise ValueError(
                "Cannot save an empty frame."
            )

        # =========================================================
        # UNIQUE FILE NAME
        # =========================================================

        unique_name = (
            f"{job_code}_"
            f"frame_{frame_idx:06d}_"
            f"{uuid.uuid4().hex[:6]}.jpg"
        )

        # =========================================================
        # ENCODE FRAME TO JPEG
        # =========================================================

        success, encoded = cv2.imencode(
            ".jpg",
            frame_img,
            [
                int(cv2.IMWRITE_JPEG_QUALITY),
                90,
            ],
        )

        if not success:

            raise RuntimeError(
                "OpenCV failed to encode CCTV frame."
            )

        frame_bytes = encoded.tobytes()

        print(
            "[Storage] Saving CCTV frame:",
            unique_name,
        )

        # =========================================================
        # SUPABASE STORAGE
        # =========================================================

        if self.supabase_client:

            try:

                storage_path = (
                    f"{job_code}/{unique_name}"
                )

                print(
                    "[Storage] Uploading CCTV frame "
                    "to Supabase..."
                )

                print(
                    "[Storage] Bucket:",
                    self.frames_bucket,
                )

                print(
                    "[Storage] Path:",
                    storage_path,
                )

                response = (
                    self.supabase_client
                    .storage
                    .from_(self.frames_bucket)
                    .upload(
                        path=storage_path,
                        file=frame_bytes,
                        file_options={
                            "content-type": "image/jpeg",
                            "upsert": "true",
                        },
                    )
                )

                print(
                    "[Storage] Supabase frame upload response:",
                    response,
                )

                public_url = self._get_public_url(
                    self.frames_bucket,
                    storage_path,
                )

                if public_url:

                    print(
                        "[Storage] CCTV frame uploaded "
                        "successfully."
                    )

                    print(
                        "[Storage] CCTV frame URL:",
                        public_url,
                    )

                    return public_url

            except Exception as exc:

                print(
                    "[Storage] Supabase CCTV frame upload "
                    f"failed: {exc}"
                )

        # =========================================================
        # LOCAL FALLBACK
        # =========================================================

        destination = (
            self.frames_dir
            / unique_name
        )

        with open(
            destination,
            "wb",
        ) as file:

            file.write(frame_bytes)

        print(
            "[Storage] CCTV frame saved locally:",
            destination,
        )

        return (
            f"/static/frames/{unique_name}"
        )


# =============================================================
# GLOBAL STORAGE INSTANCE
# =============================================================

storage = StorageService()