#!/usr/bin/env python3
"""
Simple test to just add one row
"""

import json
import requests
from datetime import datetime

# Google Apps Script web app URL
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzlSrRZ-Rje7aA_CPOJB00Onf0r_gTiVKUt_FqZwoVssKzcAFEWt5smekN6ddLHIOgv/exec"

# Test token
TOKEN = "3c4ebe48f035fd3f68ccd5c9f619d7aa3f686d2d7637dc54324d979acc066feb"

def test_simple_add():
    """Simple test to add one row"""
    
    print("🧪 Simple Add Test")
    print("=" * 20)
    
    # Test data - should go to POTENTIAL_TRADES (no purchase price)
    test_data = {
        "auction_name": "Simple Test Auction",
        "auction_date": "2025-08-05T23:00:00.000Z",
        "address": "Simple Test Property",
        "auction_sale": "Sold for £100,000",
        "profit": "£10,000",
        "lot_number": "SIMPLE-001",
        "postcode": "AB12 3CD",
        "purchase_price": "",  # No purchase price = POTENTIAL_TRADES
        "sold_date": "2025-03-15T00:00:00.000Z",
        "transaction_type": "estate agent to auction",
        "eig_street_history_url": "",
        "guide_price": "£100,000",
        "source_url": "https://example.com",
        "auction_url": "https://example.com/auction",
        "qa_status": "test",
        "ingested_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    try:
        print("\nAdding one row with lot_number SIMPLE-001")
        payload = {
            'token': TOKEN,
            'action': 'add',
            'rows': [test_data]
        }
        
        response = requests.post(WEBAPP_URL, json=payload, timeout=30)
        result = response.json()
        
        if result.get('ok'):
            print(f"   ✅ Success: Added {result.get('added', 0)}, Updated {result.get('updated', 0)}, Skipped {result.get('skipped', 0)}")
            if result.get('added', 0) > 0:
                print("   🎯 Correct: Row was added successfully")
            elif result.get('updated', 0) > 0:
                print("   ⚠️ Warning: Row was updated instead of added")
            elif result.get('skipped', 0) > 0:
                print("   ⚠️ Warning: Row was skipped instead of added")
        else:
            print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_simple_add() 