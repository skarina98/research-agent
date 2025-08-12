#!/usr/bin/env python3
"""
Simple test for Searchland search functionality
"""

import asyncio
import os
from searchland_processor import SearchlandSheetProcessor

async def test_searchland_simple():
    """Test Searchland search with a simple address"""
    
    print("🧪 Simple Searchland Test")
    print("=" * 30)
    
    # Initialize the processor
    processor = SearchlandSheetProcessor()
    
    # Test with a common London address
    test_address = "123 Oxford Street"
    test_postcode = "W1D 2JD"
    
    print(f"🔍 Testing search for: {test_address}, {test_postcode}")
    
    # Test the search functionality
    result = await processor.search_property_in_searchland(test_address, test_postcode)
    
    if result:
        print(f"✅ Search successful!")
        print(f"   Owner: {result.get('owner_name', 'Not found')}")
        print(f"   Guide Price: {result.get('guide_price', 'Not found')}")
        print(f"   Listing Link: {result.get('listing_link', 'Not found')}")
    else:
        print(f"❌ Search failed or no results found")
        print(f"   This could be normal if the address doesn't exist in Searchland")

if __name__ == "__main__":
    asyncio.run(test_searchland_simple()) 