#!/usr/bin/env python3
"""
Cleanup and Categorize Data

This script will:
1. Read all data from POTENTIAL_TRADES
2. Categorize entries based on our logic
3. Move appropriate entries to AUCTION_MASTER
4. Clean up POTENTIAL_TRADES to only contain entries that should be there
"""

import sys
import os
import requests
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sheets_webapp import PropertyDataManagerWebApp
from main_workflow_controller import MainWorkflowController

def categorize_entry_by_date(auction_date_str):
    """Categorize auction as OLDER (3-12 months) or NEWER (0-3 months)"""
    try:
        auction_date = datetime.strptime(auction_date_str.split('T')[0], '%Y-%m-%d')
        current_date = datetime.now()
        
        # Calculate months difference
        date_diff = relativedelta(current_date, auction_date)
        months_diff = date_diff.years * 12 + date_diff.months
        
        if months_diff >= 3 and months_diff <= 12:
            return 'OLDER'
        elif months_diff >= 0 and months_diff < 3:
            return 'NEWER'
        else:
            return 'SKIP'
            
    except Exception as e:
        print(f"   ❌ Error categorizing auction date: {e}")
        return 'SKIP'

def check_purchase_price_criteria(entry):
    """Check if property meets purchase price criteria"""
    purchase_price = entry.get('purchase_price', '')
    sold_date = entry.get('sold_date', '')
    
    # Check if purchase price exists and is not empty
    has_purchase_price = purchase_price and str(purchase_price).strip() and str(purchase_price) != 'Not found'
    
    if not has_purchase_price:
        return False
    
    # Check if sold date is within 6 months
    if sold_date:
        try:
            sold_date_obj = datetime.strptime(sold_date.split('T')[0], '%Y-%m-%d')
            current_date = datetime.now()
            
            date_diff = relativedelta(current_date, sold_date_obj)
            months_diff = date_diff.years * 12 + date_diff.months
            
            if months_diff < 6:
                return True
            else:
                return False
                
        except Exception as e:
            print(f"   ⚠️ Error parsing sold date: {e}")
            return False
    else:
        return False

def cleanup_and_categorize():
    """Main cleanup and categorization function"""
    print("🧹 Starting Data Cleanup and Categorization")
    print("=" * 60)
    
    # Initialize components
    sheets_manager = PropertyDataManagerWebApp()
    controller = MainWorkflowController()
    
    try:
        # Step 1: Read all data from POTENTIAL_TRADES
        print("\n📊 Step 1: Reading all data from POTENTIAL_TRADES...")
        
        payload = {
            'token': sheets_manager.shared_token,
            'action': 'read',
            'sheet_name': 'POTENTIAL_TRADES'
        }
        
        response = requests.post(sheets_manager.webapp_url, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Failed to read POTENTIAL_TRADES: {response.status_code}")
            return
        
        result = response.json()
        if not result.get('ok'):
            print(f"❌ Failed to read POTENTIAL_TRADES: {result}")
            return
        
        entries = result.get('rows', [])
        print(f"✅ Found {len(entries)} entries in POTENTIAL_TRADES")
        
        # Step 2: Categorize entries
        print("\n🔄 Step 2: Categorizing entries...")
        
        to_auction_master = []
        to_potential_trades = []
        to_delete = []
        
        for i, entry in enumerate(entries):
            address = entry.get('address', 'Unknown')
            auction_date = entry.get('auction_date', '')
            
            print(f"   Processing {i+1}/{len(entries)}: {address}")
            
            # Skip test entries
            if 'Test' in address or 'Debug' in address:
                print(f"     ⏭️ Skipping test entry")
                to_delete.append(entry)
                continue
            
            # Categorize by date
            if auction_date:
                category = categorize_entry_by_date(auction_date)
                print(f"     📅 Category: {category}")
            else:
                print(f"     ⚠️ No auction date")
                to_delete.append(entry)
                continue
            
            # Check purchase price criteria
            meets_criteria = check_purchase_price_criteria(entry)
            print(f"     💰 Meets purchase price criteria: {meets_criteria}")
            
            # Decision logic
            if category == 'OLDER':
                if meets_criteria:
                    print(f"     ✅ Moving to AUCTION_MASTER (OLDER + meets criteria)")
                    to_auction_master.append(entry)
                else:
                    print(f"     ⏭️ Keeping in POTENTIAL_TRADES (OLDER + doesn't meet criteria)")
                    # Update the entry with proper timestamp
                    entry['added_to_potential_trades'] = datetime.now().isoformat()
                    to_potential_trades.append(entry)
            elif category == 'NEWER':
                if meets_criteria:
                    print(f"     ✅ Moving to AUCTION_MASTER (NEWER + meets criteria)")
                    to_auction_master.append(entry)
                else:
                    print(f"     ⏭️ Keeping in POTENTIAL_TRADES (NEWER + doesn't meet criteria)")
                    # Update the entry with proper timestamp
                    entry['added_to_potential_trades'] = datetime.now().isoformat()
                    to_potential_trades.append(entry)
            else:  # SKIP
                print(f"     🗑️ Marking for deletion (outside date range)")
                to_delete.append(entry)
        
        # Step 3: Summary
        print(f"\n📊 Categorization Summary:")
        print(f"   To AUCTION_MASTER: {len(to_auction_master)}")
        print(f"   To POTENTIAL_TRADES: {len(to_potential_trades)}")
        print(f"   To DELETE: {len(to_delete)}")
        
        # Step 4: Move entries to AUCTION_MASTER
        if to_auction_master:
            print(f"\n🔄 Step 3: Moving {len(to_auction_master)} entries to AUCTION_MASTER...")
            
            for entry in to_auction_master:
                try:
                    # Prepare entry for AUCTION_MASTER
                    auction_master_entry = {
                        'auction_name': entry.get('auction_name', ''),
                        'auction_date': entry.get('auction_date', ''),
                        'address': entry.get('address', ''),
                        'auction_sale': entry.get('auction_sale', ''),
                        'lot_number': entry.get('lot_number', ''),
                        'postcode': entry.get('postcode', ''),
                        'purchase_price': entry.get('purchase_price', ''),
                        'sold_date': entry.get('sold_date', ''),
                        'auction_url': entry.get('auction_url', ''),
                        'source_url': entry.get('source_url', ''),
                        'guide_price': entry.get('guide_price', ''),
                        'owner': entry.get('owner', ''),
                        'qa_status': 'categorized',
                        'ingested_at': datetime.now().isoformat()
                    }
                    
                    success = sheets_manager.add_property(auction_master_entry)
                    if success:
                        print(f"     ✅ Moved: {entry.get('address', 'Unknown')}")
                    else:
                        print(f"     ❌ Failed to move: {entry.get('address', 'Unknown')}")
                        
                except Exception as e:
                    print(f"     ❌ Error moving entry: {e}")
        
        # Step 5: Clear POTENTIAL_TRADES and add back only appropriate entries
        print(f"\n🔄 Step 4: Clearing POTENTIAL_TRADES and adding back {len(to_potential_trades)} entries...")
        
        # Note: We can't easily clear the entire sheet via API, so we'll need to do this manually
        # For now, let's just add the properly categorized entries
        
        if to_potential_trades:
            # Add entries to POTENTIAL_TRADES with proper structure
            payload = {
                'token': sheets_manager.shared_token,
                'action': 'add',
                'sheet_name': 'POTENTIAL_TRADES',
                'rows': []
            }
            
            for entry in to_potential_trades:
                payload['rows'].append({
                    'auction_name': entry.get('auction_name', ''),
                    'auction_date': entry.get('auction_date', ''),
                    'address': entry.get('address', ''),
                    'auction_sale': entry.get('auction_sale', ''),
                    'lot_number': entry.get('lot_number', ''),
                    'postcode': entry.get('postcode', ''),
                    'purchase_price': entry.get('purchase_price', ''),
                    'sold_date': entry.get('sold_date', ''),
                    'auction_url': entry.get('auction_url', ''),
                    'source_url': entry.get('source_url', ''),
                    'guide_price': entry.get('guide_price', ''),
                    'owner': entry.get('owner', ''),
                    'qa_status': 'pending_enrichment',
                    'added_to_potential_trades': entry.get('added_to_potential_trades', ''),
                    'ingested_at': datetime.now().isoformat()
                })
            
            response = requests.post(sheets_manager.webapp_url, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    print(f"     ✅ Added {len(to_potential_trades)} entries to POTENTIAL_TRADES")
                else:
                    print(f"     ❌ Failed to add to POTENTIAL_TRADES: {result}")
            else:
                print(f"     ❌ HTTP error: {response.status_code}")
        
        print(f"\n✅ Cleanup and categorization completed!")
        print(f"   📊 Final Summary:")
        print(f"     - Moved to AUCTION_MASTER: {len(to_auction_master)}")
        print(f"     - Kept in POTENTIAL_TRADES: {len(to_potential_trades)}")
        print(f"     - Marked for deletion: {len(to_delete)}")
        print(f"\n   ⚠️ Note: You may need to manually clear the old POTENTIAL_TRADES data")
        print(f"   since the API doesn't support bulk deletion.")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    cleanup_and_categorize() 