#!/usr/bin/env python3
"""
Script to run the Searchland workflow
Processes Google Sheet data and updates with Searchland information
"""

import asyncio
import os
from searchland_processor import SearchlandSheetProcessor

async def main():
    """Main function to run Searchland workflow"""
    
    print("🚀 Running Searchland Workflow")
    print("=" * 40)
    
    # Set environment variables
    os.environ['GOOGLE_SHEETS_ID'] = '1ONZrugWl0amSFqGLq3_hHmR82Bps-vNxr-25gGk8B9Q'
    os.environ['GOOGLE_SHEETS_OAUTH'] = 'true'
    os.environ['GOOGLE_SHEETS_SHARED_TOKEN'] = '3c4ebe48f035fd3f68ccd5c9f619d7aa3f686d2d7637dc54324d979acc066feb'
    
    print("📋 This script will:")
    print("   1. Read data from your Google Sheet")
    print("   2. For each row, search the address in Searchland")
    print("   3. Extract owner name from ownership tab")
    print("   4. Extract guide price from residential sales tab")
    print("   5. Get the listing link")
    print("   6. Update the Google Sheet with this data")
    print()
    
    try:
        # Initialize processor
        processor = SearchlandSheetProcessor()
        
        # Process the Google Sheet data
        await processor.process_google_sheet_data()
        
        print()
        print("🎉 Searchland workflow completed!")
        
    except KeyboardInterrupt:
        print("\n⚠️ Workflow interrupted by user")
    except Exception as e:
        print(f"❌ Error during workflow: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 