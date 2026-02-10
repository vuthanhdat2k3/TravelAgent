from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
# Ensure app logs are shown
logging.getLogger("app").setLevel(logging.INFO)

from app.routes import (
    auth_route,
    user_route,
    passenger_route,
    flight_route,
    booking_route,
    payment_route,
    preference_route,
    calendar_route,
    google_calendar_route,
    chat_route,
    notification_route,
    admin_route,
    llm_route,
)

app = FastAPI(
    title="Travel Agent API",
    description="Flight booking API with multi-agent chatbot",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.APP_CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Travel Agent API", "version": "1.0.0"}


@app.on_event("startup")
async def startup_event():
    """Initialize agent tools with DB session factory and start background tasks."""
    from app.db.database import AsyncSessionLocal
    from app.agents.tools import set_db_session_factory
    from app.services.cache_cleanup_service import start_cleanup_task

    set_db_session_factory(AsyncSessionLocal)

    # Start periodic flight offer cache cleanup (every ~7 min)
    start_cleanup_task()


@app.on_event("shutdown")
async def shutdown_event():
    """Gracefully stop background tasks."""
    from app.services.cache_cleanup_service import stop_cleanup_task
    await stop_cleanup_task()


# Auth & User routes
app.include_router(auth_route.router)
app.include_router(user_route.router)

# Passenger routes
app.include_router(passenger_route.router)

# Flight routes
app.include_router(flight_route.router)

# Booking routes
app.include_router(booking_route.router)

# Payment routes
app.include_router(payment_route.router)

# User preference routes
app.include_router(preference_route.router)

# Calendar routes
app.include_router(calendar_route.router)
app.include_router(google_calendar_route.router)

# Chat routes
app.include_router(chat_route.router)

# Notification routes
app.include_router(notification_route.router)

# Admin routes
app.include_router(admin_route.router)

# LLM config routes
app.include_router(llm_route.router)
