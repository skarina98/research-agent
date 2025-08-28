#!/usr/bin/env python3
"""
Test to run just one auction to debug street history parsing
"""

import asyncio
from playwright.sync_api import sync_playwright
import os
from eig import parse_event_days

def test_single_auction():
    """Test to run just one auction to debug street history parsing"""
    
    with sync_playwright() as p:
        # Load existing session
        session_file = "sessions/eig.json"
        if not os.path.exists(session_file):
            print("❌ No EIG session found. Please run the workflow first.")
            return
        
        # Create browser context with session
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_file)
        page = context.new_page()
        
        try:
            # Test with a specific auction URL
            test_auction_url = "https://www.eigpropertyauctions.co.uk/clients/auctions/details/b0ee94de-33ca-4d19-b9f1-78a308a1944b"
            auction_name = "Auction House London"
            auction_date = "2025-05-28"
            
            print(f"🔍 Testing single auction: {auction_name} on {auction_date}")
            print(f"🔗 URL: {test_auction_url}")
            
            # Parse the auction
            lots = parse_event_days(test_auction_url, auction_name, auction_date, page)
            
            print(f"\n📊 Found {len(lots)} lots in auction")
            
            # Look for lots that should have street history entries
            for i, lot in enumerate(lots[:5]):  # Just check first 5 lots
                print(f"\n📄 Lot {i+1}: {lot.get('address', 'No address')}")
                print(f"   Property prices status: {lot.get('property_prices_status', 'NOT SET')}")
                print(f"   Transaction type: {lot.get('transaction_type', 'NOT SET')}")
                print(f"   Auction sale: {lot.get('auction_sale', 'NOT SET')}")
                print(f"   EIG Street History URL: {lot.get('eig_street_history_url', 'NOT SET')}")
                
                # Check if this lot should have street history entries
                if lot.get('eig_street_history_url'):
                    print(f"   ✅ Has street history URL - should check for relevant entries")
                else:
                    print(f"   ❌ No street history URL - might be missing")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    test_single_auction() 