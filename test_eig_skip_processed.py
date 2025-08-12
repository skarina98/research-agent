#!/usr/bin/env python3
"""
Test script to verify EIG skip processed auctions functionality
"""

import os
from datetime import datetime, timedelta
from eig import process_auctions_to_sheets

def main():
    """Test the EIG skip processed auctions functionality"""
    
    print("🧪 Testing EIG Skip Processed Auctions")
    print("=" * 50)
    
    # Set environment variables
    os.environ['GOOGLE_SHEETS_ID'] = '1ONZrugWl0amSFqGLq3_hHmR82Bps-vNxr-25gGk8B9Q'
    os.environ['GOOGLE_SHEETS_OAUTH'] = 'true'
    os.environ['GOOGLE_SHEETS_SHARED_TOKEN'] = '3c4ebe48f035fd3f68ccd5c9f619d7aa3f686d2d7637dc54324d979acc066feb'
    
    # Use a date range that includes already processed auctions
    start_date = "2025-03-01"
    end_date = "2025-04-30"
    
    print(f"📅 Testing date range: {start_date} to {end_date}")
    print(f"🎯 This should skip already processed auctions and only process new ones")
    print()
    
    try:
        # Run the workflow
        result = process_auctions_to_sheets(start_date, end_date)
        
        print(f"\n📊 Test Results:")
        print(f"   Status: {result.get('status', 'Unknown')}")
        print(f"   Message: {result.get('message', 'No message')}")
        print(f"   Total Imported: {result.get('total_imported', 0)}")
        print(f"   Total Skipped: {result.get('total_skipped', 0)}")
        print(f"   Auctions Processed: {result.get('auctions_processed', 0)}")
        print(f"   Auctions Skipped: {result.get('auctions_skipped', 0)}")
        
        if result.get('status') == 'already_processed':
            print(f"\n✅ SUCCESS: All auctions were already processed (as expected)")
        elif result.get('auctions_skipped', 0) > 0:
            print(f"\n✅ SUCCESS: Some auctions were skipped (already processed)")
        else:
            print(f"\n⚠️ No auctions were skipped - this might be expected if no auctions were processed before")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 