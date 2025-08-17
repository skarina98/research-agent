#!/usr/bin/env python3
"""
Check POTENTIAL_TRADES Headers

This script will check if the POTENTIAL_TRADES tab has the correct headers,
especially the added_to_potential_trades column that the Google Apps Script expects.
"""

import sys
import os
import requests
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sheets_webapp import PropertyDataManagerWebApp

def check_potential_trades_headers():
    """Check POTENTIAL_TRADES headers"""
    print("🔍 Checking POTENTIAL_TRADES Headers")
    print("=" * 50)
    
    # Initialize sheets manager
    sheets_manager = PropertyDataManagerWebApp()
    
    # Test reading POTENTIAL_TRADES with minimal data
    print("🔄 Reading POTENTIAL_TRADES headers...")
    try:
        payload = {
            'token': sheets_manager.shared_token,
            'action': 'read',
            'sheet_name': 'POTENTIAL_TRADES'
        }
        
        response = requests.post(sheets_manager.webapp_url, json=payload, timeout=30)
        
        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                entries = result.get('rows', [])
                print(f"✅ POTENTIAL_TRADES has {len(entries)} entries")
                
                if entries:
                    # Show headers from first entry
                    headers = list(entries[0].keys())
                    print(f"\n📋 Headers in POTENTIAL_TRADES:")
                    for i, header in enumerate(headers):
                        print(f"   {i+1}. {header}")
                    
                    # Check for required headers
                    required_headers = [
                        'auction_name', 'auction_date', 'address', 'auction_sale',
                        'lot_number', 'postcode', 'purchase_price', 'sold_date',
                        'owner', 'guide_price', 'auction_url', 'source_url',
                        'qa_status', 'added_to_potential_trades', 'ingested_at'
                    ]
                    
                    print(f"\n🔍 Checking required headers:")
                    missing_headers = []
                    for header in required_headers:
                        if header in headers:
                            print(f"   ✅ {header}")
                        else:
                            print(f"   ❌ {header} - MISSING")
                            missing_headers.append(header)
                    
                    if missing_headers:
                        print(f"\n⚠️ Missing headers: {missing_headers}")
                        print(f"   This might be causing the Google Apps Script to fail")
                    else:
                        print(f"\n✅ All required headers present")
                        
                    # Show first entry details
                    if entries:
                        first_entry = entries[0]
                        print(f"\n📋 First entry details:")
                        for header in headers:
                            value = first_entry.get(header, '')
                            print(f"   {header}: '{value}'")
                else:
                    print("⚠️ POTENTIAL_TRADES is empty - no headers to check")
            else:
                print(f"❌ Error reading POTENTIAL_TRADES: {result}")
        else:
            print(f"❌ HTTP error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error reading POTENTIAL_TRADES: {e}")
    
    print()
    
    # Compare with AUCTIONS_MASTER headers
    print("🔄 Comparing with AUCTIONS_MASTER headers...")
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
                
                if entries:
                    headers = list(entries[0].keys())
                    print(f"\n📋 Headers in AUCTIONS_MASTER:")
                    for i, header in enumerate(headers):
                        print(f"   {i+1}. {header}")
                    
                    # Check if AUCTIONS_MASTER has added_to_potential_trades
                    if 'added_to_potential_trades' in headers:
                        print(f"\n⚠️ AUCTIONS_MASTER has 'added_to_potential_trades' column")
                        print(f"   This might be causing confusion in the Google Apps Script")
                    else:
                        print(f"\n✅ AUCTIONS_MASTER does NOT have 'added_to_potential_trades' column")
            else:
                print(f"❌ Error reading AUCTIONS_MASTER: {result}")
        else:
            print(f"❌ HTTP error reading AUCTIONS_MASTER: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error reading AUCTIONS_MASTER: {e}")
    
    print("\n🔍 Header check completed!")

if __name__ == "__main__":
    check_potential_trades_headers() 