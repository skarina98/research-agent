#!/usr/bin/env python3
"""
Test to directly access the specific lot URL
"""

import asyncio
from playwright.sync_api import sync_playwright
import os

def test_specific_lot_simple():
    """Test specific lot URL directly"""
    
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
            # Test with the specific lot URL
            test_lot_url = "https://www.eigpropertyauctions.co.uk/lot/62ef3d4d-510d-4434-a85b-640722207df3?sb=1"
            
            print(f"🔍 Testing specific lot URL: {test_lot_url}")
            
            # Navigate to the lot page with a shorter timeout
            page.goto(test_lot_url, wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(2000)
            
            page_title = page.title()
            print(f"✅ Page loaded: {page_title}")
            
            # Check if we're on a login page
            if "sign in" in page_title.lower() or "login" in page_title.lower():
                print(f"⚠️ Redirected to login page - need to be logged in")
                return
            
            # Extract lot information
            try:
                # Get lot number
                lot_number_elem = page.query_selector('.lot-number, .lot-no, h1, h2, [class*="lot"]')
                lot_number = lot_number_elem.text_content().strip() if lot_number_elem else "Unknown"
                
                # Get address
                address_elem = page.query_selector('.address, .property-address, [class*="address"], h1, h2, h3')
                address = address_elem.text_content().strip() if address_elem else "Unknown"
                
                # Get auction sale status
                auction_sale_elem = page.query_selector('.text-end h2, .auction-result, [class*="result"], [class*="sale"]')
                auction_sale = auction_sale_elem.text_content().strip() if auction_sale_elem else "Unknown"
                
                print(f"\n📋 Lot Information:")
                print(f"   Lot Number: {lot_number}")
                print(f"   Address: {address}")
                print(f"   Auction Sale: {auction_sale}")
                
                # Check if this should be an auction opportunity
                auction_sale_lower = auction_sale.lower()
                is_withdrawn_unsold = any(pattern in auction_sale_lower for pattern in ['withdrawn', 'unsold', 'passed', 'no bids', 'no sale', 'not sold', 'failed to sell'])
                
                print(f"\n🔍 Auction Opportunity Analysis:")
                print(f"   Current auction sale: '{auction_sale}'")
                print(f"   Is withdrawn/unsold: {is_withdrawn_unsold}")
                
                if is_withdrawn_unsold:
                    print(f"   ✅ Current listing is withdrawn/unsold - could be auction opportunity")
                else:
                    print(f"   ❌ Current listing is NOT withdrawn/unsold - cannot be auction opportunity")
                
                # Look for street history link
                print(f"\n🔍 Looking for 'View Street history' link...")
                links = page.query_selector_all('a')
                street_history_link = None
                
                for i, link in enumerate(links):
                    try:
                        link_text = link.text_content().strip()
                        if 'street history' in link_text.lower():
                            street_history_link = link
                            print(f"   🎯 Found street history link {i+1}: '{link_text}'")
                            break
                    except:
                        continue
                
                if street_history_link:
                    print(f"   ✅ Street history link found!")
                    
                    # Get the href
                    href = street_history_link.get_attribute('href')
                    if href:
                        print(f"   🔗 Street history URL: {href}")
                        
                        # Click on the street history link
                        print(f"   🎯 Clicking on street history link...")
                        street_history_link.click()
                        page.wait_for_timeout(3000)
                        
                        print(f"   ✅ Navigated to street history page: {page.title()}")
                        
                        # Look for entries with the same address
                        print(f"   🔍 Looking for entries with address: {address}")
                        
                        # Look for elements that might contain auction entries
                        elements = page.query_selector_all('div[class*="property"], div[class*="lot"], div[class*="result"], div')
                        print(f"   📋 Found {len(elements)} potential elements")
                        
                        # Look for elements containing our address
                        matching_elements = []
                        for i, elem in enumerate(elements[:50]):  # Check first 50 elements
                            try:
                                text = elem.text_content().strip()
                                if address.lower() in text.lower() and len(text) > 50:
                                    matching_elements.append((i+1, text[:200]))
                                    print(f"   📄 Found address match in element {i+1}: {text[:100]}...")
                            except:
                                continue
                        
                        print(f"   📊 Found {len(matching_elements)} elements with matching address")
                        
                        if matching_elements:
                            print(f"   ✅ POTENTIAL AUCTION TO AUCTION OR AUCTION OPPORTUNITY!")
                            print(f"   📋 This property has appeared in multiple auctions")
                        else:
                            print(f"   ❌ No matching address entries found")
                        
                    else:
                        print(f"   ❌ No href found for street history link")
                else:
                    print(f"   ❌ No street history link found")
                    
                    # Show all links for debugging
                    print(f"   📋 All links on page:")
                    for i, link in enumerate(links[:20]):
                        try:
                            link_text = link.text_content().strip()
                            if link_text:
                                print(f"      {i+1}. '{link_text}'")
                        except:
                            continue
                
            except Exception as e:
                print(f"❌ Error extracting lot information: {e}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    test_specific_lot_simple() 