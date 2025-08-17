#!/usr/bin/env python3
"""
Test script to verify the new Google Apps Script URL is working correctly
"""

from sheets_webapp import PropertyDataManagerWebApp
import json

def test_new_url():
    """Test the new Google Apps Script URL"""
    print("🧪 Testing new Google Apps Script URL...")
    print("=" * 50)
    
    # Initialize the manager with the new URL
    manager = PropertyDataManagerWebApp()
    
    print(f"🌐 Using URL: {manager.webapp_url}")
    print(f"🔐 Token: {manager.shared_token[:10] if manager.shared_token else 'None'}...")
    
    # Test reading from AUCTIONS_MASTER
    print("\n📖 Testing read from AUCTIONS_MASTER...")
    try:
        import requests
        
        # Test GET request to read data
        response = requests.get(
            manager.webapp_url,
            params={
                'sheet_name': 'AUCTIONS_MASTER',
                'limit': 5
            },
            timeout=30
        )
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Found {result.get('total', 0)} total rows")
            print(f"📊 Returned {result.get('returned', 0)} rows")
            print(f"📋 Sheet name: {result.get('sheet_name', 'Unknown')}")
            
            if result.get('rows'):
                print("\n📋 Sample data:")
                for i, row in enumerate(result['rows'][:3]):
                    print(f"  {i+1}. {row.get('address', 'No address')} - {row.get('auction_sale', 'No sale price')}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing read: {e}")
    
    # Test adding a test property to POTENTIAL_TRADES
    print("\n📝 Testing add to POTENTIAL_TRADES...")
    test_property = {
        'auction_name': 'Test Auction',
        'auction_date': '2025-01-15',
        'address': '123 Test Street, London',
        'auction_sale': '£500,000',
        'lot_number': 'TEST123',
        'postcode': 'SW1A 1AA',
        'purchase_price': '',
        'sold_date': '',
        'guide_price': '',
        'auction_url': 'https://example.com/test',
        'source_url': '',
        'qa_status': 'test',
        'added_to_potential_trades': '2025-01-15T10:00:00Z',
        'ingested_at': '2025-01-15T10:00:00Z'
    }
    
    try:
        # Test POST request to add data to POTENTIAL_TRADES
        payload = {
            'token': manager.shared_token,
            'action': 'add',
            'sheet_name': 'POTENTIAL_TRADES',
            'rows': [test_property]
        }
        
        response = requests.post(manager.webapp_url, json=payload, timeout=30)
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📥 Response: {json.dumps(result, indent=2)}")
            
            if result.get('ok'):
                print(f"✅ Successfully added test property to POTENTIAL_TRADES")
                print(f"📊 Added {result.get('count', 0)} rows")
                print(f"📋 Sheet name: {result.get('sheet_name', 'Unknown')}")
            else:
                print(f"❌ Error: {result.get('error', 'Unknown error')}")
        else:
            print(f"❌ HTTP Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing add: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Test completed!")

if __name__ == "__main__":
    test_new_url() 