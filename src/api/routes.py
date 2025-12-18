"""API routes for the SyncFlow dashboard."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.config import settings
from src.services.sync import sync_service, SyncStatus

router = APIRouter(prefix="/api")


class SyncResponse(BaseModel):
    """Response model for sync operations."""
    status: str
    message: str
    data: dict | None = None


class ConfigUpdate(BaseModel):
    """Request model for config updates."""
    sync_schedule: str | None = None
    conflict_strategy: str | None = None


@router.get("/status")
async def get_status() -> SyncResponse:
    """Get the current sync status."""
    last_result = sync_service.last_result

    if last_result is None:
        return SyncResponse(
            status="idle",
            message="No sync has been run yet",
            data=None,
        )

    return SyncResponse(
        status=last_result.status.value,
        message=f"Last sync: {last_result.status.value}",
        data=last_result.to_dict(),
    )


@router.get("/history")
async def get_history() -> SyncResponse:
    """Get sync history."""
    history = sync_service.history

    return SyncResponse(
        status="success",
        message=f"Retrieved {len(history)} sync records",
        data={"history": history},
    )


@router.post("/sync")
async def trigger_sync() -> SyncResponse:
    """Trigger a manual sync."""
    # Check if sync is already running
    if (sync_service.last_result and
        sync_service.last_result.status == SyncStatus.RUNNING):
        raise HTTPException(
            status_code=409,
            detail="A sync is already in progress"
        )

    result = sync_service.run_sync()

    return SyncResponse(
        status=result.status.value,
        message=f"Sync completed with status: {result.status.value}",
        data=result.to_dict(),
    )


@router.get("/config")
async def get_config() -> SyncResponse:
    """Get current configuration (non-sensitive)."""
    return SyncResponse(
        status="success",
        message="Configuration retrieved",
        data={
            "demo_mode": settings.demo_mode,
            "sync_schedule": settings.sync_schedule,
            "conflict_strategy": settings.conflict_strategy,
            "sf_configured": bool(settings.sf_username),
            "jira_configured": bool(settings.jira_url),
            "sheets_configured": bool(settings.google_spreadsheet_id),
        },
    )


@router.put("/config")
async def update_config(update: ConfigUpdate) -> SyncResponse:
    """Update configuration (limited fields)."""
    # In a real app, this would persist to a database or config file
    # For demo purposes, we just acknowledge the request
    return SyncResponse(
        status="success",
        message="Configuration updated (note: changes are not persisted in demo mode)",
        data={
            "sync_schedule": update.sync_schedule or settings.sync_schedule,
            "conflict_strategy": update.conflict_strategy or settings.conflict_strategy,
        },
    )
