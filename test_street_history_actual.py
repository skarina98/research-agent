#!/usr/bin/env python3
"""
Test to examine actual street history element content
"""

import asyncio
from playwright.sync_api import sync_playwright
import os

def test_street_history_actual():
    """Test to examine actual street history element content"""
    
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
            # Navigate to a specific street history page to test
            test_url = "https://www.eigpropertyauctions.co.uk/search/historical/1318204"
            print(f"🔍 Testing street history page: {test_url}")
            
            page.goto(test_url, wait_until="networkidle")
            page.wait_for_timeout(3000)
            
            print(f"✅ Page loaded: {page.title}")
            
            # Look for auction entries on the page
            elements = page.query_selector_all('div[class*="property"]')
            print(f"🔍 Found {len(elements)} elements with selector: div[class*='property']")
            
            # Look for elements that contain addresses
            address_elements = []
            for elem in elements:
                try:
                    text = elem.text_content().strip()
                    if text and any(char.isdigit() for char in text) and len(text) > 20:
                        # Check if it looks like an address (contains numbers and is reasonably long)
                        address_elements.append(elem)
                except:
                    continue
            
            print(f"🏠 Found {len(address_elements)} potential address elements")
            
            # Look for elements containing our target address
            target_address = "Flat 25, Wadhurst Court, Downview Road, Worthing, BN11 4QX"
            target_address_lower = target_address.lower()
            
            print(f"🏠 Looking for entries with exact address: {target_address}")
            print(f"🔍 Processing {len(address_elements)} elements...")
            
            found_entries = []
            for i, element in enumerate(address_elements):
                try:
                    element_text = element.text_content().strip()
                    
                    # Check if this element contains our exact address
                    if target_address_lower in element_text.lower():
                        print(f"\n📄 Found exact address match in element {i+1}:")
                        print(f"   Text: {element_text}")
                        print(f"   Length: {len(element_text)} characters")
                        found_entries.append(element_text)
                        
                        # Try to extract date patterns
                        import re
                        date_patterns = [
                            r'(\d{1,2}/\d{1,2}/\d{4})',  # DD/MM/YYYY
                            r'(\d{1,2}-\d{1,2}-\d{4})',  # DD-MM-YYYY
                            r'(\d{1,2}\s+[A-Za-z]+\s+\d{4})',  # DD Month YYYY
                            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
                        ]
                        
                        for pattern in date_patterns:
                            matches = re.findall(pattern, element_text)
                            if matches:
                                print(f"   📅 Date matches: {matches}")
                        
                        # Look for auction names
                        auctioneer_names = [
                            "SDL Property Auctions",
                            "Auction House London", 
                            "McHugh & Co",
                            "Bonde Wolfe",
                            "Auction House South West",
                            "Savills",
                            "Yopa"
                        ]
                        
                        for name in auctioneer_names:
                            if name.lower() in element_text.lower():
                                print(f"   🏢 Auction name found: {name}")
                        
                        # Look for sold patterns
                        sold_patterns = [
                            "sold for",
                            "sold prior",
                            "sold post",
                            "withdrawn prior",
                            "sold at",
                            "sold by",
                            "sold to",
                            "sold -",
                            "sold:",
                            "sold."
                        ]
                        
                        for pattern in sold_patterns:
                            if pattern in element_text.lower():
                                print(f"   💰 Sold pattern found: '{pattern}'")
                        
                        # Look for unsold patterns
                        unsold_patterns = [
                            "unsold",
                            "withdrawn",
                            "passed",
                            "no bids",
                            "no sale",
                            "not sold",
                            "failed to sell"
                        ]
                        
                        for pattern in unsold_patterns:
                            if pattern in element_text.lower():
                                print(f"   ❌ Unsold pattern found: '{pattern}'")
                
                except Exception as e:
                    print(f"⚠️ Error processing element {i+1}: {e}")
                    continue
            
            print(f"\n📊 Summary: Found {len(found_entries)} entries with target address")
            
            if not found_entries:
                print("🔍 Let's look at some sample elements to understand the structure:")
                for i, element in enumerate(address_elements[:5]):
                    try:
                        element_text = element.text_content().strip()
                        print(f"\n📄 Element {i+1} sample:")
                        print(f"   Text: {element_text[:200]}...")
                    except:
                        continue
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    test_street_history_actual() 