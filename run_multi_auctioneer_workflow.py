#!/usr/bin/env python3
"""
Multi-Auctioneer EIG Workflow
Usage: python3 run_multi_auctioneer_workflow.py

This workflow processes multiple auctioneers:
1. Auction House London (ID: 680)
2. SDL Auctions (ID: 915)
3. Mchugh & Co (ID: 35)
4. Bonde Wolfe (ID: 984)
5. Auction House South West (ID: 618)
6. Savills (ID: 55)

For each auctioneer:
- Finds auctions in the specified date range
- Extracts lot data from EIG auction pages
- Looks up properties in English House Prices database
- Checks street history for auction-to-auction properties
- Imports properties with auction_sale and/or property_prices data to Google Sheets
"""

import os
import sys
from datetime import datetime, timedelta
from eig import process_auctions_to_sheets
from playwright.sync_api import sync_playwright

# Define all auctioneers to process
AUCTIONEERS = [
    {
        'id': 680,
        'name': 'Auction House London',
        'url': 'https://www.eigpropertyauctions.co.uk/clients/auctions/results?SelectedAuctioneerId=680'
    },
    {
        'id': 915,
        'name': 'SDL Auctions',
        'url': 'https://www.eigpropertyauctions.co.uk/clients/auctions/results?SelectedAuctioneerId=915'
    },
    {
        'id': 35,
        'name': 'Mchugh & Co',
        'url': 'https://www.eigpropertyauctions.co.uk/clients/auctions/results?SelectedAuctioneerId=35'
    },
    {
        'id': 984,
        'name': 'Bonde Wolfe',
        'url': 'https://www.eigpropertyauctions.co.uk/clients/auctions/results?SelectedAuctioneerId=984'
    },
    {
        'id': 618,
        'name': 'Auction House South West',
        'url': 'https://www.eigpropertyauctions.co.uk/clients/auctions/results?SelectedAuctioneerId=618'
    },
    {
        'id': 55,
        'name': 'Savills',
        'url': 'https://www.eigpropertyauctions.co.uk/clients/auctions/results?SelectedAuctioneerId=55'
    }
]

def process_auctioneer(auctioneer, start_date, end_date, page):
    """Process a single auctioneer"""
    print(f"\n{'='*60}")
    print(f"🏢 PROCESSING: {auctioneer['name']} (ID: {auctioneer['id']})")
    print(f"{'='*60}")
    
    try:
        # Navigate to the auctioneer's results page
        print(f"🌐 Navigating to: {auctioneer['url']}")
        page.goto(auctioneer['url'])
        page.wait_for_timeout(3000)
        
        print(f"📄 Page title: {page.title()}")
        print(f"🔗 Current URL: {page.url}")
        
        # Check if we're on a login page
        if "login" in page.title().lower() or "log-in" in page.url.lower():
            print(f"⚠️ Redirected to login page for {auctioneer['name']}")
            print(f"   This auctioneer may require authentication")
            return {
                'auctioneer': auctioneer['name'],
                'status': 'login_required',
                'message': 'Auctioneer requires login authentication'
            }
        
        # Process auctions for this auctioneer
        result = process_auctions_to_sheets(start_date, end_date, page, auctioneer['url'], auctioneer['name'])
        
        # Add auctioneer info to result
        result['auctioneer'] = auctioneer['name']
        result['auctioneer_id'] = auctioneer['id']
        
        return result
        
    except Exception as e:
        print(f"❌ Error processing {auctioneer['name']}: {e}")
        return {
            'auctioneer': auctioneer['name'],
            'status': 'error',
            'message': str(e)
        }

def main():
    """Main function to run the multi-auctioneer workflow"""
    
    print("🚀 Running Multi-Auctioneer EIG Workflow")
    print("=" * 60)
    print(f"📋 Processing {len(AUCTIONEERS)} auctioneers:")
    for auctioneer in AUCTIONEERS:
        print(f"   • {auctioneer['name']} (ID: {auctioneer['id']})")
    print()
    
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
    print(f"🏠 Will check: street history for auction-to-auction properties")
    print(f"📊 Will import: properties with auction_sale and/or property_prices data")
    print()
    
    # Summary tracking
    total_results = []
    successful_auctioneers = 0
    failed_auctioneers = 0
    
    try:
        # Create a browser context for processing
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
            
            # Process each auctioneer
            for i, auctioneer in enumerate(AUCTIONEERS):
                print(f"\n🔄 Processing auctioneer {i+1}/{len(AUCTIONEERS)}")
                
                result = process_auctioneer(auctioneer, start_date, end_date, page)
                total_results.append(result)
                
                # Track success/failure
                if result.get('status') in ['success', 'no_auctions', 'already_processed']:
                    successful_auctioneers += 1
                else:
                    failed_auctioneers += 1
                
                # Add a small delay between auctioneers
                page.wait_for_timeout(2000)
            
            browser.close()
        
        # Print summary
        print(f"\n{'='*60}")
        print("📊 MULTI-AUCTIONEER WORKFLOW SUMMARY")
        print(f"{'='*60}")
        
        for result in total_results:
            auctioneer = result.get('auctioneer', 'Unknown')
            status = result.get('status', 'unknown')
            message = result.get('message', 'No message')
            
            if status == 'success':
                total_imported = result.get('total_imported', 0)
                total_skipped = result.get('total_skipped', 0)
                total_lots_found = result.get('total_lots_found', 0)
                print(f"✅ {auctioneer}: {total_imported} imported, {total_skipped} skipped, {total_lots_found} lots found")
            elif status == 'no_auctions':
                print(f"⚠️ {auctioneer}: No auctions found in date range")
            elif status == 'already_processed':
                print(f"⏭️ {auctioneer}: All auctions already processed")
            elif status == 'login_required':
                print(f"🔒 {auctioneer}: Requires login authentication")
            else:
                print(f"❌ {auctioneer}: {message}")
        
        print(f"\n📈 Overall Results:")
        print(f"   ✅ Successful auctioneers: {successful_auctioneers}/{len(AUCTIONEERS)}")
        print(f"   ❌ Failed auctioneers: {failed_auctioneers}/{len(AUCTIONEERS)}")
        
        print(f"\n🎉 Multi-auctioneer workflow completed!")
        print(f"📊 Check your Google Sheet for imported data from all auctioneers!")
        
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