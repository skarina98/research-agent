#!/usr/bin/env python3
"""
Final Test for POTENTIAL_TRADES Integration

This script will test if the Google Apps Script now properly handles
the POTENTIAL_TRADES tab with the correct headers.
"""

import sys
import os
import requests
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sheets_webapp import PropertyDataManagerWebApp

def test_potential_trades_final():
    """Final test for POTENTIAL_TRADES integration"""
    print("🧪 Final Test for POTENTIAL_TRADES Integration")
    print("=" * 50)
    
    # Initialize sheets manager
    sheets_manager = PropertyDataManagerWebApp()
    
    # Test 1: Read from POTENTIAL_TRADES (should be empty)
    print("🔄 Test 1: Reading from POTENTIAL_TRADES...")
    try:
        payload = {
            'token': sheets_manager.shared_token,
            'action': 'read',
            'sheet_name': 'POTENTIAL_TRADES'
        }
        
        response = requests.post(sheets_manager.webapp_url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                entries = result.get('rows', [])
                print(f"✅ POTENTIAL_TRADES has {len(entries)} entries")
                
                if entries:
                    # Show headers
                    headers = list(entries[0].keys())
                    print(f"📋 Headers: {', '.join(headers)}")
                    
                    # Check for required headers
                    required_headers = ['added_to_potential_trades', 'ingested_at']
                    for header in required_headers:
                        if header in headers:
                            print(f"   ✅ {header}")
                        else:
                            print(f"   ❌ {header} - MISSING")
                else:
                    print("✅ POTENTIAL_TRADES is empty (as expected)")
            else:
                print(f"❌ Error reading POTENTIAL_TRADES: {result}")
        else:
            print(f"❌ HTTP error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error reading POTENTIAL_TRADES: {e}")
    
    print()
    
    # Test 2: Add entry to POTENTIAL_TRADES
    print("🔄 Test 2: Adding entry to POTENTIAL_TRADES...")
    try:
        test_property = {
            'auction_name': 'Final POTENTIAL_TRADES Test',
            'auction_date': '2025-01-15',
            'address': '888 Final Test Street, London',
            'auction_sale': '£450,000',
            'lot_number': 'FINAL-001',
            'postcode': 'SW1A 1AA',
            'purchase_price': '',  # EMPTY - should go to POTENTIAL_TRADES
            'sold_date': '',  # EMPTY - should go to POTENTIAL_TRADES
            'auction_url': 'https://example.com/auction/final-test',
            'source_url': '',
            'guide_price': '£420,000',
            'owner': '',
            'qa_status': 'pending_enrichment',
            'added_to_potential_trades': '2025-01-15T10:00:00'
        }
        
        payload = {
            'token': sheets_manager.shared_token,
            'action': 'add',
            'sheet_name': 'POTENTIAL_TRADES',
            'rows': [{
                'auction_name': test_property.get('auction_name', ''),
                'auction_date': test_property.get('auction_date', ''),
                'address': test_property.get('address', ''),
                'auction_sale': test_property.get('auction_sale', ''),
                'lot_number': test_property.get('lot_number', ''),
                'postcode': test_property.get('postcode', ''),
                'purchase_price': test_property.get('purchase_price', ''),
                'sold_date': test_property.get('sold_date', ''),
                'auction_url': test_property.get('auction_url', ''),
                'source_url': test_property.get('source_url', ''),
                'guide_price': test_property.get('guide_price', ''),
                'owner': test_property.get('owner', ''),
                'qa_status': test_property.get('qa_status', 'pending_enrichment'),
                'added_to_potential_trades': test_property.get('added_to_potential_trades', ''),
                'ingested_at': '2025-01-15T10:00:00'
            }]
        }
        
        response = requests.post(sheets_manager.webapp_url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print(f"✅ Successfully added to POTENTIAL_TRADES")
                print(f"   Response: {result}")
            else:
                print(f"❌ Failed to add to POTENTIAL_TRADES: {result}")
        else:
            print(f"❌ HTTP error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error adding to POTENTIAL_TRADES: {e}")
    
    print()
    
    # Test 3: Verify it was added to POTENTIAL_TRADES only
    print("🔄 Test 3: Verifying entry was added to POTENTIAL_TRADES only...")
    try:
        # Check POTENTIAL_TRADES
        payload = {
            'token': sheets_manager.shared_token,
            'action': 'read',
            'sheet_name': 'POTENTIAL_TRADES'
        }
        
        response = requests.post(sheets_manager.webapp_url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                entries = result.get('rows', [])
                
                # Look for our test entry
                test_found_in_pt = False
                for entry in entries:
                    if entry.get('address') == test_property['address']:
                        test_found_in_pt = True
                        print(f"✅ Found test entry in POTENTIAL_TRADES")
                        break
                
                if not test_found_in_pt:
                    print("❌ Test entry not found in POTENTIAL_TRADES")
            else:
                print(f"❌ Error reading POTENTIAL_TRADES: {result}")
        else:
            print(f"❌ HTTP error reading POTENTIAL_TRADES: {response.status_code}")
        
        # Check AUCTIONS_MASTER (should NOT have the entry)
        payload = {
            'token': sheets_manager.shared_token,
            'action': 'read',
            'sheet_name': 'AUCTIONS_MASTER'
        }
        
        response = requests.post(sheets_manager.webapp_url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                entries = result.get('rows', [])
                
                # Look for our test entry (should NOT be there)
                test_found_in_am = False
                for entry in entries:
                    if entry.get('address') == test_property['address']:
                        test_found_in_am = True
                        print(f"❌ ERROR: Test entry found in AUCTIONS_MASTER (should not be there)")
                        break
                
                if not test_found_in_am:
                    print("✅ Test entry correctly NOT found in AUCTIONS_MASTER")
            else:
                print(f"❌ Error reading AUCTIONS_MASTER: {result}")
        else:
            print(f"❌ HTTP error reading AUCTIONS_MASTER: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error verifying entries: {e}")
    
    print()
    print("🧪 Final test completed!")

if __name__ == "__main__":
    test_potential_trades_final() 