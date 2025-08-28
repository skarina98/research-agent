#!/usr/bin/env python3
"""
Test to check street view functionality for auction opportunity
"""

import asyncio
from playwright.sync_api import sync_playwright
import os
from eig import parse_event_days

def test_auction_opportunity():
    """Test street view functionality for auction opportunity"""
    
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
            # Test with a specific auction URL that contains the target address
            test_auction_url = "https://www.eigpropertyauctions.co.uk/clients/auctions/details/b0ee94de-33ca-4d19-b9f1-78a308a1944b"
            auction_name = "Auction House London"
            auction_date = "2025-05-28"
            
            print(f"🔍 Testing auction opportunity for: 194 Hainault Avenue, Westcliff-on-Sea, SS0 9EX")
            print(f"🔗 URL: {test_auction_url}")
            
            # Parse the auction
            lots = parse_event_days(test_auction_url, auction_name, auction_date, page)
            
            print(f"\n📊 Found {len(lots)} lots in auction")
            
            # Look for the specific address
            target_address = "194 Hainault Avenue, Westcliff-on-Sea, SS0 9EX"
            found_lot = None
            
            for i, lot in enumerate(lots):
                if lot.get('address', '').lower() == target_address.lower():
                    found_lot = lot
                    print(f"\n🎯 Found target lot {i+1}: {lot.get('address', 'No address')}")
                    break
            
            if found_lot:
                print(f"   Property prices status: {found_lot.get('property_prices_status', 'NOT SET')}")
                print(f"   Transaction type: {found_lot.get('transaction_type', 'NOT SET')}")
                print(f"   Auction sale: {found_lot.get('auction_sale', 'NOT SET')}")
                print(f"   EIG Street History URL: {found_lot.get('eig_street_history_url', 'NOT SET')}")
                
                # Check if this should be an auction opportunity
                auction_sale = found_lot.get('auction_sale', '').lower()
                is_withdrawn_unsold = any(pattern in auction_sale for pattern in ['withdrawn', 'unsold', 'passed', 'no bids', 'no sale', 'not sold', 'failed to sell'])
                
                print(f"\n🔍 Auction Opportunity Analysis:")
                print(f"   Current auction sale: '{found_lot.get('auction_sale', 'NOT SET')}'")
                print(f"   Is withdrawn/unsold: {is_withdrawn_unsold}")
                
                if is_withdrawn_unsold:
                    print(f"   ✅ Current listing is withdrawn/unsold")
                else:
                    print(f"   ❌ Current listing is NOT withdrawn/unsold - cannot be auction opportunity")
                
                if found_lot.get('transaction_type') == 'auction opportunity':
                    print(f"   ✅ CORRECTLY classified as auction opportunity")
                elif found_lot.get('transaction_type') == 'auction to auction':
                    print(f"   ⚠️ Classified as auction to auction (should check if it should be auction opportunity)")
                else:
                    print(f"   ❌ NOT classified as auction opportunity (current: {found_lot.get('transaction_type')})")
                
                if found_lot.get('eig_street_history_url'):
                    print(f"   ✅ Has street history URL - should check for relevant entries")
                else:
                    print(f"   ❌ No street history URL - might be missing")
                
            else:
                print(f"\n❌ Target address '{target_address}' not found in auction")
                
                # Show some sample addresses to help find it
                print(f"\n📋 Sample addresses from auction:")
                for i, lot in enumerate(lots[:10]):
                    print(f"   {i+1}. {lot.get('address', 'No address')}")
                if len(lots) > 10:
                    print(f"   ... and {len(lots) - 10} more")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    test_auction_opportunity() 