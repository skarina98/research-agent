#!/usr/bin/env python3
"""
Update the existing enriched row with the correct PropertyEngine URL
"""

import os
import sys
import requests
from sheets_webapp import PropertyDataManagerWebApp

def update_enriched_row():
    """Update the existing enriched row with the correct PropertyEngine URL"""
    sheets_manager = PropertyDataManagerWebApp()
    
    print("🔄 Updating enriched row with correct PropertyEngine URL")
    print("=" * 60)
    
    # The correct PropertyEngine URL we found
    correct_propertyengine_url = "https://propertyengine.co.uk/property/lIa9rTdci"
    correct_guide_price = "£145,000"
    
    try:
        # Get fresh data from Google Sheet
        webapp_url = sheets_manager.webapp_url
        shared_token = sheets_manager.shared_token
        
        payload = {
            'token': shared_token,
            'action': 'read',
            'sheet_id': os.getenv('GOOGLE_SHEETS_ID', '1ONZrugWl0amSFqGLq3_hHmR82Bps-vNxr-25gGk8B9Q')
        }
        
        response = requests.post(webapp_url, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            if result.get('ok') and result.get('rows'):
                rows = result.get('rows', [])
                print(f"✅ Successfully fetched {len(rows)} rows from Google Sheet")
                
                # Find the enriched row for 26 Cromwell Terrace, Lot 50
                target_address = "26 Cromwell Terrace, Chatham, ME4 5PQ"
                enriched_row = None
                enriched_row_index = None
                
                for i, row in enumerate(rows):
                    address = row.get('address', '')
                    qa_status = row.get('qa_status', '')
                    lot_number = row.get('lot_number', '')
                    
                    if (target_address.lower() in address.lower() and 
                        qa_status == 'enriched' and 
                        lot_number == '50'):
                        enriched_row = row
                        enriched_row_index = i
                        print(f"📋 Found enriched row at index {i+1}: {address}")
                        break
                
                if enriched_row:
                    print(f"\n📋 Current enriched row data:")
                    print(f"   Address: {enriched_row.get('address', 'N/A')}")
                    print(f"   Guide Price: {enriched_row.get('guide_price', 'N/A')}")
                    print(f"   Source URL: {enriched_row.get('source_url', 'N/A')}")
                    print(f"   QA Status: {enriched_row.get('qa_status', 'N/A')}")
                    
                    # Check if it needs updating
                    current_source_url = enriched_row.get('source_url', '')
                    current_guide_price = enriched_row.get('guide_price', '')
                    
                    if (current_source_url != correct_propertyengine_url or 
                        current_guide_price != correct_guide_price):
                        print(f"\n🔄 Row needs updating:")
                        print(f"   Current source_url: {current_source_url}")
                        print(f"   Correct source_url: {correct_propertyengine_url}")
                        print(f"   Current guide_price: {current_guide_price}")
                        print(f"   Correct guide_price: {correct_guide_price}")
                        
                        # Create updated row data
                        updated_row_data = {
                            'auction_name': enriched_row.get('auction_name', ''),
                            'auction_date': enriched_row.get('auction_date', ''),
                            'address': enriched_row.get('address', ''),
                            'auction_sale': enriched_row.get('auction_sale', ''),
                            'lot_number': enriched_row.get('lot_number', ''),
                            'postcode': enriched_row.get('postcode', ''),
                            'purchase_price': enriched_row.get('purchase_price', ''),
                            'sold_date': enriched_row.get('sold_date', ''),
                            'auction_url': enriched_row.get('auction_url', ''),
                            'source_url': correct_propertyengine_url,
                            'guide_price': correct_guide_price,
                            'qa_status': 'enriched'
                        }
                        
                        # Add the updated row
                        print(f"\n📝 Adding updated enriched row...")
                        add_success = sheets_manager.process_property_data_to_tab(updated_row_data, 'AUCTIONS_MASTER')
                        
                        if add_success:
                            print(f"✅ Successfully added updated enriched row")
                            print(f"🎉 Now you can manually delete the old enriched row (Row {enriched_row_index + 1}) and the duplicate imported row (Row 2)")
                        else:
                            print(f"❌ Failed to add updated enriched row")
                    else:
                        print(f"✅ Enriched row already has correct data")
                        print(f"🎉 Now you can manually delete the duplicate imported row (Row 2)")
                else:
                    print(f"❌ Could not find enriched row for {target_address}, Lot 50")
                
            else:
                print(f"❌ Could not fetch from Google Sheet")
        else:
            print(f"❌ HTTP error fetching from Google Sheet: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error updating enriched row: {e}")

if __name__ == "__main__":
    update_enriched_row() 