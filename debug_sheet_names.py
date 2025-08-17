#!/usr/bin/env python3
"""
Debug Sheet Names and Tab Access

This script will help us understand what sheet tabs exist and how to properly access them.
"""

import sys
import os
import requests
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sheets_webapp import PropertyDataManagerWebApp

def debug_sheet_names():
    """Debug sheet names and tab access"""
    print("🔍 Debugging Sheet Names and Tab Access")
    print("=" * 50)
    
    # Initialize sheets manager
    sheets_manager = PropertyDataManagerWebApp()
    
    # Test different sheet name variations
    sheet_names_to_test = [
        'POTENTIAL_TRADES',
        'potential_trades',
        'Potential_Trades',
        'POTENTIALTRADES',
        'Potential Trades',
        'AUCTIONS_MASTER',
        'auctions_master',
        'AUCTION_MASTER',
        'auction_master'
    ]
    
    print(f"📤 Testing different sheet name variations...")
    print(f"   URL: {sheets_manager.webapp_url}")
    print(f"   Token: {sheets_manager.shared_token[:10]}...")
    print()
    
    for sheet_name in sheet_names_to_test:
        print(f"🔄 Testing sheet name: '{sheet_name}'")
        
        try:
            # Test read operation
            payload = {
                'token': sheets_manager.shared_token,
                'action': 'read',
                'sheet_name': sheet_name
            }
            
            response = requests.post(sheets_manager.webapp_url, json=payload, timeout=30)
            
            print(f"   📥 Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    entries = result.get('rows', [])
                    print(f"   ✅ SUCCESS: Found {len(entries)} entries in '{sheet_name}'")
                    
                    # Show first entry details if any
                    if entries:
                        first_entry = entries[0]
                        print(f"   📋 First entry: {first_entry.get('address', 'No address')} - {first_entry.get('auction_name', 'No name')}")
                else:
                    print(f"   ❌ ERROR: {result.get('error', 'Unknown error')}")
            else:
                print(f"   ❌ HTTP ERROR: {response.status_code}")
                print(f"   📥 Response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"   ❌ EXCEPTION: {e}")
        
        print()
    
    # Test adding to different sheet names
    print(f"🔄 Testing add operation to different sheet names...")
    
    test_property = {
        'auction_name': 'Sheet Name Test',
        'auction_date': '2025-01-15',
        'address': '999 Sheet Test Street, London',
        'auction_sale': '£400,000',
        'lot_number': 'SHEET-001',
        'postcode': 'SW1A 1AA',
        'purchase_price': '',  # Empty - should go to POTENTIAL_TRADES
        'sold_date': '',  # Empty - should go to POTENTIAL_TRADES
        'auction_url': 'https://example.com/auction/sheet-test',
        'source_url': '',
        'guide_price': '',
        'owner': '',
        'qa_status': 'pending_enrichment',
        'added_to_potential_trades': '2025-01-15T10:00:00'
    }
    
    for sheet_name in ['POTENTIAL_TRADES', 'potential_trades', 'Potential_Trades']:
        print(f"🔄 Testing add to: '{sheet_name}'")
        
        try:
            payload = {
                'token': sheets_manager.shared_token,
                'action': 'add',
                'sheet_name': sheet_name,
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
            
            print(f"   📥 Response status: {response.status_code}")
            print(f"   📥 Response: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    print(f"   ✅ SUCCESS: Added to '{sheet_name}'")
                else:
                    print(f"   ❌ ERROR: {result.get('error', 'Unknown error')}")
            else:
                print(f"   ❌ HTTP ERROR: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ EXCEPTION: {e}")
        
        print()
    
    print("🔍 Sheet name debugging completed!")

if __name__ == "__main__":
    debug_sheet_names() 