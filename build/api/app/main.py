import asyncio
import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.api.v1.router import api_router
from app.crud.user import crud_user
from app.models.user import User
from app.services.cron import run_daily_receipt_generation

logger = logging.getLogger("uvicorn")


async def _try_bootstrap() -> None:
    async with AsyncSessionLocal() as db:
        existing = await crud_user.get_by_email(db, settings.ADMIN_EMAIL)
        if existing:
            logger.info("Admin user already exists (%s), skipping bootstrap.", settings.ADMIN_EMAIL)
            return
        admin = User(
            email=settings.ADMIN_EMAIL,
            passwordHash=hash_password(settings.ADMIN_PASSWORD),
            isAdmin=1,
            verified=1,
            name="Admin",
        )
        db.add(admin)
        await db.commit()
        logger.info("Admin user bootstrapped: %s", settings.ADMIN_EMAIL)


async def bootstrap_admin(max_retries: int = 15, delay: float = 2.0) -> None:
    """Create the admin user if missing, retrying while the DB is still booting."""
    for attempt in range(1, max_retries + 1):
        try:
            await _try_bootstrap()
            return
        except OperationalError as exc:
            logger.info("DB not ready (attempt %d/%d): %s", attempt, max_retries, exc.orig)
            await asyncio.sleep(delay)
        except Exception as exc:
            logger.warning("Admin bootstrap failed: %s", exc)
            return
    logger.warning("Admin bootstrap gave up after %d attempts", max_retries)


scheduler = AsyncIOScheduler(timezone="Europe/Paris")
scheduler.add_job(
    run_daily_receipt_generation,
    CronTrigger(hour=12, minute=24, timezone="Europe/Paris"),
    id="daily_receipt_generation",
    replace_existing=True,
    misfire_grace_time=3600,  # tolère jusqu'à 1h de retard (redémarrage du container)
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await bootstrap_admin()
    scheduler.start()
    logger.info("Scheduler démarré — génération quotidienne des quittances à 07h00")
    yield
    scheduler.shutdown()
    logger.info("Scheduler arrêté")


app = FastAPI(
    title="Rental Management API",
    version="1.0.0",
    description="Rental management backend — MySQL + FastAPI async.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Auth", "description": "Authentication (cookie-based)"},
        {"name": "Users"},
        {"name": "Owners"},
        {"name": "Places"},
        {"name": "PlacesUnits"},
        {"name": "PlacesUnitsRooms"},
        {"name": "Tenants"},
        {"name": "Rents"},
        {"name": "RentsFees"},
        {"name": "RentReceipts"},
        {"name": "RentReceiptsDetails"},
        {"name": "Dashboard"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    # Also accept any LAN/loopback origin (localhost, 127.x, 192.168.x.y, 10.x, 172.16-31.x)
    # on any port — covers Vite dev server reached from another machine on the LAN.
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Database integrity error", "error": str(exc.orig)},
    )


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
