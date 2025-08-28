#!/usr/bin/env python3
"""
Test to check specific lot URL for auction opportunity
"""

import asyncio
from playwright.sync_api import sync_playwright
import os
from eig import check_street_history_for_auction_properties

def test_specific_lot():
    """Test specific lot URL for auction opportunity"""
    
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
            
            # Navigate to the lot page
            page.goto(test_lot_url, wait_until="networkidle")
            page.wait_for_timeout(3000)
            
            print(f"✅ Page loaded: {page.title}")
            
            # Extract lot information
            try:
                # Get lot number
                lot_number_elem = page.query_selector('.lot-number, .lot-no, h1, h2')
                lot_number = lot_number_elem.text_content().strip() if lot_number_elem else "Unknown"
                
                # Get address
                address_elem = page.query_selector('.address, .property-address, [class*="address"]')
                address = address_elem.text_content().strip() if address_elem else "Unknown"
                
                # Get auction sale status
                auction_sale_elem = page.query_selector('.text-end h2, .auction-result, [class*="result"]')
                auction_sale = auction_sale_elem.text_content().strip() if auction_sale_elem else "Unknown"
                
                print(f"\n📋 Lot Information:")
                print(f"   Lot Number: {lot_number}")
                print(f"   Address: {address}")
                print(f"   Auction Sale: {auction_sale}")
                
                # Create mock lot data for testing
                lot_data = {
                    'address': address,
                    'auction_sale': auction_sale,
                    'auction_name': 'Auction House London',  # Default
                    'auction_date': '2025-05-28'  # Default
                }
                
                # Test the street history check
                result = check_street_history_for_auction_properties(
                    lot_data, 
                    page
                )
                
                print(f"\n📊 Street History Check Result:")
                print(f"   Transaction Type: {result.get('transaction_type', 'NOT SET')}")
                print(f"   EIG Street History URL: {result.get('eig_street_history_url', 'NOT SET')}")
                
                # Check if it should be an auction opportunity
                auction_sale_lower = auction_sale.lower()
                is_withdrawn_unsold = any(pattern in auction_sale_lower for pattern in ['withdrawn', 'unsold', 'passed', 'no bids', 'no sale', 'not sold', 'failed to sell'])
                
                print(f"\n🔍 Auction Opportunity Analysis:")
                print(f"   Current auction sale: '{auction_sale}'")
                print(f"   Is withdrawn/unsold: {is_withdrawn_unsold}")
                
                if is_withdrawn_unsold:
                    print(f"   ✅ Current listing is withdrawn/unsold")
                else:
                    print(f"   ❌ Current listing is NOT withdrawn/unsold - cannot be auction opportunity")
                
                if result.get('transaction_type') == 'auction opportunity':
                    print(f"   ✅ CORRECTLY IDENTIFIED AS AUCTION OPPORTUNITY!")
                elif result.get('transaction_type') == 'auction to auction':
                    print(f"   ✅ IDENTIFIED AS AUCTION TO AUCTION!")
                else:
                    print(f"   ❌ NOT identified as auction opportunity or auction to auction")
                    print(f"   Expected: auction opportunity or auction to auction")
                    print(f"   Found: {result.get('transaction_type', 'NOT SET')}")
                
            except Exception as e:
                print(f"❌ Error extracting lot information: {e}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    test_specific_lot() 