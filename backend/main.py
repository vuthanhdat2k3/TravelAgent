from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

from app.routes import (
    auth_route,
    user_route,
    passenger_route,
    flight_route,
    booking_route,
    payment_route,
    preference_route,
    calendar_route,
    chat_route,
    notification_route,
    admin_route,
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

# Chat routes
app.include_router(chat_route.router)

# Notification routes
app.include_router(notification_route.router)

# Admin routes
app.include_router(admin_route.router)