#!/usr/bin/env python3
"""
Test date formatting integration in sheets_webapp
"""

from sheets_webapp import PropertyDataManagerWebApp

def test_date_formatting():
    """Test that dates are properly formatted when adding properties"""
    
    # Create a test property with ISO timestamps
    test_property = {
        'auction_name': 'Test Auction',
        'auction_date': '2025-08-05T23:00:00.000Z',
        'address': '123 Test Street',
        'auction_sale': 'Sold for £200,000',
        'profit': '£50,000',
        'lot_number': '123',
        'postcode': 'AB12 3CD',
        'purchase_price': '£150,000',
        'sold_date': '2025-07-02T23:00:00.000Z',
        'guide_price': '£180,000',
        'auction_url': 'https://example.com/auction',
        'source_url': '',
        'qa_status': 'imported',
        'ingested_at': '2025-05-27T23:00:00.000Z',
        'transaction_type': 'auction to auction',
        'eig_street_history_url': 'https://example.com/street-history'
    }
    
    print("🧪 Testing Date Formatting Integration")
    print("=" * 50)
    
    # Create property manager instance
    manager = PropertyDataManagerWebApp()
    
    print("\n📋 Original Property Data:")
    for key, value in test_property.items():
        if 'date' in key.lower() or 'ingested' in key.lower():
            print(f"   {key}: {value}")
    
    print("\n🔧 Testing format_property_dates method:")
    formatted_property = manager.format_property_dates(test_property)
    
    print("\n✨ Formatted Property Data:")
    for key, value in formatted_property.items():
        if 'date' in key.lower() or 'ingested' in key.lower():
            print(f"   {key}: {value}")
    
    print("\n✅ Date Formatting Test Complete!")
    
    # Verify the formatting worked
    expected_formats = {
        'auction_date': '2025-08-05',
        'sold_date': '2025-07-02', 
        'ingested_at': '2025-05-27'
    }
    
    print("\n🔍 Verification:")
    all_correct = True
    for field, expected in expected_formats.items():
        actual = formatted_property.get(field, '')
        if actual == expected:
            print(f"   ✅ {field}: {actual}")
        else:
            print(f"   ❌ {field}: expected {expected}, got {actual}")
            all_correct = False
    
    if all_correct:
        print("\n🎉 All dates formatted correctly!")
    else:
        print("\n⚠️ Some dates were not formatted correctly!")
    
    return all_correct

if __name__ == "__main__":
    test_date_formatting() 