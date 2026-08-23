import functools
import threading
import time
import uuid

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

import httpx

from app.config import settings


# ============================================================
# TRANSIENT SUPABASE ERRORS
# ============================================================

_TRANSIENT_SUPABASE_ERRORS = (
    httpx.RemoteProtocolError,
    httpx.ConnectError,
    httpx.ReadError,
    httpx.WriteError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.PoolTimeout,
)


def _is_retryable_supabase_error(
    exc: Exception,
) -> bool:
    """Return True only for errors that can be fixed by rebuilding the client."""

    if isinstance(
        exc,
        _TRANSIENT_SUPABASE_ERRORS,
    ):
        return True

    message = str(exc).lower()

    return (
        isinstance(exc, RuntimeError)
        and (
            "client is closed" in message
            or "cannot send a request" in message
        )
    )


def _with_supabase_retry(func):
    """
    Retry repository operations after a transient Supabase connection failure.

    The retry is intentionally limited to network/client-lifecycle failures.
    Normal application/database errors are allowed to propagate immediately.
    """

    @functools.wraps(func)
    def wrapper(
        self,
        *args,
        **kwargs,
    ):
        last_error = None

        for attempt in range(3):

            try:
                return func(
                    self,
                    *args,
                    **kwargs,
                )

            except Exception as exc:

                if not _is_retryable_supabase_error(
                    exc
                ):
                    raise

                last_error = exc

                print(
                    f"[Database] Supabase network/client "
                    f"error in {func.__name__}: {exc}. "
                    f"Reconnecting "
                    f"(attempt {attempt + 1}/3)..."
                )

                self._reconnect_supabase()

                if attempt < 2:
                    time.sleep(
                        0.5 * (2 ** attempt)
                    )

        if last_error is not None:
            raise last_error

        raise RuntimeError(
            f"Supabase operation "
            f"{func.__name__} failed unexpectedly."
        )

    return wrapper


# ============================================================
# DATABASE REPOSITORY
# ============================================================

class DatabaseRepository:
    """
    Persistent Supabase repository for LocateMe.

    Stores:
    - Missing persons
    - Face embeddings
    - CCTV jobs
    - Detection results
    - Alerts
    - Recognition settings
    """

    def __init__(self):

        self._lock = threading.Lock()

        self.supabase = None

        self.is_supabase_connected = False

        if (
            settings.SUPABASE_URL
            and settings.SUPABASE_KEY
        ):
            self._connect_supabase()

        if not self.is_supabase_connected:
            print(
                "[Database] WARNING: Supabase is not connected."
            )


    # ========================================================
    # SUPABASE CONNECTION
    # ========================================================

    def _connect_supabase(self):
        """Create a fresh Supabase client."""

        try:

            from supabase import create_client

            if (
                not settings.SUPABASE_URL
                or not settings.SUPABASE_KEY
            ):
                raise RuntimeError(
                    "SUPABASE_URL or SUPABASE_KEY is missing."
                )

            self.supabase = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY,
            )

            self.is_supabase_connected = True

            print(
                "[Database] Supabase connected successfully."
            )

        except Exception as exc:

            self.supabase = None

            self.is_supabase_connected = False

            print(
                f"[Database] Supabase connection failed: {exc}"
            )


    def _reconnect_supabase(self):
        """
        Rebuild the Supabase client after a transient
        connection failure.
        """

        self.supabase = None

        self.is_supabase_connected = False

        self._connect_supabase()


    # ========================================================
    # HELPERS
    # ========================================================

    def _require_supabase(self):

        if not self.supabase:
            raise RuntimeError(
                "Supabase is not connected. "
                "Check SUPABASE_URL and SUPABASE_KEY."
            )


    @staticmethod
    def _now():

        return datetime.now(
            timezone.utc
        ).isoformat()


    # ========================================================
    # VECTOR CONVERSION
    # ========================================================

    @staticmethod
    def _vector_to_db(
        embedding,
    ):
        """
        Convert a Python/numpy embedding into
        pgvector-compatible string format.
        """

        if embedding is None:
            return None

        if isinstance(
            embedding,
            str,
        ):
            return embedding

        return (
            "["
            + ",".join(
                str(float(x))
                for x in embedding
            )
            + "]"
        )


    @staticmethod
    def _vector_from_db(
        embedding,
    ):
        """
        Convert pgvector/string representation
        back into a Python list.
        """

        if embedding is None:
            return None

        if isinstance(
            embedding,
            list,
        ):
            return embedding

        if isinstance(
            embedding,
            str,
        ):

            value = embedding.strip()

            if (
                value.startswith("[")
                and value.endswith("]")
            ):

                value = value[1:-1]

                if not value.strip():
                    return []

                return [
                    float(x)
                    for x in value.split(",")
                ]

        return embedding


    @staticmethod
    def _is_uuid(
        value: str,
    ) -> bool:
        """Return True when value is a valid UUID string."""

        try:

            uuid.UUID(
                str(value)
            )

            return True

        except (
            ValueError,
            AttributeError,
            TypeError,
        ):
            return False


    # ============================================================
    # PERSON OPERATIONS
    # ============================================================

    @_with_supabase_retry
    def get_person_by_case_id(
        self,
        case_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Return a missing-person record by its unique case ID.
        """

        self._require_supabase()

        response = (
            self.supabase
            .table("missing_persons")
            .select("*")
            .eq(
                "case_id",
                case_id,
            )
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        person = response.data[0]

        person["embedding"] = (
            self._vector_from_db(
                person.get("embedding")
            )
        )

        return person


    # ========================================================
    # CREATE PERSON
    # ========================================================

    @_with_supabase_retry
    def create_person(
        self,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:

        self._require_supabase()

        with self._lock:

            person_id = (
                data.get("id")
                or str(uuid.uuid4())
            )

            case_id = data.get(
                "case_id"
            )

            if not case_id:

                case_id = (
                    f"MP-"
                    f"{datetime.utcnow().strftime('%y')}-"
                    f"{uuid.uuid4().hex[:4].upper()}"
                )

            now = self._now()

            # IMPORTANT:
            # The embedding generated during registration
            # MUST be included in this database record.

            embedding = data.get(
                "embedding"
            )

            record = {
                "id": person_id,

                "case_id": case_id,

                "name": data["name"],

                "age": data["age"],

                "gender": data["gender"],

                "height": data.get(
                    "height",
                    "Unknown",
                ),

                "missing_since": (
                    data.get(
                        "missing_since"
                    )
                    or datetime.utcnow().strftime(
                        "%Y-%m-%d"
                    )
                ),

                "last_known_location": (
                    data.get(
                        "last_known_location"
                    )
                    or "Unknown"
                ),

                "notes": data.get(
                    "notes"
                ),

                "photo_url": data.get(
                    "photo_url"
                ),

                "status": (
                    data.get(
                        "status"
                    )
                    or "active_alert"
                ),

                # ============================================
                # FACE EMBEDDING
                # ============================================

                "embedding": (
                    self._vector_to_db(
                        embedding
                    )
                ),

                "created_at": now,

                "updated_at": now,
            }

            print(
                "[Database] Creating person "
                f"'{data['name']}' "
                f"with embedding: "
                f"{embedding is not None}"
            )

            response = (
                self.supabase
                .table("missing_persons")
                .insert(record)
                .execute()
            )

            if not response.data:

                raise RuntimeError(
                    "Failed to create missing person."
                )

            result = response.data[0]

            result["embedding"] = (
                self._vector_from_db(
                    result.get(
                        "embedding"
                    )
                )
            )

            print(
                "[Database] Person created successfully: "
                f"{result.get('name')} | "
                f"has_embedding="
                f"{result.get('embedding') is not None}"
            )

            return result


    # ========================================================
    # GET PERSONS
    # ========================================================

    @_with_supabase_retry
    def get_persons(
        self,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:

        self._require_supabase()

        query = (
            self.supabase
            .table("missing_persons")
            .select("*")
        )

        if (
            status
            and status != "all"
        ):

            query = query.eq(
                "status",
                status,
            )

        response = (
            query
            .execute()
        )

        items = (
            response.data
            or []
        )

        for person in items:

            person["embedding"] = (
                self._vector_from_db(
                    person.get(
                        "embedding"
                    )
                )
            )

        if search:

            s = search.lower()

            items = [
                p
                for p in items
                if (
                    s
                    in str(
                        p.get(
                            "name",
                            "",
                        )
                    ).lower()

                    or s
                    in str(
                        p.get(
                            "case_id",
                            "",
                        )
                    ).lower()

                    or s
                    in str(
                        p.get(
                            "last_known_location",
                            "",
                        )
                    ).lower()
                )
            ]

        return sorted(
            items,
            key=lambda x:
                x.get(
                    "created_at",
                    "",
                ),
            reverse=True,
        )


    # ========================================================
    # GET SINGLE PERSON
    # ========================================================

    @_with_supabase_retry
    def get_person(
        self,
        person_id: str,
    ) -> Optional[Dict[str, Any]]:

        self._require_supabase()

        query = (
            self.supabase
            .table("missing_persons")
            .select("*")
        )

        # UUID id vs human-readable case ID

        if self._is_uuid(
            person_id
        ):

            query = query.eq(
                "id",
                person_id,
            )

        else:

            query = query.eq(
                "case_id",
                person_id,
            )

        response = (
            query
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        person = response.data[0]

        person["embedding"] = (
            self._vector_from_db(
                person.get(
                    "embedding"
                )
            )
        )

        return person


    # ========================================================
    # UPDATE PERSON STATUS
    # ========================================================

    @_with_supabase_retry
    def update_person_status(
        self,
        person_id: str,
        status: str,
    ) -> Optional[Dict[str, Any]]:

        self._require_supabase()

        person = self.get_person(
            person_id
        )

        if not person:
            return None

        response = (
            self.supabase
            .table("missing_persons")
            .update(
                {
                    "status": status,
                    "updated_at": self._now(),
                }
            )
            .eq(
                "id",
                person["id"],
            )
            .execute()
        )

        if not response.data:
            return None

        result = response.data[0]

        result["embedding"] = (
            self._vector_from_db(
                result.get(
                    "embedding"
                )
            )
        )

        return result


    # ========================================================
    # GET ACTIVE EMBEDDINGS
    # ========================================================

    @_with_supabase_retry
    def get_active_embeddings(
        self,
    ) -> List[Dict[str, Any]]:

        self._require_supabase()

        response = (
            self.supabase
            .table("missing_persons")
            .select("*")
            .neq(
                "status",
                "found_safe",
            )
            .not_.is_(
                "embedding",
                "null",
            )
            .execute()
        )

        items = (
            response.data
            or []
        )

        for person in items:

            person["embedding"] = (
                self._vector_from_db(
                    person.get(
                        "embedding"
                    )
                )
            )

        return items


    # ========================================================
    # DUPLICATE FACE CHECK
    # ========================================================

    @_with_supabase_retry
    def find_duplicate_person_by_embedding(
        self,
        embedding,
        threshold: float = 0.95,
    ) -> Optional[Dict[str, Any]]:
        """
        Find an existing active missing-person record
        whose face embedding is extremely similar.
        """

        if embedding is None:
            return None

        import numpy as np

        existing_people = (
            self.get_active_embeddings()
        )

        new_embedding = np.asarray(
            embedding,
            dtype=np.float32,
        ).reshape(-1)

        new_norm = np.linalg.norm(
            new_embedding
        )

        if new_norm == 0:
            return None

        for person in existing_people:

            existing_embedding = (
                person.get(
                    "embedding"
                )
            )

            if existing_embedding is None:
                continue

            existing_vector = np.asarray(
                existing_embedding,
                dtype=np.float32,
            ).reshape(-1)

            if (
                existing_vector.shape
                != new_embedding.shape
            ):
                continue

            existing_norm = np.linalg.norm(
                existing_vector
            )

            if existing_norm == 0:
                continue

            similarity = float(
                np.dot(
                    new_embedding,
                    existing_vector,
                )
                / (
                    new_norm
                    * existing_norm
                )
            )

            if similarity >= threshold:

                person[
                    "face_similarity"
                ] = similarity

                return person

        return None


    # ============================================================
    # CCTV JOB OPERATIONS
    # ============================================================

    def create_cctv_job(
        self,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:

        self._require_supabase()

        with self._lock:

            job_id = str(
                uuid.uuid4()
            )

            job_code = (
                f"JOB-"
                f"{datetime.utcnow().strftime('%y%m%d%H%M%S')}"
            )

            now = self._now()

            record = {
                "id": job_id,

                "job_code": job_code,

                "filename": data[
                    "filename"
                ],

                "video_url": data.get(
                    "video_url"
                ),

                "location": (
                    data.get(
                        "location"
                    )
                    or "Unspecified Location"
                ),

                "camera_id": (
                    data.get(
                        "camera_id"
                    )
                    or "CAM-AUTO-01"
                ),

                "capture_time": (
                    data.get(
                        "capture_time"
                    )
                    or now
                ),

                "status": "queued",

                "total_frames": 0,

                "processed_frames": 0,

                "faces_detected": 0,

                "matches_found": 0,

                "error_message": None,

                "created_at": now,

                "updated_at": now,
            }

            response = (
                self.supabase
                .table("cctv_jobs")
                .insert(record)
                .execute()
            )

            if not response.data:

                raise RuntimeError(
                    "Failed to create CCTV job."
                )

            return response.data[0]


    @_with_supabase_retry
    def get_cctv_jobs(
        self,
    ) -> List[Dict[str, Any]]:

        self._require_supabase()

        response = (
            self.supabase
            .table("cctv_jobs")
            .select("*")
            .order(
                "created_at",
                desc=True,
            )
            .execute()
        )

        return (
            response.data
            or []
        )


    @_with_supabase_retry
    def get_cctv_job(
        self,
        job_id: str,
    ) -> Optional[Dict[str, Any]]:

        self._require_supabase()

        query = (
            self.supabase
            .table("cctv_jobs")
            .select("*")
        )

        if self._is_uuid(
            job_id
        ):

            query = query.eq(
                "id",
                job_id,
            )

        else:

            query = query.eq(
                "job_code",
                job_id,
            )

        response = (
            query
            .limit(1)
            .execute()
        )

        return (
            response.data[0]
            if response.data
            else None
        )


    @_with_supabase_retry
    def update_cctv_job(
        self,
        job_id: str,
        updates: Dict[str, Any],
    ):

        self._require_supabase()

        job = self.get_cctv_job(
            job_id
        )

        if not job:
            return None

        updates = dict(
            updates
        )

        updates[
            "updated_at"
        ] = self._now()

        response = (
            self.supabase
            .table("cctv_jobs")
            .update(updates)
            .eq(
                "id",
                job["id"],
            )
            .execute()
        )

        return (
            response.data[0]
            if response.data
            else None
        )


    # ============================================================
    # DETECTION OPERATIONS
    # ============================================================

    def create_detection(
        self,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:

        self._require_supabase()

        with self._lock:

            det_id = str(
                uuid.uuid4()
            )

            det_code = (
                f"DET-"
                f"{datetime.utcnow().strftime('%y%m%d%H%M%S')}"
                f"-"
                f"{uuid.uuid4().hex[:3].upper()}"
            )

            now = self._now()

            record = {
                "id": det_id,

                "detection_code": det_code,

                "person_id": data[
                    "person_id"
                ],

                "cctv_job_id": data.get(
                    "cctv_job_id"
                ),

                "confidence": round(
                    float(
                        data["confidence"]
                    ),
                    2,
                ),

                "frame_url": data[
                    "frame_url"
                ],

                "location": data[
                    "location"
                ],

                "camera_id": data[
                    "camera_id"
                ],

                "detected_at": (
                    data.get(
                        "detected_at"
                    )
                    or now
                ),

                "verification_status": (
                    data.get(
                        "verification_status"
                    )
                    or "pending"
                ),

                "bounding_box": data.get(
                    "bounding_box"
                ),

                "created_at": now,
            }

            response = (
                self.supabase
                .table("detections")
                .insert(record)
                .execute()
            )

            if not response.data:

                raise RuntimeError(
                    "Failed to create detection."
                )

            result = response.data[0]

            person = self.get_person(
                data["person_id"]
            )

            if person:

                result[
                    "person_name"
                ] = person[
                    "name"
                ]

                result[
                    "person_photo"
                ] = person.get(
                    "photo_url"
                )

            return result


    @_with_supabase_retry
    def get_detections(
        self,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:

        self._require_supabase()

        query = (
            self.supabase
            .table("detections")
            .select("*")
        )

        if (
            status
            and status != "all"
        ):

            query = query.eq(
                "verification_status",
                status,
            )

        response = (
            query
            .order(
                "detected_at",
                desc=True,
            )
            .execute()
        )

        detections = (
            response.data
            or []
        )

        for detection in detections:

            person = self.get_person(
                detection[
                    "person_id"
                ]
            )

            if person:

                detection[
                    "person_name"
                ] = person[
                    "name"
                ]

                detection[
                    "person_photo"
                ] = person.get(
                    "photo_url"
                )

        return detections


    @_with_supabase_retry
    def update_detection_status(
        self,
        det_id: str,
        status: str,
    ) -> Optional[Dict[str, Any]]:

        self._require_supabase()

        allowed_statuses = {
            "pending",
            "verified",
            "rejected",
        }

        if status not in allowed_statuses:

            raise ValueError(
                f"Invalid detection status: {status}"
            )

        query = (
            self.supabase
            .table("detections")
            .select("*")
        )

        if self._is_uuid(
            det_id
        ):

            query = query.eq(
                "id",
                det_id,
            )

        else:

            query = query.eq(
                "detection_code",
                det_id,
            )

        response = (
            query
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        detection = response.data[0]

        update_response = (
            self.supabase
            .table("detections")
            .update(
                {
                    "verification_status": status,
                }
            )
            .eq(
                "id",
                detection["id"],
            )
            .execute()
        )

        return (
            update_response.data[0]
            if update_response.data
            else None
        )


    # ============================================================
    # ALERT OPERATIONS
    # ============================================================

    def create_alert(
        self,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:

        self._require_supabase()

        with self._lock:

            alert_id = str(
                uuid.uuid4()
            )

            alert_code = (
                f"AL-"
                f"{datetime.utcnow().strftime('%y%m%d%H%M%S')}"
                f"-"
                f"{uuid.uuid4().hex[:3].upper()}"
            )

            now = self._now()

            record = {
                "id": alert_id,

                "alert_code": alert_code,

                "detection_id": data.get(
                    "detection_id"
                ),

                "case_id": data[
                    "case_id"
                ],

                "title": data[
                    "title"
                ],

                "detail": data[
                    "detail"
                ],

                "severity": data.get(
                    "severity",
                    "critical",
                ),

                "is_read": False,

                "created_at": now,
            }

            response = (
                self.supabase
                .table("alerts")
                .insert(record)
                .execute()
            )

            if not response.data:

                raise RuntimeError(
                    "Failed to create alert."
                )

            return response.data[0]


    @_with_supabase_retry
    def get_alerts(
        self,
    ) -> List[Dict[str, Any]]:

        self._require_supabase()

        response = (
            self.supabase
            .table("alerts")
            .select("*")
            .order(
                "created_at",
                desc=True,
            )
            .execute()
        )

        return (
            response.data
            or []
        )


    @_with_supabase_retry
    def mark_alert_read(
        self,
        alert_id: str,
    ) -> bool:

        self._require_supabase()

        query = (
            self.supabase
            .table("alerts")
            .select("id")
        )

        if self._is_uuid(
            alert_id
        ):

            query = query.eq(
                "id",
                alert_id,
            )

        else:

            query = query.eq(
                "alert_code",
                alert_id,
            )

        response = (
            query
            .limit(1)
            .execute()
        )

        if not response.data:
            return False

        real_id = response.data[0][
            "id"
        ]

        update_response = (
            self.supabase
            .table("alerts")
            .update(
                {
                    "is_read": True,
                }
            )
            .eq(
                "id",
                real_id,
            )
            .execute()
        )

        return bool(
            update_response.data
        )


    # ============================================================
    # SETTINGS
    # ============================================================

    @_with_supabase_retry
    def get_settings(
        self,
    ) -> Dict[str, Any]:

        self._require_supabase()

        response = (
            self.supabase
            .table("system_settings")
            .select("value")
            .eq(
                "key",
                "recognition",
            )
            .limit(1)
            .execute()
        )

        if not response.data:

            return {
                "similarity_threshold": 0.80,
                "alert_threshold": 0.90,
                "frame_sample_interval": (
                    settings.FRAME_SAMPLE_INTERVAL_SECONDS
                ),
            }

        recognition = (
            response.data[0].get(
                "value",
                {},
            )
        )

        return {
            "similarity_threshold": float(
                recognition.get(
                    "similarity_threshold",
                    0.80,
                )
            ),

            "alert_threshold": float(
                recognition.get(
                    "alert_threshold",
                    0.90,
                )
            ),

            "frame_sample_interval": (
                settings.FRAME_SAMPLE_INTERVAL_SECONDS
            ),
        }


    @_with_supabase_retry
    def update_settings(
        self,
        new_settings: Dict[str, Any],
    ) -> Dict[str, Any]:

        self._require_supabase()

        current = self.get_settings()

        current.update(
            new_settings
        )

        value = {
            "similarity_threshold": float(
                current.get(
                    "similarity_threshold",
                    0.80,
                )
            ),

            "alert_threshold": float(
                current.get(
                    "alert_threshold",
                    0.90,
                )
            ),
        }

        response = (
            self.supabase
            .table("system_settings")
            .upsert(
                {
                    "key": "recognition",
                    "value": value,
                    "updated_at": self._now(),
                }
            )
            .execute()
        )

        if not response.data:

            raise RuntimeError(
                "Failed to update system settings."
            )

        return self.get_settings()


# ================================================================
# GLOBAL DATABASE INSTANCE
# ================================================================

db = DatabaseRepository()