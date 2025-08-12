#!/usr/bin/env python3
"""
Direct script to run the full auction workflow
Usage: python3 run_auction_workflow.py
"""

import os
import sys
from datetime import datetime, timedelta
from eig import process_auctions_to_sheets

def main():
    """Main function to run the auction workflow"""
    
    print("🚀 Running Full Auction Workflow")
    print("=" * 40)
    
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
    print()
    
    try:
        # Run the full workflow
        print("🔄 Starting auction processing and import to Google Sheets...")
        print("   (This will import each lot immediately when a property prices match is found)")
        print()
        
        result = process_auctions_to_sheets(start_date, end_date)
        
        print()
        print("=" * 40)
        print("🎉 WORKFLOW COMPLETE!")
        print("=" * 40)
        print(f"📊 Check your Google Sheet for imported data!")
        print()
        print("✅ The auction workflow has completed successfully!")
        
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