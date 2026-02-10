"""
Google Calendar API integration.
Handles OAuth flow and calendar event creation.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class GoogleCalendarClient:
    """Client for Google Calendar API operations."""

    SCOPES = ['https://www.googleapis.com/auth/calendar']

    def __init__(self, access_token: str, refresh_token: str, token_expiry: Optional[datetime] = None):
        """
        Initialize Google Calendar client with OAuth credentials.

        Args:
            access_token: Google OAuth access token
            refresh_token: Google OAuth refresh token
            token_expiry: Token expiration datetime
        """
        self.creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=None,  # Will be set from config
            client_secret=None,  # Will be set from config
            scopes=self.SCOPES
        )
        
        # Auto-refresh if expired
        if self.creds.expired and self.creds.refresh_token:
            try:
                self.creds.refresh(Request())
            except Exception as e:
                logger.error(f"Failed to refresh Google token: {e}")
                raise

        self.service = build('calendar', 'v3', credentials=self.creds)

    def create_flight_event(
        self,
        booking_reference: str,
        origin: str,
        destination: str,
        departure_time: datetime,
        arrival_time: datetime,
        airline_code: str,
        flight_number: str,
        passenger_name: str,
        calendar_id: str = 'primary'
    ) -> str:
        """
        Create a flight event in Google Calendar.

        Args:
            booking_reference: Booking reference code
            origin: Departure airport IATA code
            destination: Arrival airport IATA code
            departure_time: Flight departure datetime
            arrival_time: Flight arrival datetime
            airline_code: Airline IATA code
            flight_number: Flight number
            passenger_name: Passenger name
            calendar_id: Google Calendar ID (default: primary)

        Returns:
            Google Calendar event ID

        Raises:
            HttpError: If calendar API call fails
        """
        try:
            # Build event summary
            summary = f"✈️ Chuyến bay {airline_code}{flight_number}: {origin} → {destination}"
            
            # Build description
            description = f"""
🎫 Booking Reference: {booking_reference}
👤 Hành khách: {passenger_name}

🛫 Khởi hành: {origin}
🛬 Đến: {destination}
✈️ Chuyến bay: {airline_code} {flight_number}

⏱️ Giờ khởi hành: {departure_time.strftime('%d/%m/%Y %H:%M')}
⏱️ Giờ đến: {arrival_time.strftime('%d/%m/%Y %H:%M')}

Được tạo bởi Travel Agent AI
            """.strip()

            # Build event
            event = {
                'summary': summary,
                'description': description,
                'location': f"{origin} Airport",
                'start': {
                    'dateTime': departure_time.isoformat(),
                    'timeZone': 'Asia/Ho_Chi_Minh',  # TODO: Get from airport timezone
                },
                'end': {
                    'dateTime': arrival_time.isoformat(),
                    'timeZone': 'Asia/Ho_Chi_Minh',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 60 * 24},  # 1 day before
                        {'method': 'popup', 'minutes': 60 * 3},   # 3 hours before
                    ],
                },
                'colorId': '5',  # Yellow color for flights
            }

            # Create event
            created_event = self.service.events().insert(
                calendarId=calendar_id,
                body=event
            ).execute()

            logger.info(f"Created Google Calendar event: {created_event['id']}")
            return created_event['id']

        except HttpError as e:
            logger.error(f"Failed to create Google Calendar event: {e}")
            raise

    def delete_event(self, event_id: str, calendar_id: str = 'primary') -> None:
        """
        Delete an event from Google Calendar.

        Args:
            event_id: Google Calendar event ID
            calendar_id: Google Calendar ID (default: primary)

        Raises:
            HttpError: If calendar API call fails
        """
        try:
            self.service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            logger.info(f"Deleted Google Calendar event: {event_id}")
        except HttpError as e:
            logger.error(f"Failed to delete Google Calendar event: {e}")
            raise

    def update_event(
        self,
        event_id: str,
        calendar_id: str = 'primary',
        **event_updates
    ) -> str:
        """
        Update an existing calendar event.

        Args:
            event_id: Google Calendar event ID
            calendar_id: Google Calendar ID
            **event_updates: Fields to update

        Returns:
            Updated event ID

        Raises:
            HttpError: If calendar API call fails
        """
        try:
            # Get current event
            event = self.service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()

            # Update fields
            event.update(event_updates)

            # Update event
            updated_event = self.service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=event
            ).execute()

            logger.info(f"Updated Google Calendar event: {event_id}")
            return updated_event['id']

        except HttpError as e:
            logger.error(f"Failed to update Google Calendar event: {e}")
            raise


def get_google_calendar_client(
    access_token: str,
    refresh_token: str,
    token_expiry: Optional[datetime] = None
) -> GoogleCalendarClient:
    """
    Factory function to create GoogleCalendarClient instance.

    Args:
        access_token: Google OAuth access token
        refresh_token: Google OAuth refresh token
        token_expiry: Token expiration datetime

    Returns:
        GoogleCalendarClient instance
    """
    return GoogleCalendarClient(access_token, refresh_token, token_expiry)
