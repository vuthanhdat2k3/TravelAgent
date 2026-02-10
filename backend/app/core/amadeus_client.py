from amadeus import Client, ResponseError
from app.core.config import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class AmadeusClient:
    """Singleton wrapper for Amadeus API client."""
    
    _instance: Optional[Client] = None
    
    @classmethod
    def get_client(cls) -> Client:
        """Get or create Amadeus client instance."""
        if cls._instance is None:
            if not settings.AMADEUS_CLIENT_ID or not settings.AMADEUS_CLIENT_SECRET:
                raise ValueError("Amadeus credentials not configured")
            
            # Determine if using production or test environment
            hostname = "production" if settings.AMADEUS_ENV == "production" else "test"
            
            cls._instance = Client(
                client_id=settings.AMADEUS_CLIENT_ID,
                client_secret=settings.AMADEUS_CLIENT_SECRET,
                hostname=hostname
            )
            logger.info(f"Amadeus client initialized in {hostname} mode")
        
        return cls._instance


def get_amadeus_client() -> Client:
    """Helper function to get Amadeus client."""
    return AmadeusClient.get_client()
