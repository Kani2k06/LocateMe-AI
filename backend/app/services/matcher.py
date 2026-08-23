from typing import List, Dict, Any, Optional
from datetime import datetime

import numpy as np

from app.core.database import db


class MatcherService:
    """
    Face matching service.

    Compares a detected FaceNet embedding against the
    embeddings of active missing persons stored in Supabase.

    Creates:
        - Detection records
        - Operator alerts

    Duplicate protection:
        1. Prevents duplicate detections inside the same CCTV job.
        2. Prevents new detections for a person who already has
           a pending or verified detection from an earlier job.
        3. Allows a new detection after an earlier detection
           has been rejected.
    """

    # ---------------------------------------------------------
    # COSINE SIMILARITY
    # ---------------------------------------------------------

    @staticmethod
    def compute_cosine_similarity(
        vec_a: List[float],
        vec_b: List[float],
    ) -> float:
        """
        Calculate cosine similarity between two vectors.

        FaceNet embeddings are L2-normalized, but we normalize
        again for safety.
        """

        if not vec_a or not vec_b:
            return 0.0

        if len(vec_a) != len(vec_b):
            print(
                "[Matcher] Embedding dimension mismatch: "
                f"{len(vec_a)} vs {len(vec_b)}"
            )
            return 0.0

        try:
            a = np.asarray(
                vec_a,
                dtype=np.float32,
            )

            b = np.asarray(
                vec_b,
                dtype=np.float32,
            )

            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)

            if norm_a < 1e-6 or norm_b < 1e-6:
                return 0.0

            similarity = float(
                np.dot(a, b)
                / (norm_a * norm_b)
            )

            # Keep similarity inside [0, 1]
            similarity = max(
                0.0,
                min(1.0, similarity),
            )

            return similarity

        except Exception as exc:
            print(
                f"[Matcher] Cosine similarity error: {exc}"
            )
            return 0.0

    # ---------------------------------------------------------
    # TIMESTAMP NORMALIZATION
    # ---------------------------------------------------------

    @staticmethod
    def normalize_timestamp(
        timestamp: Optional[str],
    ) -> Optional[str]:
        """
        Converts incoming timestamps into a PostgreSQL-safe
        ISO-8601 timestamp.
        """

        if not timestamp:
            return None

        try:
            value = str(timestamp).strip()

            # 2026-08-22T00:00:00+00:00Z
            if value.endswith("Z") and "+" in value:
                value = value[:-1]

            # 2026-08-22T00:00:00Z
            elif value.endswith("Z"):
                value = value[:-1] + "+00:00"

            parsed = datetime.fromisoformat(value)

            return parsed.isoformat()

        except Exception as exc:
            print(
                f"[Matcher] Timestamp normalization failed: "
                f"{timestamp} | {exc}"
            )

            return None

    # ---------------------------------------------------------
    # EXISTING DETECTION - SAME JOB
    # ---------------------------------------------------------

    def _find_existing_detection(
        self,
        person_id: str,
        cctv_job_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Prevents the same person from generating multiple
        detection cards from different frames of the same
        CCTV job.
        """

        try:
            detections = db.get_detections()

            if not detections:
                return None

            target_person_id = str(person_id)
            target_job_id = str(cctv_job_id)

            for detection in detections:

                detection_person_id = str(
                    detection.get(
                        "person_id",
                        "",
                    )
                )

                detection_job_id = str(
                    detection.get(
                        "cctv_job_id",
                        "",
                    )
                )

                if (
                    detection_person_id
                    == target_person_id
                    and detection_job_id
                    == target_job_id
                ):
                    return detection

            return None

        except Exception as exc:
            print(
                f"[Matcher] Existing detection lookup failed: "
                f"{exc}"
            )

            return None

    # ---------------------------------------------------------
    # EXISTING ACTIVE DETECTION - ALL JOBS
    # ---------------------------------------------------------

    def _find_existing_active_detection(
        self,
        person_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Finds an existing pending or verified detection for
        the same missing person.

        Rejected detections are ignored so that the person can
        be matched again in a future CCTV job.
        """

        try:
            detections = db.get_detections()

            if not detections:
                return None

            target_person_id = str(person_id)

            active_detections = []

            for detection in detections:

                detection_person_id = str(
                    detection.get(
                        "person_id",
                        "",
                    )
                )

                if detection_person_id != target_person_id:
                    continue

                status = str(
                    detection.get(
                        "verification_status",
                        "pending",
                    )
                ).lower()

                if status in {
                    "pending",
                    "verified",
                }:
                    active_detections.append(
                        detection
                    )

            if not active_detections:
                return None

            # get_detections() is already ordered newest first.
            return active_detections[0]

        except Exception as exc:
            print(
                f"[Matcher] Active detection lookup failed: "
                f"{exc}"
            )

            return None

    # ---------------------------------------------------------
    # MATCH DETECTED FACE
    # ---------------------------------------------------------

    def evaluate_detected_faces(
        self,
        detected_embedding: List[float],
        active_persons: List[Dict[str, Any]],
        frame_url: str,
        location: str,
        camera_id: str,
        detected_at: str,
        cctv_job_id: str,
        bbox: Optional[Dict[str, int]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Compare one detected CCTV face against ALL active persons
        and return every match above the configured threshold.
        """

        if not detected_embedding or not active_persons:
            return []

        matches = []

        for person in active_persons:

            person_id = person.get("id")

            if not person_id:
                continue

            # Avoid duplicate detection in same CCTV job.
            if self._find_existing_detection(
                person_id=person_id,
                cctv_job_id=cctv_job_id,
            ):
                continue

            # Avoid duplicate pending/verified detections
            # from previous jobs.
            if self._find_existing_active_detection(
                person_id=person_id,
            ):
                continue

            detection = self._evaluate_single_match(
                detected_embedding=detected_embedding,
                active_persons=[person],
                frame_url=frame_url,
                location=location,
                camera_id=camera_id,
                detected_at=detected_at,
                cctv_job_id=cctv_job_id,
                bbox=bbox,
            )

            if detection:
                matches.append(detection)

        return matches

    # ---------------------------------------------------------
    # LEGACY API
    # ---------------------------------------------------------

    def evaluate_detected_face(
        self,
        detected_embedding: List[float],
        active_persons: List[Dict[str, Any]],
        frame_url: str,
        location: str,
        camera_id: str,
        detected_at: str,
        cctv_job_id: str,
        bbox: Optional[Dict[str, int]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Legacy single-best-match API kept for compatibility.
        """

        return self._evaluate_single_match(
            detected_embedding=detected_embedding,
            active_persons=active_persons,
            frame_url=frame_url,
            location=location,
            camera_id=camera_id,
            detected_at=detected_at,
            cctv_job_id=cctv_job_id,
            bbox=bbox,
        )

    # ---------------------------------------------------------
    # SINGLE MATCH EVALUATION
    # ---------------------------------------------------------

    def _evaluate_single_match(
        self,
        detected_embedding: List[float],
        active_persons: List[Dict[str, Any]],
        frame_url: str,
        location: str,
        camera_id: str,
        detected_at: str,
        cctv_job_id: str,
        bbox: Optional[Dict[str, int]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Compare one detected CCTV face against all active
        missing persons.

        IMPORTANT:
        This version logs every similarity score so we can
        diagnose why a CCTV face is or is not being matched.
        """

        # -----------------------------------------------------
        # VALIDATION
        # -----------------------------------------------------

        if not detected_embedding:
            print(
                "[Matcher] Empty detected embedding."
            )
            return None

        if not active_persons:
            print(
                "[Matcher] No active persons available."
            )
            return None

        # FaceNet must return 512 dimensions.
        if len(detected_embedding) != 512:
            print(
                "[Matcher] Invalid detected embedding dimension:",
                len(detected_embedding),
            )
            return None

        # -----------------------------------------------------
        # LOAD SETTINGS
        # -----------------------------------------------------

        try:
            settings_data = db.get_settings()

        except Exception as exc:
            print(
                f"[Matcher] Could not load settings: {exc}"
            )
            settings_data = {}

        try:
            similarity_threshold = float(
                settings_data.get(
                    "similarity_threshold",
                    0.80,
                )
            )

        except (
            TypeError,
            ValueError,
        ):
            similarity_threshold = 0.80

        try:
            alert_threshold = float(
                settings_data.get(
                    "alert_threshold",
                    0.90,
                )
            )

        except (
            TypeError,
            ValueError,
        ):
            alert_threshold = 0.90

        # Safety bounds.
        similarity_threshold = max(
            0.0,
            min(
                1.0,
                similarity_threshold,
            ),
        )

        alert_threshold = max(
            similarity_threshold,
            min(
                1.0,
                alert_threshold,
            ),
        )

        print(
            "[Matcher] Similarity threshold: "
            f"{similarity_threshold:.4f} "
            f"({similarity_threshold * 100:.2f}%)"
        )

        print(
            "[Matcher] Alert threshold: "
            f"{alert_threshold:.4f} "
            f"({alert_threshold * 100:.2f}%)"
        )

        # -----------------------------------------------------
        # FIND BEST MATCH
        # -----------------------------------------------------

        best_match_person = None
        best_score = 0.0

        print(
            "[Matcher] Comparing CCTV face against "
            f"{len(active_persons)} active persons..."
        )

        for person in active_persons:

            person_name = person.get(
                "name",
                "Unknown",
            )

            person_id = person.get(
                "id"
            )

            person_embedding = person.get(
                "embedding"
            )

            # -------------------------------------------------
            # EMBEDDING VALIDATION
            # -------------------------------------------------

            if not person_embedding:

                print(
                    f"[Matcher] SKIP {person_name}: "
                    "no embedding stored."
                )

                continue

            if len(person_embedding) != 512:

                print(
                    f"[Matcher] SKIP {person_name}: "
                    f"invalid embedding dimension "
                    f"{len(person_embedding)}."
                )

                continue

            # -------------------------------------------------
            # CALCULATE SIMILARITY
            # -------------------------------------------------

            score = self.compute_cosine_similarity(
                detected_embedding,
                person_embedding,
            )

            # -------------------------------------------------
            # DEBUG OUTPUT
            # -------------------------------------------------

            print(
                f"[Matcher] Similarity: "
                f"{person_name} "
                f"(ID: {person_id}) = "
                f"{score:.4f} "
                f"({score * 100:.2f}%)"
            )

            # -------------------------------------------------
            # BEST MATCH
            # -------------------------------------------------

            if score > best_score:

                best_score = score

                best_match_person = person

        # -----------------------------------------------------
        # BEST MATCH DEBUG
        # -----------------------------------------------------

        if best_match_person:

            print(
                "[Matcher] BEST MATCH: "
                f"{best_match_person.get('name', 'Unknown')} "
                f"= {best_score:.4f} "
                f"({best_score * 100:.2f}%)"
            )

        else:

            print(
                "[Matcher] No valid person embedding "
                "was available for comparison."
            )

        print(
            "[Matcher] Required threshold: "
            f"{similarity_threshold:.4f} "
            f"({similarity_threshold * 100:.2f}%)"
        )

        # -----------------------------------------------------
        # NO MATCH
        # -----------------------------------------------------

        if (
            best_match_person is None
            or best_score < similarity_threshold
        ):

            if best_match_person:

                print(
                    "[Matcher] NO MATCH: "
                    f"best score "
                    f"{best_score:.4f} "
                    f"is below threshold "
                    f"{similarity_threshold:.4f}."
                )

            return None

        # -----------------------------------------------------
        # MATCH ACCEPTED
        # -----------------------------------------------------

        person_id = best_match_person.get(
            "id"
        )

        if not person_id:
            return None

        person_name = best_match_person.get(
            "name",
            "Unknown",
        )

        print(
            "[Matcher] MATCH THRESHOLD PASSED: "
            f"{person_name} "
            f"{best_score * 100:.2f}%"
        )

        # -----------------------------------------------------
        # PREVENT DUPLICATE - SAME JOB
        # -----------------------------------------------------

        existing_detection = (
            self._find_existing_detection(
                person_id=person_id,
                cctv_job_id=cctv_job_id,
            )
        )

        if existing_detection:

            print(
                f"[Matcher] Duplicate prevented: "
                f"{person_name} already matched "
                f"in job {str(cctv_job_id)[:8]}"
            )

            return existing_detection

        # -----------------------------------------------------
        # PREVENT DUPLICATE - PREVIOUS JOBS
        # -----------------------------------------------------

        existing_active_detection = (
            self._find_existing_active_detection(
                person_id=person_id,
            )
        )

        if existing_active_detection:

            existing_status = str(
                existing_active_detection.get(
                    "verification_status",
                    "pending",
                )
            ).lower()

            existing_job = str(
                existing_active_detection.get(
                    "cctv_job_id",
                    "",
                )
            )

            print(
                f"[Matcher] Cross-job duplicate prevented: "
                f"{person_name} already has "
                f"{existing_status} detection "
                f"from job {existing_job[:8]}"
            )

            return existing_active_detection

        # -----------------------------------------------------
        # CONFIDENCE
        # -----------------------------------------------------

        confidence = float(
            max(
                0.0,
                min(
                    1.0,
                    best_score,
                ),
            )
        )

        percentage = int(
            round(
                confidence * 100
            )
        )

        # -----------------------------------------------------
        # NORMALIZE TIMESTAMP
        # -----------------------------------------------------

        normalized_detected_at = (
            self.normalize_timestamp(
                detected_at
            )
        )

        if normalized_detected_at is None:

            print(
                "[Matcher] Invalid detected timestamp. "
                "Using current UTC time."
            )

            normalized_detected_at = (
                datetime.utcnow().isoformat()
            )

        # -----------------------------------------------------
        # CREATE DETECTION
        # -----------------------------------------------------

        detection_data = {
            "person_id": person_id,

            "person_name": person_name,

            "person_photo": (
                best_match_person.get(
                    "photo_url"
                )
            ),

            "cctv_job_id": cctv_job_id,

            "confidence": confidence,

            "frame_url": frame_url,

            "location": location,

            "camera_id": camera_id,

            "detected_at": normalized_detected_at,

            "verification_status": "pending",

            "bounding_box": bbox,
        }

        try:

            detection_record = (
                db.create_detection(
                    detection_data
                )
            )

        except Exception as exc:

            print(
                f"[Matcher] Failed to create detection: "
                f"{exc}"
            )

            raise

        if not detection_record:
            return None

        print(
            "[Matcher] MATCH FOUND: "
            f"{person_name} — "
            f"{percentage}%"
        )

        # -----------------------------------------------------
        # CREATE ALERT
        # -----------------------------------------------------

        if confidence >= alert_threshold:

            alert_data = {
                "detection_id": (
                    detection_record["id"]
                ),

                "case_id": (
                    best_match_person[
                        "case_id"
                    ]
                ),

                "title": (
                    "High-confidence match"
                ),

                "detail": (
                    f"{person_name} — "
                    f"{percentage}% at "
                    f"{location} "
                    f"({camera_id})."
                ),

                "severity": "critical",
            }

            try:

                db.create_alert(
                    alert_data
                )

                print(
                    "[Matcher] CRITICAL ALERT CREATED: "
                    f"{person_name} — "
                    f"{percentage}%"
                )

            except Exception as exc:

                # Detection already exists, so alert failure
                # should not destroy the result.

                print(
                    f"[Matcher] Alert creation failed: "
                    f"{exc}"
                )

        else:

            alert_data = {
                "detection_id": (
                    detection_record["id"]
                ),

                "case_id": (
                    best_match_person[
                        "case_id"
                    ]
                ),

                "title": (
                    "Pending verification"
                ),

                "detail": (
                    f"{person_name} — "
                    f"{percentage}% at "
                    f"{location}."
                ),

                "severity": "high",
            }

            try:

                db.create_alert(
                    alert_data
                )

                print(
                    "[Matcher] VERIFICATION ALERT CREATED: "
                    f"{person_name} — "
                    f"{percentage}%"
                )

            except Exception as exc:

                print(
                    f"[Matcher] Alert creation failed: "
                    f"{exc}"
                )

        # -----------------------------------------------------
        # RETURN DETECTION
        # -----------------------------------------------------

        return detection_record


# -------------------------------------------------------------
# GLOBAL MATCHER INSTANCE
# -------------------------------------------------------------

matcher = MatcherService()