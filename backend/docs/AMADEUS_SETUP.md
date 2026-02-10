# Amadeus API Integration Guide

## Overview
This Travel Agent application integrates with the Amadeus Flight Offers Search API to provide real-time flight search functionality.

## Getting Amadeus API Credentials

### 1. Create an Amadeus Account
1. Visit [Amadeus for Developers](https://developers.amadeus.com/)
2. Click "Register" and create a free account
3. Verify your email address

### 2. Create an Application
1. Log in to your Amadeus dashboard
2. Go to "My Self-Service Workspace"
3. Click "Create New App"
4. Fill in the application details:
   - **Application Name**: Travel Agent (or your preferred name)
   - **Application Type**: Select appropriate type
5. Click "Create"

### 3. Get Your Credentials
After creating the app, you'll receive:
- **API Key** (Client ID)
- **API Secret** (Client Secret)

### 4. Configure Environment Variables
Add these credentials to your `.env` file:

```bash
# Amadeus Configuration
AMADEUS_CLIENT_ID=your_client_id_here
AMADEUS_CLIENT_SECRET=your_client_secret_here
AMADEUS_ENV=test  # Use 'test' for development, 'production' for live data
```

## Test vs Production Environment

### Test Environment (Free)
- **Purpose**: Development and testing
- **Data**: Sample flight data (not real-time)
- **Cost**: Free
- **Rate Limits**: Lower limits suitable for development
- **Setup**: Use `AMADEUS_ENV=test`

### Production Environment
- **Purpose**: Live application with real flight data
- **Data**: Real-time flight offers from airlines
- **Cost**: Pay-per-transaction (check Amadeus pricing)
- **Rate Limits**: Higher limits for production use
- **Setup**: Use `AMADEUS_ENV=production`

## API Features Used

### Flight Offers Search
- **Endpoint**: `GET /v2/shopping/flight-offers`
- **Features**:
  - One-way and round-trip searches
  - Multiple passengers support
  - Cabin class selection (Economy, Business, etc.)
  - Currency conversion
  - Price filtering
  - Direct flights or with connections

## Implementation Details

### Search Parameters
The integration supports:
- **Origin/Destination**: IATA airport codes (e.g., HAN, SGN, JFK)
- **Dates**: Departure and optional return date
- **Passengers**: Number of adults (1-9)
- **Cabin Class**: ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST
- **Currency**: Any supported currency code (VND, USD, EUR, etc.)

### Response Normalization
Amadeus responses are normalized to our schema:
```python
{
    "offer_id": str,           # Unique offer identifier
    "total_price": float,      # Total price in specified currency
    "currency": str,           # Currency code
    "duration_minutes": int,   # Total flight duration
    "stops": int,              # Number of stops
    "segments": [              # Flight segments
        {
            "origin": str,
            "destination": str,
            "departure_time": datetime,
            "arrival_time": datetime,
            "airline_code": str,
            "flight_number": str
        }
    ]
}
```

### Caching Strategy
- Search results are cached for 30 minutes
- Cache key is based on search parameters (origin, destination, dates, etc.)
- Reduces API calls and improves response time
- Automatic cache expiration

## Error Handling

The integration includes robust error handling:
- **API Errors**: Returns empty results instead of failing
- **Invalid Credentials**: Logs error and returns empty results
- **Rate Limiting**: Gracefully handles rate limit errors
- **Network Issues**: Catches and logs connection errors

## Testing

### Test the Integration
1. Ensure your `.env` file has valid Amadeus credentials
2. Start the backend server:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```
3. Make a test search request:
   ```bash
   curl -X POST "http://localhost:8000/api/flights/search" \
     -H "Content-Type: application/json" \
     -d '{
       "origin": "HAN",
       "destination": "SGN",
       "depart_date": "2026-03-15",
       "adults": 1,
       "travel_class": "ECONOMY",
       "currency": "VND"
     }'
   ```

### Common IATA Codes (Vietnam)
- **HAN**: Hanoi (Noi Bai International Airport)
- **SGN**: Ho Chi Minh City (Tan Son Nhat International Airport)
- **DAD**: Da Nang International Airport
- **CXR**: Cam Ranh International Airport
- **PQC**: Phu Quoc International Airport

## Rate Limits

### Test Environment
- **Transactions per month**: 2,000 free
- **Requests per second**: 10

### Production Environment
- **Pricing**: Pay-as-you-go
- **Rate limits**: Based on your subscription tier

## Troubleshooting

### "Amadeus credentials not configured"
- Check that `AMADEUS_CLIENT_ID` and `AMADEUS_CLIENT_SECRET` are set in `.env`
- Verify there are no extra spaces or quotes in the values

### "401 Unauthorized"
- Verify your API credentials are correct
- Check if your Amadeus app is active
- Ensure you're using the correct environment (test vs production)

### "No results found"
- Check that IATA codes are valid
- Verify dates are in the future
- Try with different search parameters
- Check Amadeus dashboard for API status

### "Rate limit exceeded"
- You've exceeded your monthly quota
- Wait for the quota to reset or upgrade your plan
- Implement request throttling in your application

## Resources

- [Amadeus API Documentation](https://developers.amadeus.com/self-service)
- [Flight Offers Search API Reference](https://developers.amadeus.com/self-service/category/air/api-doc/flight-offers-search)
- [Amadeus SDK for Python](https://github.com/amadeus4dev/amadeus-python)
- [IATA Airport Codes](https://www.iata.org/en/publications/directories/code-search/)

## Support

For issues with:
- **Amadeus API**: Contact Amadeus support or check their documentation
- **This Integration**: Check application logs or create an issue in the repository
