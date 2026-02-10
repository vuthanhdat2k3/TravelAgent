"""
Test script for Amadeus API integration.
Run this to verify your Amadeus credentials are working.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.amadeus_client import get_amadeus_client
from amadeus import ResponseError


async def test_amadeus_connection():
    """Test basic Amadeus API connectivity."""
    print("🔍 Testing Amadeus API Connection...\n")
    
    try:
        # Get Amadeus client
        print("📡 Initializing Amadeus client...")
        amadeus = get_amadeus_client()
        print("✅ Client initialized successfully\n")
        
        # Test with a simple flight search
        print("🛫 Testing flight search: HAN -> SGN")
        print("   Date: 2026-03-15")
        print("   Passengers: 1 adult")
        print("   Class: Economy\n")
        
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode="HAN",
            destinationLocationCode="SGN",
            departureDate="2026-03-15",
            adults=1,
            travelClass="ECONOMY",
            currencyCode="VND",
            max=5
        )
        
        # Check response
        if response.data:
            print(f"✅ SUCCESS! Found {len(response.data)} flight offers\n")
            
            # Display first offer details
            if len(response.data) > 0:
                first_offer = response.data[0]
                price = first_offer.get('price', {})
                
                print("📋 Sample Offer Details:")
                print(f"   Offer ID: {first_offer.get('id', 'N/A')}")
                print(f"   Price: {price.get('total', 'N/A')} {price.get('currency', 'N/A')}")
                print(f"   Itineraries: {len(first_offer.get('itineraries', []))}")
                
                # Show segments
                for idx, itinerary in enumerate(first_offer.get('itineraries', []), 1):
                    print(f"\n   Itinerary {idx}:")
                    print(f"   Duration: {itinerary.get('duration', 'N/A')}")
                    print(f"   Segments: {len(itinerary.get('segments', []))}")
                    
                    for seg_idx, segment in enumerate(itinerary.get('segments', []), 1):
                        dep = segment.get('departure', {})
                        arr = segment.get('arrival', {})
                        print(f"      Segment {seg_idx}: {dep.get('iataCode')} -> {arr.get('iataCode')}")
                        print(f"         Carrier: {segment.get('carrierCode')} {segment.get('number')}")
        else:
            print("⚠️  No offers found (this might be normal for test environment)")
        
        print("\n✅ Amadeus API integration is working correctly!")
        return True
        
    except ResponseError as error:
        print(f"\n❌ Amadeus API Error:")
        print(f"   Status Code: {error.response.status_code}")
        print(f"   Error: {error.response.body}")
        print("\n💡 Troubleshooting:")
        print("   1. Check your AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET in .env")
        print("   2. Verify your Amadeus app is active")
        print("   3. Check if you're using the correct environment (test/production)")
        return False
        
    except ValueError as error:
        print(f"\n❌ Configuration Error: {error}")
        print("\n💡 Make sure AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET are set in .env")
        return False
        
    except Exception as error:
        print(f"\n❌ Unexpected Error: {error}")
        print(f"   Type: {type(error).__name__}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("  AMADEUS API INTEGRATION TEST")
    print("=" * 60)
    print()
    
    # Run test
    success = asyncio.run(test_amadeus_connection())
    
    print("\n" + "=" * 60)
    if success:
        print("  ✅ ALL TESTS PASSED")
    else:
        print("  ❌ TESTS FAILED - Check errors above")
    print("=" * 60)
    
    sys.exit(0 if success else 1)
