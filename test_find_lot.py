#!/usr/bin/env python3
"""
Test to find the specific lot in the auction we were processing
"""

import asyncio
from playwright.sync_api import sync_playwright
import os
from eig import parse_event_days

def test_find_lot():
    """Test to find the specific lot in the auction"""
    
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
            # Test with the auction URL we were using
            test_auction_url = "https://www.eigpropertyauctions.co.uk/clients/auctions/details/b0ee94de-33ca-4d19-b9f1-78a308a1944b"
            auction_name = "Auction House London"
            auction_date = "2025-05-28"
            
            print(f"🔍 Testing auction URL: {test_auction_url}")
            
            # Parse the auction
            lots = parse_event_days(test_auction_url, auction_name, auction_date, page)
            
            print(f"\n📊 Found {len(lots)} lots in auction")
            
            # Look for lots that might be the one we're looking for
            # The lot ID from the URL is: 62ef3d4d-510d-4434-a85b-640722207df3
            target_lot_id = "62ef3d4d-510d-4434-a85b-640722207df3"
            
            print(f"\n🔍 Looking for lot with ID: {target_lot_id}")
            
            # Check if any lot URLs contain this ID
            found_lot = None
            for i, lot in enumerate(lots):
                lot_url = lot.get('lot_url', '')
                if target_lot_id in lot_url:
                    found_lot = lot
                    print(f"\n🎯 Found target lot {i+1}: {lot.get('address', 'No address')}")
                    print(f"   Lot URL: {lot_url}")
                    break
            
            if not found_lot:
                print(f"\n❌ Lot with ID '{target_lot_id}' not found in this auction")
                
                # Show some sample lot URLs to help identify the pattern
                print(f"\n📋 Sample lot URLs from auction:")
                for i, lot in enumerate(lots[:10]):
                    lot_url = lot.get('lot_url', 'No URL')
                    address = lot.get('address', 'No address')
                    print(f"   {i+1}. {address}")
                    print(f"      URL: {lot_url}")
                if len(lots) > 10:
                    print(f"   ... and {len(lots) - 10} more")
            
            # Also look for lots that might be "unsold" or "withdrawn" as potential auction opportunities
            print(f"\n🔍 Looking for potential auction opportunities (unsold/withdrawn lots)...")
            potential_opportunities = []
            
            for i, lot in enumerate(lots):
                auction_sale = lot.get('auction_sale', '').lower()
                is_withdrawn_unsold = any(pattern in auction_sale for pattern in ['withdrawn', 'unsold', 'passed', 'no bids', 'no sale', 'not sold', 'failed to sell'])
                
                if is_withdrawn_unsold:
                    potential_opportunities.append((i+1, lot))
                    print(f"   📄 Lot {i+1}: {lot.get('address', 'No address')}")
                    print(f"      Auction Sale: {lot.get('auction_sale', 'NOT SET')}")
                    print(f"      Transaction Type: {lot.get('transaction_type', 'NOT SET')}")
                    print(f"      EIG Street History URL: {lot.get('eig_street_history_url', 'NOT SET')}")
            
            print(f"\n📊 Found {len(potential_opportunities)} potential auction opportunities")
            
            if potential_opportunities:
                print(f"   ✅ These lots could be auction opportunities if they have relevant street history")
            else:
                print(f"   ❌ No unsold/withdrawn lots found in this auction")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    test_find_lot() 