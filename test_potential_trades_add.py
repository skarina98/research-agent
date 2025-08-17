#!/usr/bin/env python3
"""
Test Adding Entry to POTENTIAL_TRADES

This script will test adding a specific entry to POTENTIAL_TRADES
that should definitely go there (no purchase price, no sold date).
"""

import sys
import os
import requests
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sheets_webapp import PropertyDataManagerWebApp

def test_add_to_potential_trades():
    """Test adding entry to POTENTIAL_TRADES"""
    print("🧪 Testing Add to POTENTIAL_TRADES")
    print("=" * 50)
    
    # Initialize sheets manager
    sheets_manager = PropertyDataManagerWebApp()
    
    # Create a test entry that should definitely go to POTENTIAL_TRADES
    # (no purchase price, no sold date)
    test_property = {
        'auction_name': 'Test POTENTIAL_TRADES Entry',
        'auction_date': '2025-01-15',
        'address': '999 POTENTIAL_TRADES Test Street, London',
        'auction_sale': '£400,000',
        'lot_number': 'PT-001',
        'postcode': 'SW1A 1AA',
        'purchase_price': '',  # EMPTY - should go to POTENTIAL_TRADES
        'sold_date': '',  # EMPTY - should go to POTENTIAL_TRADES
        'auction_url': 'https://example.com/auction/potential-trades-test',
        'source_url': '',
        'guide_price': '£380,000',
        'owner': '',
        'qa_status': 'pending_enrichment',
        'added_to_potential_trades': '2025-01-15T10:00:00'
    }
    
    print(f"📋 Test Property: {test_property['address']}")
    print(f"   Purchase Price: '{test_property['purchase_price']}' (empty)")
    print(f"   Sold Date: '{test_property['sold_date']}' (empty)")
    print(f"   Should go to: POTENTIAL_TRADES")
    print()
    
    # Test 1: Add to POTENTIAL_TRADES
    print("🔄 Test 1: Adding to POTENTIAL_TRADES...")
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
        
        print(f"📤 Sending request to POTENTIAL_TRADES...")
        print(f"   Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(sheets_manager.webapp_url, json=payload, timeout=30)
        
        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print(f"✅ SUCCESS: Added to POTENTIAL_TRADES")
            else:
                print(f"❌ ERROR: {result.get('error', 'Unknown error')}")
        else:
            print(f"❌ HTTP ERROR: {response.status_code}")
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
    
    print()
    
    # Test 2: Verify it was added by reading POTENTIAL_TRADES
    print("🔄 Test 2: Verifying POTENTIAL_TRADES content...")
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
                
                # Look for our test entry
                test_found = False
                for entry in entries:
                    if entry.get('address') == test_property['address']:
                        test_found = True
                        print(f"✅ Found our test entry in POTENTIAL_TRADES!")
                        print(f"   Address: {entry.get('address')}")
                        print(f"   Purchase Price: '{entry.get('purchase_price')}'")
                        print(f"   Sold Date: '{entry.get('sold_date')}'")
                        break
                
                if not test_found:
                    print("❌ Test entry not found in POTENTIAL_TRADES")
            else:
                print(f"❌ Error reading POTENTIAL_TRADES: {result}")
        else:
            print(f"❌ HTTP error reading POTENTIAL_TRADES: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error reading POTENTIAL_TRADES: {e}")
    
    print()
    
    # Test 3: Check AUCTIONS_MASTER to make sure it wasn't added there
    print("🔄 Test 3: Checking AUCTIONS_MASTER...")
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
                print(f"✅ AUCTIONS_MASTER has {len(entries)} entries")
                
                # Look for our test entry (should NOT be there)
                test_found = False
                for entry in entries:
                    if entry.get('address') == test_property['address']:
                        test_found = True
                        print(f"❌ ERROR: Test entry found in AUCTIONS_MASTER (should not be there)")
                        break
                
                if not test_found:
                    print("✅ Test entry correctly NOT found in AUCTIONS_MASTER")
            else:
                print(f"❌ Error reading AUCTIONS_MASTER: {result}")
        else:
            print(f"❌ HTTP error reading AUCTIONS_MASTER: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error reading AUCTIONS_MASTER: {e}")
    
    print("\n🧪 Test completed!")

if __name__ == "__main__":
    test_add_to_potential_trades() 