#!/usr/bin/env python3
"""
Test guide price extraction logic
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from run_listing_enrichment_workflow import ListingEnrichmentWorkflow

def test_guide_price_extraction():
    """Test that guide price is extracted even when timeline has no usable data"""
    
    print("🧪 Testing Guide Price Extraction Logic")
    print("=" * 50)
    
    # Create a test row
    test_row = {
        'auction_name': 'EIG Property Auctions',  # Real auction name for timeline testing
        'auction_date': '2025-04-24',
        'address': 'Test Property Address',  # Will be updated based on PropertyEngine results
        'auction_sale': '£200,000',
        'guide_price': '',  # Missing - this is what we're looking for
        'lot_number': '999',
        'postcode': 'TEST',
        'purchase_price': '£190,000',
        'sold_date': '2025-04-20',
        'auction_url': 'https://www.eigpropertyauctions.co.uk/lot/test-999',
        'source_url': '',  # Missing - this is what we're looking for
        'owner': '',
        'qa_status': 'test'
    }
    
    print(f"📋 Test Address: {test_row['address']}")
    print(f"   Missing guide_price: {not test_row['guide_price']}")
    print(f"   Missing source_url: {not test_row['source_url']}")
    print()
    
    # Initialize workflow
    workflow = ListingEnrichmentWorkflow()
    
    try:
        # Start browser
        workflow.start_browser()
        
        # Test PropertyEngine extraction directly with a known URL
        test_url = "https://www.rightmove.co.uk/properties/160421669#/?channel=RES_BUY"
        print(f"🔍 Testing PropertyEngine extraction with: {test_url}")
        
        result = workflow.extract_from_propertyengine(test_url, test_row['auction_name'], test_row['auction_date'])
        
        if result:
            print(f"✅ Successfully extracted data from PropertyEngine!")
            print(f"   Source URL: {result.get('source_url', 'Not found')}")
            print(f"   Guide Price: {result.get('guide_price', 'Not found')}")
            
            # Test the update logic
            print(f"\n🔄 Testing spreadsheet update logic...")
            update_success = workflow.update_spreadsheet_row(test_row, result)
            
            if update_success:
                print(f"✅ Successfully updated spreadsheet")
                print(f"   Updated guide_price: {test_row.get('guide_price', 'Not found')}")
                print(f"   Updated source_url: {test_row.get('source_url', 'Not found')}")
            else:
                print(f"❌ Failed to update spreadsheet")
        else:
            print(f"❌ Failed to extract data from PropertyEngine")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        workflow.close_browser()
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    test_guide_price_extraction() 