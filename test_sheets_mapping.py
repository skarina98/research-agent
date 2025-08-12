#!/usr/bin/env python3
"""
Test script to verify sheets mapping
"""

import os
from sheets_webapp import PropertyDataManagerWebApp

def main():
    """Test the sheets mapping"""
    
    print("🔧 Testing sheets mapping")
    print("=" * 40)
    
    # Set environment variables
    os.environ['GOOGLE_SHEETS_ID'] = '1ONZrugWl0amSFqGLq3_hHmR82Bps-vNxr-25gGk8B9Q'
    os.environ['GOOGLE_SHEETS_OAUTH'] = 'true'
    os.environ['GOOGLE_SHEETS_SHARED_TOKEN'] = '3c4ebe48f035fd3f68ccd5c9f619d7aa3f686d2d7637dc54324d979acc066feb'
    
    # Create test property data
    test_property = {
        'auction_name': 'Test Auction',
        'auction_date': '2025-03-15',
        'address': '123 Test Street, London, SW1A 1AA',
        'price_bought': '£500,000',  # This should be mapped to price-bought
        'lot_number': '999',
        'postcode': 'SW1A 1AA',
        'sold_price': '£550,000',
        'sold_date': '15/03/2025',
        'auction_url': 'https://test-auction.com',
        'property_prices_status': 'found'
    }
    
    print(f"📋 Test property data:")
    for key, value in test_property.items():
        print(f"   {key}: {value}")
    
    print(f"\n🔧 Testing sheets mapping...")
    
    # Initialize sheets manager
    sheets_manager = PropertyDataManagerWebApp()
    
    # Test the mapping
    try:
        result = sheets_manager.process_property_data(test_property)
        print(f"\n📊 Result: {result}")
        
        if result.get('status') == 'success':
            print(f"✅ Test successful!")
        else:
            print(f"❌ Test failed: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 