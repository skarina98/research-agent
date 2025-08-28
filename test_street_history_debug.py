#!/usr/bin/env python3
"""
Simple test to debug street history parsing
"""

import asyncio
from playwright.sync_api import sync_playwright
import os
from eig import parse_street_history_page

def test_street_history_debug():
    """Test to debug street history parsing"""
    
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
            # Test with a specific street history page that we know has multiple entries
            test_url = "https://www.eigpropertyauctions.co.uk/search/historical/1316703"
            target_address = "52 Cecil Road, Gravesend, DA11 7DG"
            current_auction_name = "Auction House London"
            current_auction_date = "2025-05-28"
            
            print(f"🔍 Testing street history parsing:")
            print(f"   URL: {test_url}")
            print(f"   Address: {target_address}")
            print(f"   Current auction: {current_auction_name} on {current_auction_date}")
            
            # Navigate to the street history page
            page.goto(test_url, wait_until="networkidle")
            page.wait_for_timeout(3000)
            
            print(f"✅ Page loaded: {page.title}")
            
            # Parse the street history page
            relevant_entries = parse_street_history_page(page, target_address, current_auction_name, current_auction_date)
            
            print(f"\n📊 Results:")
            print(f"   Found {len(relevant_entries)} relevant auction entries")
            
            for i, entry in enumerate(relevant_entries):
                print(f"   Entry {i+1}:")
                print(f"     Date: {entry.get('auction_date')}")
                print(f"     Auction: {entry.get('auction_name')}")
                print(f"     Has sold indicator: {entry.get('has_sold_indicator')}")
                print(f"     Has unsold indicator: {entry.get('has_unsold_indicator')}")
                print(f"     Text: {entry.get('element_text', '')[:100]}...")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    test_street_history_debug() 