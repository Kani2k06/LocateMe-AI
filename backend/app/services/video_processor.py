from datetime import datetime, timedelta, timezone
import gc

import cv2

from app.core.database import db
from app.core.storage import storage
from app.services.face_engine import face_engine
from app.services.matcher import matcher


class VideoProcessorService:
    """
    Background worker for CCTV video processing.

    Processing pipeline:

    1. Open CCTV video
    2. Extract sampled frames
    3. Detect faces using MTCNN
    4. Generate 512-dimensional FaceNet embeddings
    5. Match faces against active missing persons
    6. Save detection results to Supabase
    7. Create alerts for matches
    8. Mark CCTV job as complete / failed

    Memory optimized for low-memory deployment environments.
    """

    # ---------------------------------------------------------
    # TIMESTAMP HELPER
    # ---------------------------------------------------------

    @staticmethod
    def _format_timestamp(dt: datetime) -> str:
        """
        Convert datetime to PostgreSQL-safe UTC timestamp.

        Returns:
            2026-08-22T00:00:00Z
        """

        if dt.tzinfo is None:
            dt = dt.replace(
                tzinfo=timezone.utc
            )

        dt = dt.astimezone(
            timezone.utc
        )

        return dt.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

    # ---------------------------------------------------------
    # PROCESS CCTV VIDEO
    # ---------------------------------------------------------

    def process_cctv_video(
        self,
        job_id: str,
        video_path: str,
        location: str,
        camera_id: str,
        capture_time_str: str,
    ):
        """
        Process a CCTV video in the background.
        """

        print(
            f"[VideoProcessor] Starting job {job_id[:8]}"
        )

        cap = None

        try:

            # -------------------------------------------------
            # JOB → EXTRACTING
            # -------------------------------------------------

            db.update_cctv_job(
                job_id,
                {
                    "status": "extracting"
                },
            )

            # -------------------------------------------------
            # OPEN VIDEO
            # -------------------------------------------------

            cap = cv2.VideoCapture(
                video_path
            )

            if not cap.isOpened():

                error_message = (
                    "Could not open video file."
                )

                db.update_cctv_job(
                    job_id,
                    {
                        "status": "failed",
                        "error_message":
                            error_message,
                    },
                )

                print(
                    f"[VideoProcessor] {error_message}"
                )

                return

            # -------------------------------------------------
            # VIDEO INFORMATION
            # -------------------------------------------------

            fps = cap.get(
                cv2.CAP_PROP_FPS
            )

            if not fps or fps <= 0:
                fps = 25.0

            total_frame_count = int(
                cap.get(
                    cv2.CAP_PROP_FRAME_COUNT
                )
            )

            if total_frame_count <= 0:
                total_frame_count = 0

            print(
                f"[VideoProcessor] FPS: {fps:.2f}"
            )

            print(
                "[VideoProcessor] Total frames: "
                f"{total_frame_count}"
            )

            # -------------------------------------------------
            # SAMPLING CONFIGURATION
            # -------------------------------------------------

            settings = db.get_settings()

            sample_interval_sec = float(
                settings.get(
                    "frame_sample_interval",
                    1.0,
                )
            )

            if sample_interval_sec <= 0:
                sample_interval_sec = 1.0

            sample_step_frames = max(
                1,
                int(
                    fps * sample_interval_sec
                ),
            )

            print(
                "[VideoProcessor] Sampling every "
                f"{sample_interval_sec:.2f} second(s)"
            )

            # -------------------------------------------------
            # UPDATE JOB FRAME COUNT
            # -------------------------------------------------

            db.update_cctv_job(
                job_id,
                {
                    "total_frames":
                        total_frame_count,
                    "processed_frames":
                        0,
                    "faces_detected":
                        0,
                    "matches_found":
                        0,
                    "status":
                        "extracting",
                },
            )

            # -------------------------------------------------
            # PARSE CAPTURE TIME
            # -------------------------------------------------

            try:

                capture_value = (
                    capture_time_str or ""
                ).strip()

                # Handle Z correctly.
                if capture_value.endswith(
                    "Z"
                ):

                    capture_value = (
                        capture_value[:-1]
                        + "+00:00"
                    )

                capture_dt = (
                    datetime.fromisoformat(
                        capture_value
                    )
                )

                if capture_dt.tzinfo is None:

                    capture_dt = (
                        capture_dt.replace(
                            tzinfo=timezone.utc
                        )
                    )

                capture_dt = (
                    capture_dt.astimezone(
                        timezone.utc
                    )
                )

            except Exception as exc:

                print(
                    "[VideoProcessor] Invalid capture "
                    f"time '{capture_time_str}': {exc}"
                )

                capture_dt = (
                    datetime.now(
                        timezone.utc
                    )
                )

            # -------------------------------------------------
            # LOAD ACTIVE PERSONS
            # -------------------------------------------------

            active_persons = (
                db.get_active_embeddings()
            )

            print(
                "[VideoProcessor] Active persons: "
                f"{len(active_persons)}"
            )

            # -------------------------------------------------
            # PROCESSING COUNTERS
            # -------------------------------------------------

            processed_frames = 0
            faces_detected_count = 0
            matches_found_count = 0

            frame_idx = 0

            # -------------------------------------------------
            # FRAME LOOP
            # -------------------------------------------------

            while True:

                ret, frame = cap.read()

                if not ret:
                    break

                # -------------------------------------------------
                # SAMPLE FRAME
                # -------------------------------------------------

                if (
                    frame_idx
                    % sample_step_frames
                    == 0
                ):

                    processed_frames += 1

                    # ---------------------------------------------
                    # UPDATE PROGRESS
                    # ---------------------------------------------

                    db.update_cctv_job(
                        job_id,
                        {
                            "processed_frames":
                                processed_frames,
                            "faces_detected":
                                faces_detected_count,
                            "matches_found":
                                matches_found_count,
                            "status":
                                (
                                    "matching"
                                    if processed_frames > 1
                                    else "extracting"
                                ),
                        },
                    )

                    # ---------------------------------------------
                    # LOG PROGRESS
                    # ---------------------------------------------

                    print(
                        "[VideoProcessor] Processing "
                        f"frame {frame_idx}/"
                        f"{total_frame_count}"
                    )

                    # ---------------------------------------------
                    # FACE DETECTION
                    # ---------------------------------------------

                    faces = (
                        face_engine.detect_faces(
                            frame
                        )
                    )

                    if not faces:

                        del faces

                        frame_idx += 1

                        # Release current frame.
                        del frame

                        gc.collect()

                        continue

                    faces_detected_count += len(
                        faces
                    )

                    # ---------------------------------------------
                    # FRAME TIMESTAMP
                    # ---------------------------------------------

                    frame_dt = (
                        capture_dt
                        + timedelta(
                            seconds=(
                                frame_idx / fps
                            )
                        )
                    )

                    frame_timestamp = (
                        self._format_timestamp(
                            frame_dt
                        )
                    )

                    # ---------------------------------------------
                    # PROCESS EACH FACE
                    # ---------------------------------------------

                    for (
                        x,
                        y,
                        w,
                        h,
                    ) in faces:

                        face_crop = None
                        embedding = None
                        annotated_frame = None
                        saved_frame_url = None
                        detection_results = None

                        try:

                            # -------------------------------------
                            # EXTRACT FACE
                            # -------------------------------------

                            face_crop = (
                                face_engine.extract_face_crop(
                                    frame,
                                    (
                                        x,
                                        y,
                                        w,
                                        h,
                                    ),
                                )
                            )

                            if (
                                face_crop is None
                                or face_crop.size == 0
                            ):
                                continue

                            print(
                                "[VideoProcessor] "
                                f"Generating embedding for "
                                f"frame {frame_idx}"
                            )

                            # -------------------------------------
                            # GENERATE EMBEDDING
                            # -------------------------------------

                            embedding = (
                                face_engine.generate_embedding(
                                    face_crop
                                )
                            )

                            print(
                                "[VideoProcessor] "
                                f"Embedding generated for "
                                f"frame {frame_idx}"
                            )

                            if (
                                not embedding
                                or len(embedding) != 512
                            ):
                                continue

                            # -------------------------------------
                            # ONLY MATCH IF ACTIVE PERSONS EXIST
                            # -------------------------------------

                            if not active_persons:
                                continue

                            # -------------------------------------
                            # SAVE ANNOTATED FRAME
                            # -------------------------------------

                            annotated_frame = (
                                frame.copy()
                            )

                            cv2.rectangle(
                                annotated_frame,
                                (x, y),
                                (
                                    x + w,
                                    y + h,
                                ),
                                (0, 32, 96),
                                2,
                            )

                            print(
                                "[VideoProcessor] "
                                f"Saving annotated frame "
                                f"{frame_idx}"
                            )

                            saved_frame_url = (
                                storage.save_frame(
                                    annotated_frame,
                                    f"job_{job_id[:6]}",
                                    frame_idx,
                                )
                            )

                            print(
                                "[VideoProcessor] "
                                f"Frame {frame_idx} saved: "
                                f"{saved_frame_url}"
                            )

                            # -------------------------------------
                            # RELEASE ANNOTATED FRAME
                            # -------------------------------------

                            del annotated_frame
                            annotated_frame = None

                            gc.collect()

                            # -------------------------------------
                            # MATCH FACE
                            # -------------------------------------

                            print(
                                "[VideoProcessor] "
                                "Starting face matching "
                                f"for frame {frame_idx}"
                            )

                            detection_results = (
                                matcher.evaluate_detected_faces(
                                    detected_embedding=
                                        embedding,
                                    active_persons=
                                        active_persons,
                                    frame_url=
                                        saved_frame_url,
                                    location=
                                        location,
                                    camera_id=
                                        camera_id,
                                    detected_at=
                                        frame_timestamp,
                                    cctv_job_id=
                                        job_id,
                                    bbox={
                                        "x": int(x),
                                        "y": int(y),
                                        "w": int(w),
                                        "h": int(h),
                                    },
                                )
                            )

                            print(
                                "[VideoProcessor] "
                                "Face matching finished "
                                f"for frame {frame_idx}"
                            )

                            # -------------------------------------
                            # HANDLE MATCHES
                            # -------------------------------------

                            if detection_results:

                                matches_found_count += (
                                    len(
                                        detection_results
                                    )
                                )

                                print(
                                    "[VideoProcessor] "
                                    f"{len(detection_results)} "
                                    "match(es) recorded."
                                )

                                db.update_cctv_job(
                                    job_id,
                                    {
                                        "faces_detected":
                                            faces_detected_count,
                                        "matches_found":
                                            matches_found_count,
                                    },
                                )

                        except Exception as face_exc:

                            print(
                                "[VideoProcessor] "
                                f"Face processing error "
                                f"on frame {frame_idx}: "
                                f"{face_exc}"
                            )

                        finally:

                            # -------------------------------------
                            # RELEASE TEMPORARY FACE OBJECTS
                            # -------------------------------------

                            if face_crop is not None:
                                del face_crop

                            if embedding is not None:
                                del embedding

                            if annotated_frame is not None:
                                del annotated_frame

                            if detection_results is not None:
                                del detection_results

                            if saved_frame_url is not None:
                                del saved_frame_url

                            gc.collect()

                            print(
                                "[VideoProcessor] "
                                "Memory cleanup completed "
                                f"for frame {frame_idx}"
                            )

                    # -------------------------------------------------
                    # RELEASE FACE DETECTION RESULTS
                    # -------------------------------------------------

                    del faces
                    gc.collect()

                # -------------------------------------------------
                # RELEASE CURRENT VIDEO FRAME
                # -------------------------------------------------

                del frame

                gc.collect()

                frame_idx += 1

            # -------------------------------------------------
            # RELEASE VIDEO
            # -------------------------------------------------

            cap.release()
            cap = None

            gc.collect()

            # -------------------------------------------------
            # JOB COMPLETE
            # -------------------------------------------------

            db.update_cctv_job(
                job_id,
                {
                    "status":
                        "complete",
                    "processed_frames":
                        processed_frames,
                    "faces_detected":
                        faces_detected_count,
                    "matches_found":
                        matches_found_count,
                    "error_message":
                        None,
                },
            )

            print(
                "[VideoProcessor] Job "
                f"{job_id[:8]} COMPLETE"
            )

            print(
                "[VideoProcessor] Frames processed: "
                f"{processed_frames}"
            )

            print(
                "[VideoProcessor] Faces detected: "
                f"{faces_detected_count}"
            )

            print(
                "[VideoProcessor] Matches found: "
                f"{matches_found_count}"
            )

        # -----------------------------------------------------
        # PROCESSING ERROR
        # -----------------------------------------------------

        except Exception as exc:

            error_message = str(exc)

            print(
                "[VideoProcessor] Processing error: "
                f"{error_message}"
            )

            try:

                db.update_cctv_job(
                    job_id,
                    {
                        "status":
                            "failed",
                        "error_message":
                            error_message,
                    },
                )

            except Exception as update_exc:

                print(
                    "[VideoProcessor] Failed to update "
                    "job failure status: "
                    f"{update_exc}"
                )

            raise

        # -----------------------------------------------------
        # ALWAYS RELEASE VIDEO
        # -----------------------------------------------------

        finally:

            if cap is not None:

                try:
                    cap.release()
                except Exception:
                    pass

            gc.collect()


# -------------------------------------------------------------
# GLOBAL INSTANCE
# -------------------------------------------------------------

video_processor = VideoProcessorService()