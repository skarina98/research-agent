#!/usr/bin/env python3
"""
Test Main Workflow Controller Integration

This script tests the integration between the main workflow controller
and the updated Google Apps Script with POTENTIAL_TRADES support.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main_workflow_controller import MainWorkflowController
from sheets_webapp import PropertyDataManagerWebApp

def test_potential_trades_integration():
    """Test POTENTIAL_TRADES functionality"""
    print("🧪 Testing POTENTIAL_TRADES Integration")
    print("=" * 50)
    
    # Initialize components
    controller = MainWorkflowController()
    sheets_manager = PropertyDataManagerWebApp()
    
    # Test data for POTENTIAL_TRADES
    test_property = {
        'auction_name': 'Test Auction Integration',
        'auction_date': '2025-01-15',
        'address': '456 Test Integration Street, London',
        'auction_sale': '£600,000',
        'lot_number': 'INT-001',
        'postcode': 'SW1A 2AA',
        'purchase_price': '',  # Empty - should go to POTENTIAL_TRADES
        'sold_date': '',  # Empty - should go to POTENTIAL_TRADES
        'auction_url': 'https://example.com/auction/integration-test',
        'source_url': '',
        'guide_price': '',
        'owner': '',
        'qa_status': 'pending_enrichment',
        'added_to_potential_trades': '2025-01-15T10:00:00'
    }
    
    print(f"📋 Test Property: {test_property['address']}")
    print(f"   Auction Date: {test_property['auction_date']}")
    print(f"   Purchase Price: {test_property['purchase_price'] or 'Empty'}")
    print()
    
    # Test 1: Add to POTENTIAL_TRADES
    print("🔄 Test 1: Adding to POTENTIAL_TRADES...")
    try:
        success = controller.add_to_potential_trades(test_property)
        if success:
            print("✅ Successfully added to POTENTIAL_TRADES")
        else:
            print("❌ Failed to add to POTENTIAL_TRADES")
    except Exception as e:
        print(f"❌ Error adding to POTENTIAL_TRADES: {e}")
    
    print()
    
    # Test 2: Read from POTENTIAL_TRADES
    print("🔄 Test 2: Reading from POTENTIAL_TRADES...")
    try:
        import requests
        
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
                print(f"✅ Successfully read {len(entries)} entries from POTENTIAL_TRADES")
                
                # Look for our test entry
                test_found = False
                for entry in entries:
                    if (entry.get('address') == test_property['address'] and 
                        entry.get('auction_name') == test_property['auction_name']):
                        test_found = True
                        print(f"✅ Found our test entry in POTENTIAL_TRADES")
                        break
                
                if not test_found:
                    print("⚠️ Test entry not found in POTENTIAL_TRADES")
            else:
                print(f"❌ Failed to read POTENTIAL_TRADES: {result}")
        else:
            print(f"❌ HTTP error reading POTENTIAL_TRADES: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error reading POTENTIAL_TRADES: {e}")
    
    print()
    
    # Test 3: Test categorization logic
    print("🔄 Test 3: Testing auction categorization...")
    
    # Test OLDER auction (3-12 months)
    older_auction_date = '2024-06-15'  # ~7 months ago
    category = controller.categorize_auction_by_date(older_auction_date)
    print(f"   Auction date {older_auction_date}: {category}")
    
    # Test NEWER auction (0-3 months)
    newer_auction_date = '2024-12-15'  # ~1 month ago
    category = controller.categorize_auction_by_date(newer_auction_date)
    print(f"   Auction date {newer_auction_date}: {category}")
    
    # Test SKIP auction (too old)
    skip_auction_date = '2023-01-15'  # ~24 months ago
    category = controller.categorize_auction_by_date(skip_auction_date)
    print(f"   Auction date {skip_auction_date}: {category}")
    
    print()
    
    # Test 4: Test purchase price criteria
    print("🔄 Test 4: Testing purchase price criteria...")
    
    # Test property with purchase price and recent sold date
    property_with_price = {
        'purchase_price': '£550,000',
        'sold_date': '2024-12-01'  # ~1 month ago
    }
    meets_criteria = controller.check_purchase_price_criteria(property_with_price)
    print(f"   Property with price and recent date: {meets_criteria}")
    
    # Test property without purchase price
    property_without_price = {
        'purchase_price': '',
        'sold_date': '2024-12-01'
    }
    meets_criteria = controller.check_purchase_price_criteria(property_without_price)
    print(f"   Property without price: {meets_criteria}")
    
    # Test property with old sold date
    property_old_date = {
        'purchase_price': '£550,000',
        'sold_date': '2023-06-01'  # ~18 months ago
    }
    meets_criteria = controller.check_purchase_price_criteria(property_old_date)
    print(f"   Property with old sold date: {meets_criteria}")
    
    print()
    print("✅ Integration test completed!")

def test_auction_master_integration():
    """Test AUCTION_MASTER functionality"""
    print("\n🧪 Testing AUCTION_MASTER Integration")
    print("=" * 50)
    
    sheets_manager = PropertyDataManagerWebApp()
    
    # Test data for AUCTION_MASTER
    test_property = {
        'auction_name': 'Test Auction Master',
        'auction_date': '2024-06-15',
        'address': '789 Test Master Street, London',
        'auction_sale': '£700,000',
        'lot_number': 'MASTER-001',
        'postcode': 'SW1A 3AA',
        'purchase_price': '£680,000',
        'sold_date': '2024-12-01',
        'auction_url': 'https://example.com/auction/master-test',
        'source_url': '',
        'guide_price': '£650,000',
        'owner': '',
        'qa_status': 'enriched'
    }
    
    print(f"📋 Test Property: {test_property['address']}")
    print(f"   Purchase Price: {test_property['purchase_price']}")
    print(f"   Sold Date: {test_property['sold_date']}")
    print()
    
    # Test adding to AUCTION_MASTER
    print("🔄 Adding to AUCTION_MASTER...")
    try:
        success = sheets_manager.add_property(test_property)
        if success:
            print("✅ Successfully added to AUCTION_MASTER")
        else:
            print("❌ Failed to add to AUCTION_MASTER")
    except Exception as e:
        print(f"❌ Error adding to AUCTION_MASTER: {e}")
    
    print()
    print("✅ AUCTION_MASTER test completed!")

if __name__ == "__main__":
    print("🚀 Starting Main Workflow Integration Tests")
    print("=" * 60)
    
    # Test POTENTIAL_TRADES integration
    test_potential_trades_integration()
    
    # Test AUCTION_MASTER integration
    test_auction_master_integration()
    
    print("\n🎉 All integration tests completed!") 