from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.flight import FlightSearchRequest, FlightOffer
from app.models.user import User
from app.db.database import get_db
from app.core.dependencies import get_current_active_user_optional, get_current_active_user
from app.services.flight_service import search_flights, get_flight_searches

router = APIRouter(prefix="/flights", tags=["flights"])


@router.post("/search")
async def search_for_flights(
    search_request: FlightSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_active_user_optional),
):
    """
    Search for flights using Amadeus API.
    Authentication is optional - if authenticated, search history will be saved.
    """
    user_id = current_user.id if current_user else None
    result = await search_flights(db, search_request, user_id)
    
    return {
        "offers": result["offers"],
        "search_id": result.get("search_id")
    }


@router.get("/searches")
async def get_search_history(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get flight search history for current user."""
    searches = await get_flight_searches(db, current_user.id, skip, limit)
    
    return [
        {
            "id": str(s.id),
            "origin": s.origin,
            "destination": s.destination,
            "depart_date": s.depart_date,
            "return_date": s.return_date,
            "adults": s.adults,
            "travel_class": s.travel_class,
            "created_at": s.created_at
        }
        for s in searches
    ]
