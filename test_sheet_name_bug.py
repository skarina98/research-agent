#!/usr/bin/env python3
"""
Test Sheet Name Bug

This script will test if the Google Apps Script is actually writing to the correct tabs
and help us understand why the data isn't appearing in the Google Sheet.
"""

import sys
import os
import requests
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sheets_webapp import PropertyDataManagerWebApp

def test_sheet_name_bug():
    """Test if the Google Apps Script is writing to the correct tabs"""
    print("🔍 Testing Sheet Name Bug")
    print("=" * 50)
    
    # Initialize sheets manager
    sheets_manager = PropertyDataManagerWebApp()
    
    # Test 1: Check what tabs actually exist by trying to read them
    print("\n🔄 Test 1: Checking what tabs actually exist...")
    
    # Try to read from AUCTIONS_MASTER (should have data)
    print(f"📤 Reading from AUCTIONS_MASTER...")
    try:
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
                print(f"   ✅ AUCTIONS_MASTER: {len(entries)} entries")
                if entries:
                    print(f"   📋 First entry: {entries[0].get('address', 'No address')}")
            else:
                print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Try to read from POTENTIAL_TRADES (should be empty)
    print(f"📤 Reading from POTENTIAL_TRADES...")
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
                print(f"   ✅ POTENTIAL_TRADES: {len(entries)} entries")
                if entries:
                    print(f"   📋 First entry: {entries[0].get('address', 'No address')}")
                else:
                    print(f"   📋 POTENTIAL_TRADES is empty (as expected)")
            else:
                print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 2: Add a test entry to POTENTIAL_TRADES
    print(f"\n🔄 Test 2: Adding test entry to POTENTIAL_TRADES...")
    
    test_property = {
        'auction_name': 'Sheet Name Bug Test',
        'auction_date': '2025-01-15',
        'address': '999 Bug Test Street, London',
        'auction_sale': '£300,000',
        'lot_number': 'BUG-001',
        'postcode': 'SW1A 1AA',
        'purchase_price': '',  # Empty - should go to POTENTIAL_TRADES
        'sold_date': '',  # Empty - should go to POTENTIAL_TRADES
        'auction_url': 'https://example.com/auction/bug-test',
        'source_url': '',
        'guide_price': '',
        'owner': '',
        'qa_status': 'pending_enrichment',
        'added_to_potential_trades': '2025-01-15T10:00:00'
    }
    
    try:
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
        
        print(f"📤 Sending add request to POTENTIAL_TRADES...")
        print(f"   Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(sheets_manager.webapp_url, json=payload, timeout=30)
        
        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print(f"✅ Successfully added to POTENTIAL_TRADES")
                
                # Now check if it actually appears
                print(f"\n🔄 Checking if the entry actually appears in POTENTIAL_TRADES...")
                
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
                        print(f"   📊 POTENTIAL_TRADES now has {len(entries)} entries")
                        
                        # Look for our test entry
                        test_found = False
                        for entry in entries:
                            if entry.get('address') == test_property['address']:
                                test_found = True
                                print(f"   ✅ Found our test entry: {entry.get('address')}")
                                break
                        
                        if not test_found:
                            print(f"   ❌ Test entry not found in POTENTIAL_TRADES")
                    else:
                        print(f"   ❌ Error reading POTENTIAL_TRADES: {result}")
                else:
                    print(f"   ❌ HTTP error reading POTENTIAL_TRADES: {response.status_code}")
            else:
                print(f"❌ Failed to add to POTENTIAL_TRADES: {result}")
        else:
            print(f"❌ HTTP error adding to POTENTIAL_TRADES: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error adding to POTENTIAL_TRADES: {e}")
    
    print(f"\n🔍 Sheet name bug test completed!")

if __name__ == "__main__":
    test_sheet_name_bug() 