"""
Dashboard API Routes
====================
Endpoints for dashboard statistics and timeline data.
"""
from fastapi import APIRouter
from database import crud

router = APIRouter()


@router.get("/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard summary statistics."""
    return await crud.get_dashboard_stats()


@router.get("/dashboard/timeline")
async def get_traffic_timeline(hours: int = 24):
    """Get hourly traffic/attack counts for the timeline chart."""
    return await crud.get_traffic_timeline(hours=hours)


@router.get("/dashboard/attacks")
async def get_attack_distribution():
    """Get attack type distribution for the pie/donut chart."""
    distribution = await crud.get_attack_distribution()
    return {"distribution": distribution}
