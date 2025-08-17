#!/usr/bin/env python3
"""
Fix POTENTIAL_TRADES Headers

This script will add the missing added_to_potential_trades column to the POTENTIAL_TRADES tab.
"""

import sys
import os
import requests
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sheets_webapp import PropertyDataManagerWebApp

def fix_potential_trades_headers():
    """Add missing column to POTENTIAL_TRADES"""
    print("🔧 Fixing POTENTIAL_TRADES Headers")
    print("=" * 50)
    
    # Initialize sheets manager
    sheets_manager = PropertyDataManagerWebApp()
    
    print("⚠️ IMPORTANT: You need to manually add the 'added_to_potential_trades' column to your POTENTIAL_TRADES tab.")
    print()
    print("📋 Steps to fix:")
    print("1. Open your Google Sheet")
    print("2. Go to the POTENTIAL_TRADES tab")
    print("3. Add a new column called 'added_to_potential_trades' (column O)")
    print("4. The column should be empty for existing rows")
    print()
    print("📋 Required headers for POTENTIAL_TRADES:")
    required_headers = [
        'auction_name', 'auction_date', 'address', 'auction_sale',
        'lot_number', 'postcode', 'purchase_price', 'sold_date',
        'owner', 'guide_price', 'auction_url', 'source_url',
        'qa_status', 'ingested_at', 'added_to_potential_trades'
    ]
    
    for i, header in enumerate(required_headers, 1):
        print(f"   {i}. {header}")
    
    print()
    print("🔄 After you add the column, run this script again to test.")
    
    # Test if the column was added
    print("\n🔄 Testing if POTENTIAL_TRADES has correct headers...")
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
                    headers = list(entries[0].keys())
                    print(f"\n📋 Current headers in POTENTIAL_TRADES:")
                    for i, header in enumerate(headers):
                        print(f"   {i+1}. {header}")
                    
                    # Check for added_to_potential_trades
                    if 'added_to_potential_trades' in headers:
                        print(f"\n✅ SUCCESS: 'added_to_potential_trades' column found!")
                        print(f"   You can now test adding entries to POTENTIAL_TRADES")
                    else:
                        print(f"\n❌ 'added_to_potential_trades' column still missing")
                        print(f"   Please add the column manually as described above")
                else:
                    print("⚠️ POTENTIAL_TRADES is empty")
            else:
                print(f"❌ Error reading POTENTIAL_TRADES: {result}")
        else:
            print(f"❌ HTTP error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error reading POTENTIAL_TRADES: {e}")
    
    print("\n🔧 Header fix instructions completed!")

if __name__ == "__main__":
    fix_potential_trades_headers() 