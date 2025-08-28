#!/usr/bin/env python3
"""
EIG-Only Workflow - No Searchland Integration
Usage: python3 run_eig_only_workflow.py

This workflow:
1. Finds auctions in the specified date range
2. Extracts lot data from EIG auction pages
3. Looks up properties in English House Prices database
4. Imports properties with both auction_sale and purchase_price data to Google Sheets
5. Skips Searchland integration entirely
"""

import os
import sys
from datetime import datetime, timedelta
from eig import process_auctions_to_sheets

def main():
    """Main function to run the EIG-only auction workflow"""
    
    print("🚀 Running EIG-Only Auction Workflow (No Searchland)")
    print("=" * 50)
    
    # Set environment variables for Google Sheets
    os.environ['GOOGLE_SHEETS_ID'] = '1ONZrugWl0amSFqGLq3_hHmR82Bps-vNxr-25gGk8B9Q'
    os.environ['GOOGLE_SHEETS_OAUTH'] = 'true'
    os.environ['GOOGLE_SHEETS_SHARED_TOKEN'] = '3c4ebe48f035fd3f68ccd5c9f619d7aa3f686d2d7637dc54324d979acc066feb'
    
    # Calculate date range: 3-12 months ago
    today = datetime.today()
    start_date = (today - timedelta(days=365)).strftime("%Y-%m-%d")  # 12 months ago
    end_date = (today - timedelta(days=90)).strftime("%Y-%m-%d")     # 3 months ago
    
    print(f"📅 Date range: {start_date} to {end_date}")
    print(f"🎯 Looking for auctions from 3-12 months ago")
    print(f"🔍 Will extract: auction_sale, purchase_price, guide_price")
    print(f"⏭️ Will skip: Searchland owner/guide price enrichment")
    print()
    
    try:
        # Run the EIG-only workflow
        print("🔄 Starting EIG auction processing and import to Google Sheets...")
        print("   (This will import each lot immediately when a property prices match is found)")
        print("   (No Searchland integration - owner and listing data will be empty)")
        print()
        
        # Create a browser context for street history checking
        from playwright.sync_api import sync_playwright
        import os
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            
            # Check if session file exists, otherwise create context without it
            session_file = "sessions/eig.json"
            if os.path.exists(session_file):
                print("Using existing EIG session file for authentication")
                context = browser.new_context(storage_state=session_file)
            else:
                print("No EIG session file found, creating new context")
                context = browser.new_context()
                
            page = context.new_page()
            
            try:
                result = process_auctions_to_sheets(start_date, end_date, page)
            finally:
                browser.close()
        
        print()
        print("=" * 50)
        print("🎉 EIG-ONLY WORKFLOW COMPLETE!")
        print("=" * 50)
        print(f"📊 Check your Google Sheet for imported data!")
        print(f"📋 Imported data includes:")
        print(f"   ✅ auction_name, auction_date, address")
        print(f"   ✅ auction_sale (from EIG auction listing)")
        print(f"   ✅ purchase_price (from property prices database)")
        print(f"   ✅ guide_price (from EIG catalogue entry)")
        print(f"   ✅ lot_number, postcode, sold_date, auction_url")
        print(f"   ⏭️ owner: empty (no Searchland integration)")
        print(f"   ⏭️ listing_link: empty (no Searchland integration)")
        print()
        print("✅ The EIG-only workflow has completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⚠️ Workflow interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during workflow: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 