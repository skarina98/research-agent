#!/usr/bin/env python3
"""
Show POTENTIAL_TRADES Content

This script will show you exactly what's in the POTENTIAL_TRADES tab
so we can verify the data is there.
"""

import sys
import os
import requests
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sheets_webapp import PropertyDataManagerWebApp

def show_potential_trades_content():
    """Show the content of POTENTIAL_TRADES tab"""
    print("📋 Showing POTENTIAL_TRADES Content")
    print("=" * 50)
    
    # Initialize sheets manager
    sheets_manager = PropertyDataManagerWebApp()
    
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
                print(f"✅ Found {len(entries)} entries in POTENTIAL_TRADES")
                
                # Show headers
                if entries:
                    headers = list(entries[0].keys())
                    print(f"\n📋 Headers: {', '.join(headers)}")
                
                # Show first 10 entries
                print(f"\n📋 First 10 entries in POTENTIAL_TRADES:")
                print("-" * 80)
                
                for i, entry in enumerate(entries[:10]):
                    print(f"Entry {i+1}:")
                    print(f"  Address: {entry.get('address', 'No address')}")
                    print(f"  Auction Name: {entry.get('auction_name', 'No name')}")
                    print(f"  Auction Date: {entry.get('auction_date', 'No date')}")
                    print(f"  Auction Sale: {entry.get('auction_sale', 'No sale')}")
                    print(f"  Purchase Price: {entry.get('purchase_price', 'No price')}")
                    print(f"  Sold Date: {entry.get('sold_date', 'No sold date')}")
                    print(f"  Guide Price: {entry.get('guide_price', 'No guide price')}")
                    print(f"  QA Status: {entry.get('qa_status', 'No status')}")
                    print(f"  Added to PT: {entry.get('added_to_potential_trades', 'No date')}")
                    print("-" * 80)
                
                # Look for our test entries
                print(f"\n🔍 Looking for our test entries...")
                test_entries = []
                
                for entry in entries:
                    address = entry.get('address', '')
                    auction_name = entry.get('auction_name', '')
                    
                    # Look for our integration test entry
                    if '456 Test Integration Street' in address and 'Test Auction Integration' in auction_name:
                        test_entries.append(('Integration Test', entry))
                    
                    # Look for our debug test entry
                    if '123 Debug Street' in address and 'Debug Test Auction' in auction_name:
                        test_entries.append(('Debug Test', entry))
                
                if test_entries:
                    print(f"✅ Found {len(test_entries)} test entries:")
                    for test_type, entry in test_entries:
                        print(f"  {test_type}: {entry.get('address', 'No address')}")
                else:
                    print("❌ No test entries found")
                
                # Show some recent entries (last 5)
                print(f"\n📋 Last 5 entries in POTENTIAL_TRADES:")
                print("-" * 80)
                
                for i, entry in enumerate(entries[-5:]):
                    print(f"Recent Entry {i+1}:")
                    print(f"  Address: {entry.get('address', 'No address')}")
                    print(f"  Auction Name: {entry.get('auction_name', 'No name')}")
                    print(f"  Auction Date: {entry.get('auction_date', 'No date')}")
                    print(f"  Added to PT: {entry.get('added_to_potential_trades', 'No date')}")
                    print("-" * 80)
                
            else:
                print(f"❌ Error reading POTENTIAL_TRADES: {result}")
        else:
            print(f"❌ HTTP error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error reading POTENTIAL_TRADES: {e}")
    
    print("\n📋 Content display completed!")

if __name__ == "__main__":
    show_potential_trades_content() 