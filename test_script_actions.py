#!/usr/bin/env python3
"""
Test what actions the Google Apps Script supports
"""

import requests
import json

def test_script_actions():
    """Test different actions on the Google Apps Script"""
    
    webapp_url = "https://script.google.com/macros/s/AKfycbxkTm30lbe0G3gMl2EAoNbpp2BF0uLJ1JIp-2vg8sxfe7xl56Gw4NvlbMS8FiC7paO6/exec"
    token = "3c4ebe48f035fd3f68ccd5c9f619d7aa3f686d2d7637dc54324d979acc066feb"
    
    print("🧪 Testing Google Apps Script Actions")
    print("=" * 50)
    
    # Test 1: Read action
    print("\n1️⃣ Testing 'read' action...")
    read_payload = {
        "token": token,
        "action": "read"
    }
    
    try:
        response = requests.post(webapp_url, json=read_payload, timeout=30)
        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ 'read' action works!")
            else:
                print(f"❌ 'read' action failed: {result.get('error')}")
        else:
            print(f"❌ HTTP error: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing 'read': {e}")
    
    # Test 2: Add action
    print("\n2️⃣ Testing 'add' action...")
    add_payload = {
        "token": token,
        "action": "add",
        "rows": [{
            "auction_name": "Test Auction",
            "auction_date": "2025-04-24",
            "address": "Test Address",
            "auction_sale": "£100,000",
            "lot_number": "999",
            "postcode": "TEST 1AA",
            "purchase_price": "£95,000",
            "sold_date": "2025-04-20",
            "owner": "",
            "guide_price": "£90,000",
            "auction_url": "https://test.com",
            "source_url": "",
            "qa_status": "test",
            "ingested_at": "2025-08-13T19:50:00"
        }]
    }
    
    try:
        response = requests.post(webapp_url, json=add_payload, timeout=30)
        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ 'add' action works!")
            else:
                print(f"❌ 'add' action failed: {result.get('error')}")
        else:
            print(f"❌ HTTP error: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing 'add': {e}")
    
    # Test 3: Update action
    print("\n3️⃣ Testing 'update_row' action...")
    update_payload = {
        "token": token,
        "action": "update_row",
        "row_data": {
            "auction_name": "Test Auction",
            "auction_date": "2025-04-24",
            "address": "Test Address",
            "guide_price": "£95,000",
            "source_url": "https://test-update.com"
        }
    }
    
    try:
        response = requests.post(webapp_url, json=update_payload, timeout=30)
        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ 'update_row' action works!")
            else:
                print(f"❌ 'update_row' action failed: {result.get('error')}")
        else:
            print(f"❌ HTTP error: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing 'update_row': {e}")
    
    print("\n✅ Action testing completed!")

if __name__ == "__main__":
    test_script_actions() 