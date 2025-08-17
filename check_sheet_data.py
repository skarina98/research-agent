#!/usr/bin/env python3
"""
Check the current data in the Google Sheet
"""

import requests
import json

def check_sheet_data():
    """Check the current data in the Google Sheet"""
    
    webapp_url = "https://script.google.com/macros/s/AKfycbxkTm30lbe0G3gMl2EAoNbpp2BF0uLJ1JIp-2vg8sxfe7xl56Gw4NvlbMS8FiC7paO6/exec"
    token = "3c4ebe48f035fd3f68ccd5c9f619d7aa3f686d2d7637dc54324d979acc066feb"
    
    print("🔍 Checking Google Sheet Data")
    print("=" * 50)
    
    # Read current data
    read_payload = {
        "token": token,
        "action": "read"
    }
    
    try:
        response = requests.post(webapp_url, json=read_payload, timeout=30)
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                rows = result.get('rows', [])
                print(f"📊 Total rows in sheet: {len(rows)}")
                
                # Look for our test data
                test_address = "123 Test Street, London, SW1A 1AA"
                found_test = False
                
                print(f"\n🔍 Looking for test data: {test_address}")
                print("-" * 50)
                
                for i, row in enumerate(rows[-10:]):  # Check last 10 rows
                    address = row.get('address', '')
                    if test_address in address:
                        found_test = True
                        print(f"✅ Found test data in row {len(rows) - 10 + i + 1}:")
                        print(f"   Address: {row.get('address')}")
                        print(f"   Guide Price: {row.get('guide_price')}")
                        print(f"   Auction URL: {row.get('auction_url')}")
                        print(f"   Auction Sale: {row.get('auction_sale')}")
                        print(f"   Purchase Price: {row.get('purchase_price')}")
                        break
                
                if not found_test:
                    print("❌ Test data not found in the last 10 rows")
                    
                    # Check if there are any recent entries
                    print(f"\n📋 Last 5 entries in sheet:")
                    print("-" * 30)
                    for i, row in enumerate(rows[-5:]):
                        print(f"Row {len(rows) - 5 + i + 1}: {row.get('address', 'No address')} - {row.get('auction_date', 'No date')}")
                
            else:
                print(f"❌ Read failed: {result.get('error')}")
        else:
            print(f"❌ HTTP error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error reading sheet: {e}")

if __name__ == "__main__":
    check_sheet_data() 