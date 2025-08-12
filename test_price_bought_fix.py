#!/usr/bin/env python3
"""
Test script to debug price_bought extraction
"""

import os
from datetime import datetime, timedelta
from eig import find_auctions, parse_event_days

def main():
    """Test the price_bought extraction fix"""
    
    print("🔧 Testing price_bought extraction fix")
    print("=" * 40)
    
    # Set environment variables for Google Sheets
    os.environ['GOOGLE_SHEETS_ID'] = '1ONZrugWl0amSFqGLq3_hHmR82Bps-vNxr-25gGk8B9Q'
    os.environ['GOOGLE_SHEETS_OAUTH'] = 'true'
    os.environ['GOOGLE_SHEETS_SHARED_TOKEN'] = '3c4ebe48f035fd3f68ccd5c9f619d7aa3f686d2d7637dc54324d979acc066feb'
    
    # Use a date range that might have more active auctions
    start_date = "2025-03-01"
    end_date = "2025-03-31"
    
    print(f"📅 Date range: {start_date} to {end_date}")
    print()
    
    try:
        # Find auctions
        print("1. Finding auctions...")
        auctions = find_auctions(start_date, end_date)
        print(f"Found {len(auctions)} auctions")
        
        if not auctions:
            print("❌ No auctions found in this date range")
            return
        
        # Test with the first auction
        auction = auctions[0]
        print(f"\n2. Testing with auction: {auction.get('name', 'Unknown')} on {auction.get('date', 'Unknown')}")
        
        if auction.get('detail_url'):
            print(f"Processing auction URL: {auction['detail_url']}")
            
            # Parse just the first few lots to test
            lots = parse_event_days(
                auction['detail_url'], 
                auction.get('name', 'Auction House London'),
                auction.get('date', '')
            )
            
            print(f"\n3. Results:")
            print(f"Total lots found: {len(lots)}")
            
            # Show the first 5 lots with their price_bought values
            for i, lot in enumerate(lots[:5]):
                print(f"\nLot {i+1}:")
                print(f"  Address: {lot.get('address', 'N/A')}")
                print(f"  Lot Number: {lot.get('lot_number', 'N/A')}")
                print(f"  Price Bought: '{lot.get('price_bought', 'N/A')}'")
                print(f"  Sold Price: '{lot.get('sold_price', 'N/A')}'")
                print(f"  Property Prices Status: {lot.get('property_prices_status', 'N/A')}")
                
                # Check if this lot would be imported
                if lot.get('price_bought') and lot.get('price_bought').strip():
                    print(f"  ✅ WOULD BE IMPORTED (has price_bought)")
                else:
                    print(f"  ❌ WOULD NOT BE IMPORTED (no price_bought)")
        else:
            print("❌ No detail URL available for this auction")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 