from fastapi import APIRouter, HTTPException
from app.core.database import db
from app.schemas.alert import AlertListResponse, AlertResponse

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=AlertListResponse)
def list_alerts():
    """Lists operator alerts for high-confidence matches and verification events."""
    alerts = db.get_alerts()
    return {
        "total": len(alerts),
        "items": alerts
    }


@router.patch("/{alert_id}/read")
def mark_alert_read(alert_id: str):
    """Marks an alert as read/acknowledged."""
    ok = db.mark_alert_read(alert_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Alert not found.")
    return {"status": "success", "alert_id": alert_id, "is_read": True}
