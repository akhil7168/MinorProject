"""
Alerts API Routes
=================
Endpoints for alert management: listing, filtering, status updates.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from database import crud

router = APIRouter()


class AlertStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None


@router.get("/alerts")
async def list_alerts(
    severity: Optional[str] = None,
    status: Optional[str] = None,
    attack_type: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
):
    """Get alerts with optional filters."""
    alerts = await crud.get_alerts(
        severity=severity,
        status=status,
        attack_type=attack_type,
        limit=limit,
        page=page,
    )
    stats = await crud.get_alert_stats()

    return {
        "alerts": alerts,
        "stats": stats,
        "page": page,
        "limit": limit,
    }


@router.patch("/alerts/{alert_id}")
async def update_alert(alert_id: str, update: AlertStatusUpdate):
    """Update alert status (acknowledge, resolve, mark false positive)."""
    valid_statuses = {"open", "acknowledged", "resolved", "false_positive"}
    if update.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {valid_statuses}",
        )

    await crud.update_alert_status(alert_id, update.status, update.notes)
    return {"status": "updated", "alert_id": alert_id}


@router.get("/alerts/stats")
async def get_alert_statistics():
    """Get alert summary statistics."""
    stats = await crud.get_alert_stats()
    return stats
