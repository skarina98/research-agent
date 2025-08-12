#!/usr/bin/env python3
"""
Test script for Searchland functionality
"""

import asyncio
import os
from searchland_processor import SearchlandSheetProcessor

async def test_searchland():
    """Test Searchland functionality"""
    
    print("🧪 Testing Searchland functionality")
    print("=" * 40)
    
    # Set environment variables
    os.environ['GOOGLE_SHEETS_ID'] = '1ONZrugWl0amSFqGLq3_hHmR82Bps-vNxr-25gGk8B9Q'
    os.environ['GOOGLE_SHEETS_OAUTH'] = 'true'
    os.environ['GOOGLE_SHEETS_SHARED_TOKEN'] = '3c4ebe48f035fd3f68ccd5c9f619d7aa3f686d2d7637dc54324d979acc066feb'
    
    processor = SearchlandSheetProcessor()
    
    # Test with a sample address
    test_address = "7 Haylands Square, South Shields"
    test_postcode = "NE34 0JB"
    
    print(f"🔍 Testing Searchland search for: {test_address}, {test_postcode}")
    
    try:
        # Test the search functionality
        result = await processor.search_property_in_searchland(test_address, test_postcode)
        
        if result:
            print(f"✅ Search successful!")
            print(f"   Owner: {result.get('owner_name', 'Not found')}")
            print(f"   Guide Price: {result.get('guide_price', 'Not found')}")
            print(f"   Listing Link: {result.get('listing_link', 'Not found')}")
            print(f"   Status: {result.get('extraction_status', 'Unknown')}")
        else:
            print(f"❌ Search failed")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_searchland()) 