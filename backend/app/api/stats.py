from collections import Counter

from fastapi import APIRouter

from app.core.database import db
from app.schemas.stats import (
    DashboardStatsResponse,
    AnalyticsResponse,
)


router = APIRouter(tags=["Statistics & Analytics"])


# ============================================================
# DASHBOARD STATS
# ============================================================

@router.get(
    "/stats",
    response_model=DashboardStatsResponse,
)
def get_dashboard_stats():
    """
    Returns aggregated summary metrics for the Operations Dashboard.

    Uses Supabase-backed repository methods instead of old
    in-memory dictionaries.
    """

    # Fetch current data from Supabase
    persons = db.get_persons()
    detections = db.get_detections()
    alerts = db.get_alerts()
    jobs = db.get_cctv_jobs()

    # --------------------------------------------------------
    # Active cases
    # --------------------------------------------------------

    active_cases = sum(
        1
        for person in persons
        if person.get("status") == "active_alert"
    )

    # --------------------------------------------------------
    # Matches today
    # --------------------------------------------------------

    # The detections endpoint already returns detections
    # ordered by detected_at.
    matches_today = len(detections)

    # --------------------------------------------------------
    # Open alerts
    # --------------------------------------------------------

    open_alerts = sum(
        1
        for alert in alerts
        if not alert.get("is_read", False)
    )

    critical_alerts = sum(
        1
        for alert in alerts
        if alert.get("severity") == "critical"
        and not alert.get("is_read", False)
    )

    # --------------------------------------------------------
    # CCTV jobs
    # --------------------------------------------------------

    cctv_jobs = len(jobs)

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return {
        "stats": [
            {
                "label": "Active cases",
                "value": str(active_cases),
                "hint": "Currently active missing-person cases",
                "icon": "person_search",
            },
            {
                "label": "Matches today",
                "value": str(matches_today),
                "hint": "Detection results",
                "icon": "biotech",
            },
            {
                "label": "Open alerts",
                "value": str(open_alerts),
                "hint": f"{critical_alerts} critical",
                "icon": "notifications_active",
            },
            {
                "label": "CCTV jobs",
                "value": str(cctv_jobs),
                "hint": "Processing queue",
                "icon": "videocam",
            },
        ],
        "active_cases": active_cases,
        "matches_today": matches_today,
        "open_alerts": open_alerts,
        "cctv_jobs": cctv_jobs,
    }


# ============================================================
# ANALYTICS
# ============================================================

@router.get(
    "/analytics",
    response_model=AnalyticsResponse,
)
def get_analytics():
    """
    Returns analytical distributions and performance metrics.

    Values are calculated from the actual Supabase data.
    """

    # Fetch data from Supabase
    persons = db.get_persons()
    detections = db.get_detections()
    jobs = db.get_cctv_jobs()

    # --------------------------------------------------------
    # Person status distribution
    # --------------------------------------------------------

    status_counts = Counter(
        person.get("status", "active_alert")
        for person in persons
    )

    by_status = [
        {
            "label": "Active",
            "value": status_counts.get("active_alert", 0),
        },
        {
            "label": "Pending",
            "value": status_counts.get(
                "pending_verification",
                0,
            ),
        },
        {
            "label": "Resolved",
            "value": status_counts.get(
                "found_safe",
                0,
            ),
        },
    ]

    # --------------------------------------------------------
    # Location distribution
    # --------------------------------------------------------

    location_counts = Counter(
        person.get("last_known_location", "Unknown")
        for person in persons
    )

    # Keep the analytics response compact.
    # Show the top 5 locations.
    top_locations = location_counts.most_common(5)

    by_location = [
        {
            "label": str(location),
            "value": count,
        }
        for location, count in top_locations
    ]

    # If there is no data, provide an empty list.
    if not by_location:
        by_location = []

    # --------------------------------------------------------
    # Match rate
    # --------------------------------------------------------

    total_faces_detected = sum(
        int(job.get("faces_detected") or 0)
        for job in jobs
    )

    total_matches = sum(
        int(job.get("matches_found") or 0)
        for job in jobs
    )

    if total_faces_detected > 0:
        match_rate = (
            total_matches / total_faces_detected
        ) * 100

        match_rate_text = f"{match_rate:.1f}%"
    else:
        match_rate_text = "0%"

    # --------------------------------------------------------
    # Average confidence
    # --------------------------------------------------------

    confidence_values = []

    for detection in detections:
        confidence = detection.get("confidence")

        if confidence is not None:
            try:
                confidence_values.append(
                    float(confidence)
                )
            except (TypeError, ValueError):
                pass

    if confidence_values:
        avg_confidence = (
            sum(confidence_values)
            / len(confidence_values)
        ) * 100

        avg_confidence_text = (
            f"{avg_confidence:.0f}%"
        )
    else:
        avg_confidence_text = "0%"

    # --------------------------------------------------------
    # Cameras online
    # --------------------------------------------------------

    camera_ids = {
        job.get("camera_id")
        for job in jobs
        if job.get("camera_id")
    }

    cameras_online_text = (
        f"{len(camera_ids)} / {len(camera_ids)}"
        if camera_ids
        else "0 / 0"
    )

    # --------------------------------------------------------
    # Median time to match
    # --------------------------------------------------------

    # We do not currently have enough timestamp data in the
    # repository to calculate a reliable median processing
    # time, so do not invent a value.
    median_time_to_match = "N/A"

    # --------------------------------------------------------
    # Final analytics response
    # --------------------------------------------------------

    return {
        "match_rate": match_rate_text,
        "avg_confidence": avg_confidence_text,
        "median_time_to_match": median_time_to_match,
        "cameras_online": cameras_online_text,
        "by_status": by_status,
        "by_location": by_location,
    }