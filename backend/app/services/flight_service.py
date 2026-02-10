from uuid import UUID, uuid4
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, Float
from fastapi import HTTPException, status
import hashlib
import json
import logging
from amadeus import ResponseError

from app.models.flight_search import FlightSearch
from app.models.flight_offer_cache import FlightOfferCache
from app.schemas.flight import FlightSearchRequest, FlightOffer
from app.core.amadeus_client import get_amadeus_client

logger = logging.getLogger(__name__)


async def search_flights(
    db: AsyncSession,
    search_request: FlightSearchRequest,
    user_id: UUID | None = None
) -> dict:
    """
    Search for flights using Amadeus API.
    Cache results and optionally save search history.
    """
    # Create search key for caching
    search_key = _create_search_key(search_request)
    
    # Check cache first
    cached_offers = await _get_cached_offers(db, search_key)
    if cached_offers:
        search_id = None
        if user_id:
            search_id = await _save_search_history(db, user_id, search_request)
        
        return {
            "offers": cached_offers,
            "search_id": search_id
        }
    
    # Call Amadeus API
    try:
        amadeus = get_amadeus_client()
        
        # Build search parameters
        search_params = {
            "originLocationCode": search_request.origin.upper(),
            "destinationLocationCode": search_request.destination.upper(),
            "departureDate": search_request.depart_date.isoformat(),
            "adults": search_request.adults,
            "travelClass": search_request.travel_class,
            "currencyCode": search_request.currency,
            "max": 10  # Limit results
        }
        
        # Add return date if round trip
        if search_request.return_date:
            search_params["returnDate"] = search_request.return_date.isoformat()
        
        # Make API call
        response = amadeus.shopping.flight_offers_search.get(**search_params)
        
        # Normalize Amadeus response to our schema
        offers = _normalize_amadeus_offers(response.data)
        
        # Cache offers
        if offers:
            await _cache_offers(db, search_key, offers)
        
        logger.info(f"Found {len(offers)} flight offers for {search_request.origin} -> {search_request.destination}")
        
    except ResponseError as error:
        logger.error(f"Amadeus API error: {error}")
        # Return empty offers on API error instead of failing
        offers = []
    except Exception as error:
        logger.error(f"Unexpected error in flight search: {error}")
        offers = []
    
    # Save search history if user is authenticated
    search_id = None
    if user_id:
        search_id = await _save_search_history(db, user_id, search_request)
    
    return {
        "offers": offers,
        "search_id": search_id
    }


async def get_flight_searches(
    db: AsyncSession,
    user_id: UUID,
    skip: int = 0,
    limit: int = 20
) -> list[FlightSearch]:
    """Get user's flight search history."""
    result = await db.execute(
        select(FlightSearch)
        .where(FlightSearch.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .order_by(FlightSearch.created_at.desc())
    )
    return list(result.scalars().all())


async def get_offer_by_flight_number(
    db: AsyncSession,
    flight_number: str,
    origin: str | None = None,
    destination: str | None = None,
    depart_date: str | None = None
) -> dict | None:
    """
    Get cached flight offer by flight number + route.
    
    Args:
        db: Database session
        flight_number: Flight number like "VJ145" or "VJ 145" (spaces will be removed)
        origin: Departure airport IATA code (e.g., HAN)
        destination: Arrival airport IATA code (e.g., SGN)
        depart_date: Departure date (YYYY-MM-DD)
    
    Returns:
        Offer dict or None if not found or expired
    
    Note:
        Flight number alone is not unique! VJ197 can fly multiple routes.
        Origin + Destination are REQUIRED to find the correct flight.
    """
    # Normalize flight number (remove spaces, uppercase)
    normalized_flight_number = flight_number.replace(" ", "").upper()
    
    # Query all cache entries with this flight number
    result = await db.execute(
        select(FlightOfferCache)
        .where(
            FlightOfferCache.flight_numbers.contains([normalized_flight_number]),
            FlightOfferCache.expires_at > datetime.utcnow()
        )
    )
    
    cache_items = result.scalars().all()
    
    if not cache_items:
        return None
    
    # Filter by origin/destination/date if provided
    matched_offers = []
    
    for cache_item in cache_items:
        offer = cache_item.payload
        segments = offer.get("segments", [])
        
        if not segments:
            continue
        
        # Check if first segment matches origin/destination
        first_segment = segments[0]
        
        # Match criteria
        origin_match = not origin or first_segment.get("origin") == origin.upper()
        dest_match = not destination or first_segment.get("destination") == destination.upper()
        
        # Date match (check departure_time)
        date_match = True
        if depart_date:
            dep_time = first_segment.get("departure_time", "")
            if dep_time:
                try:
                    dep_date = dep_time.split("T")[0]  # Extract YYYY-MM-DD
                    date_match = dep_date == depart_date
                except:
                    date_match = False
        
        if origin_match and dest_match and date_match:
            matched_offers.append((cache_item, offer))
    
    if not matched_offers:
        return None
    
    # Sort by price (cheapest first)
    matched_offers.sort(key=lambda x: x[1].get("total_price", float('inf')))
    
    return matched_offers[0][1]


def _create_search_key(search_request: FlightSearchRequest) -> str:
    """Create a hash key for caching based on search parameters."""
    key_data = {
        "origin": search_request.origin,
        "destination": search_request.destination,
        "depart_date": str(search_request.depart_date),
        "return_date": str(search_request.return_date) if search_request.return_date else None,
        "adults": search_request.adults,
        "travel_class": search_request.travel_class,
    }
    key_string = json.dumps(key_data, sort_keys=True)
    return hashlib.sha256(key_string.encode()).hexdigest()


async def _get_cached_offers(
    db: AsyncSession,
    search_key: str
) -> list[dict] | None:
    """Get cached flight offers if not expired."""
    result = await db.execute(
        select(FlightOfferCache)
        .where(
            FlightOfferCache.search_key == search_key,
            FlightOfferCache.expires_at > datetime.utcnow()
        )
    )
    cached_items = result.scalars().all()
    
    if not cached_items:
        return None
    
    return [item.payload for item in cached_items]


async def _cache_offers(
    db: AsyncSession,
    search_key: str,
    offers: list[dict]
) -> None:
    """Cache flight offers with expiration (15-30 minutes)."""
    # Delete old cache entries for this search_key to avoid duplicates
    await db.execute(
        FlightOfferCache.__table__.delete().where(
            FlightOfferCache.search_key == search_key
        )
    )
    
    expires_at = datetime.utcnow() + timedelta(minutes=30)
    
    for offer in offers:
        # Extract flight numbers from segments
        flight_numbers = []
        for segment in offer.get("segments", []):
            airline_code = segment.get("airline_code", "")
            flight_number = segment.get("flight_number", "")
            if airline_code and flight_number:
                # Format: VJ145, VN123, etc.
                flight_code = f"{airline_code}{flight_number}"
                if flight_code not in flight_numbers:
                    flight_numbers.append(flight_code)
        
        cache_item = FlightOfferCache(
            search_key=search_key,
            offer_id=offer.get("offer_id", str(uuid4())),
            payload=offer,
            flight_numbers=flight_numbers if flight_numbers else None,
            expires_at=expires_at
        )
        db.add(cache_item)
    
    await db.commit()


async def _save_search_history(
    db: AsyncSession,
    user_id: UUID,
    search_request: FlightSearchRequest
) -> UUID:
    """Save flight search to user's history."""
    search_record = FlightSearch(
        user_id=user_id,
        origin=search_request.origin,
        destination=search_request.destination,
        depart_date=search_request.depart_date,
        return_date=search_request.return_date,
        adults=search_request.adults,
        travel_class=search_request.travel_class,
    )
    
    db.add(search_record)
    await db.commit()
    await db.refresh(search_record)
    
    return search_record.id


def _normalize_amadeus_offers(amadeus_data: list) -> list[dict]:
    """
    Normalize Amadeus flight offers to our schema.
    
    Amadeus response structure:
    - data: list of flight offers
    - each offer has: id, itineraries, price, travelerPricings
    - each itinerary has: segments (array of flight segments)
    """
    normalized_offers = []
    
    for offer in amadeus_data:
        try:
            # Extract price information
            price_info = offer.get("price", {})
            total_price = float(price_info.get("total", 0))
            currency = price_info.get("currency", "USD")
            
            # Process itineraries (outbound + return if applicable)
            all_segments = []
            total_duration_minutes = 0
            
            for itinerary in offer.get("itineraries", []):
                # Parse duration (format: PT2H30M)
                duration_str = itinerary.get("duration", "PT0M")
                duration_minutes = _parse_duration(duration_str)
                total_duration_minutes += duration_minutes
                
                # Process segments
                for segment in itinerary.get("segments", []):
                    departure = segment.get("departure", {})
                    arrival = segment.get("arrival", {})
                    
                    normalized_segment = {
                        "origin": departure.get("iataCode", ""),
                        "destination": arrival.get("iataCode", ""),
                        "departure_time": departure.get("at", ""),
                        "arrival_time": arrival.get("at", ""),
                        "airline_code": segment.get("carrierCode", ""),
                        "flight_number": segment.get("number", ""),
                    }
                    all_segments.append(normalized_segment)
            
            # Calculate number of stops (segments - 1 per itinerary)
            # For simplicity, count total segments minus number of itineraries
            num_itineraries = len(offer.get("itineraries", []))
            total_segments = len(all_segments)
            stops = max(0, total_segments - num_itineraries)
            
            normalized_offer = {
                "offer_id": offer.get("id", str(uuid4())),
                "total_price": total_price,
                "currency": currency,
                "duration_minutes": total_duration_minutes,
                "stops": stops,
                "segments": all_segments,
            }
            
            normalized_offers.append(normalized_offer)
            
        except Exception as e:
            logger.warning(f"Failed to normalize offer: {e}")
            continue
    
    return normalized_offers


def _parse_duration(duration_str: str) -> int:
    """
    Parse ISO 8601 duration format (e.g., PT2H30M) to minutes.
    
    Args:
        duration_str: Duration in ISO 8601 format (PT2H30M)
        
    Returns:
        Total duration in minutes
    """
    import re
    
    # Remove PT prefix
    duration_str = duration_str.replace("PT", "")
    
    hours = 0
    minutes = 0
    
    # Extract hours
    hours_match = re.search(r'(\d+)H', duration_str)
    if hours_match:
        hours = int(hours_match.group(1))
    
    # Extract minutes
    minutes_match = re.search(r'(\d+)M', duration_str)
    if minutes_match:
        minutes = int(minutes_match.group(1))
    
    return hours * 60 + minutes
