#!/usr/bin/env python3
"""
Debug POTENTIAL_TRADES Operations

This script will help us understand what's happening with POTENTIAL_TRADES
operations and why entries might not be appearing in the spreadsheet.
"""

import sys
import os
import requests
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sheets_webapp import PropertyDataManagerWebApp

def debug_potential_trades():
    """Debug POTENTIAL_TRADES operations"""
    print("🔍 Debugging POTENTIAL_TRADES Operations")
    print("=" * 50)
    
    # Initialize sheets manager
    sheets_manager = PropertyDataManagerWebApp()
    
    # Test 1: Check if POTENTIAL_TRADES tab exists
    print("\n🔄 Test 1: Checking if POTENTIAL_TRADES tab exists...")
    try:
        payload = {
            'token': sheets_manager.shared_token,
            'action': 'read',
            'sheet_name': 'POTENTIAL_TRADES'
        }
        
        print(f"📤 Sending request to check POTENTIAL_TRADES...")
        print(f"   URL: {sheets_manager.webapp_url}")
        print(f"   Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(sheets_manager.webapp_url, json=payload, timeout=30)
        
        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response text: {response.text[:500]}...")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                entries = result.get('rows', [])
                print(f"✅ POTENTIAL_TRADES tab exists with {len(entries)} entries")
                
                # Show first few entries
                print(f"\n📋 First 3 entries in POTENTIAL_TRADES:")
                for i, entry in enumerate(entries[:3]):
                    print(f"   Entry {i+1}: {entry.get('address', 'No address')} - {entry.get('auction_name', 'No name')}")
            else:
                print(f"❌ Error reading POTENTIAL_TRADES: {result}")
        else:
            print(f"❌ HTTP error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking POTENTIAL_TRADES: {e}")
    
    # Test 2: Try to add a test entry directly
    print("\n🔄 Test 2: Adding test entry directly to POTENTIAL_TRADES...")
    try:
        test_property = {
            'auction_name': 'Debug Test Auction',
            'auction_date': '2025-01-15',
            'address': '123 Debug Street, London',
            'auction_sale': '£500,000',
            'lot_number': 'DEBUG-001',
            'postcode': 'SW1A 1AA',
            'purchase_price': '',  # Empty - should go to POTENTIAL_TRADES
            'sold_date': '',  # Empty - should go to POTENTIAL_TRADES
            'auction_url': 'https://example.com/auction/debug-test',
            'source_url': '',
            'guide_price': '',
            'owner': '',
            'qa_status': 'pending_enrichment',
            'added_to_potential_trades': '2025-01-15T10:00:00'
        }
        
        # Prepare payload for POTENTIAL_TRADES
        payload = {
            'token': sheets_manager.shared_token,
            'action': 'add',
            'sheet_name': 'POTENTIAL_TRADES',  # Specify the tab name
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
        print(f"📥 Response text: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print(f"✅ Successfully added to POTENTIAL_TRADES: {result}")
            else:
                print(f"❌ Failed to add to POTENTIAL_TRADES: {result}")
        else:
            print(f"❌ HTTP error adding to POTENTIAL_TRADES: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error adding to POTENTIAL_TRADES: {e}")
    
    # Test 3: Check AUCTION_MASTER to see if it's working
    print("\n🔄 Test 3: Checking AUCTION_MASTER tab...")
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
                print(f"✅ AUCTION_MASTER tab exists with {len(entries)} entries")
                
                # Look for our test entry from the integration test
                test_found = False
                for entry in entries:
                    if entry.get('address') == '789 Test Master Street, London':
                        test_found = True
                        print(f"✅ Found our AUCTION_MASTER test entry")
                        break
                
                if not test_found:
                    print("⚠️ AUCTION_MASTER test entry not found")
            else:
                print(f"❌ Error reading AUCTION_MASTER: {result}")
        else:
            print(f"❌ HTTP error reading AUCTION_MASTER: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking AUCTION_MASTER: {e}")
    
    print("\n🔍 Debug completed!")

if __name__ == "__main__":
    debug_potential_trades() 