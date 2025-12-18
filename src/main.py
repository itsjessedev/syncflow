"""SyncFlow - Main application entry point."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.api.routes import router as api_router
from src.config import settings
from src.services.sync import sync_service
from src.utils.email import send_sync_notification

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Scheduler for cron jobs
scheduler = AsyncIOScheduler()


async def scheduled_sync():
    """Run sync on schedule and send notification."""
    logger.info("Running scheduled sync...")
    result = sync_service.run_sync()
    send_sync_notification(result)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting SyncFlow...")
    logger.info(f"Demo mode: {settings.demo_mode}")

    # Parse cron schedule and start scheduler
    try:
        parts = settings.sync_schedule.split()
        if len(parts) == 5:
            trigger = CronTrigger(
                minute=parts[0],
                hour=parts[1],
                day=parts[2],
                month=parts[3],
                day_of_week=parts[4],
            )
            scheduler.add_job(scheduled_sync, trigger, id="sync_job")
            scheduler.start()
            logger.info(f"Scheduled sync: {settings.sync_schedule}")
    except Exception as e:
        logger.warning(f"Could not parse cron schedule: {e}")

    yield

    # Shutdown
    logger.info("Shutting down SyncFlow...")
    scheduler.shutdown(wait=False)


# Create FastAPI app
app = FastAPI(
    title="SyncFlow",
    description="Automated Salesforce + Jira to Google Sheets sync",
    version="1.0.0",
    lifespan=lifespan,
)

# Include API routes
app.include_router(api_router)

# Templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Render the main dashboard."""
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "demo_mode": settings.demo_mode,
            "schedule": settings.sync_schedule,
        },
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "demo_mode": settings.demo_mode}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
