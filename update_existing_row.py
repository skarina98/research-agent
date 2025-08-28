#!/usr/bin/env python3
"""
Update the existing imported row with guide price and PropertyEngine URL
"""

import os
import sys
import requests
from sheets_webapp import PropertyDataManagerWebApp

def update_existing_row():
    """Update the existing imported row with enrichment data"""
    sheets_manager = PropertyDataManagerWebApp()
    
    print("🔄 Updating existing imported row with enrichment data")
    print("=" * 60)
    
    # The correct PropertyEngine URL and guide price we found
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
                
                # Find the imported row for 26 Cromwell Terrace, Lot 50
                target_address = "26 Cromwell Terrace, Chatham, ME4 5PQ"
                imported_row = None
                imported_row_index = None
                
                for i, row in enumerate(rows):
                    address = row.get('address', '')
                    qa_status = row.get('qa_status', '')
                    lot_number = row.get('lot_number', '')
                    auction_sale = row.get('auction_sale', '')
                    
                    # Look for the imported row with the target address and "Sold for" auction sale (Lot 50)
                    if (target_address.lower() in address.lower() and 
                        qa_status == 'imported' and 
                        'Sold for' in auction_sale):
                        imported_row = row
                        imported_row_index = i
                        print(f"📋 Found imported row at index {i+1}: {address}")
                        print(f"   Lot Number: {lot_number}")
                        print(f"   Auction Sale: {auction_sale}")
                        break
                
                if imported_row:
                    print(f"\n📋 Current imported row data:")
                    print(f"   Address: {imported_row.get('address', 'N/A')}")
                    print(f"   Guide Price: {imported_row.get('guide_price', 'N/A')}")
                    print(f"   Source URL: {imported_row.get('source_url', 'N/A')}")
                    print(f"   QA Status: {imported_row.get('qa_status', 'N/A')}")
                    
                    # Create updated row data with enrichment
                    updated_row_data = {
                        'auction_name': imported_row.get('auction_name', ''),
                        'auction_date': imported_row.get('auction_date', ''),
                        'address': imported_row.get('address', ''),
                        'auction_sale': imported_row.get('auction_sale', ''),
                        'lot_number': imported_row.get('lot_number', ''),
                        'postcode': imported_row.get('postcode', ''),
                        'purchase_price': imported_row.get('purchase_price', ''),
                        'sold_date': imported_row.get('sold_date', ''),
                        'auction_url': imported_row.get('auction_url', ''),
                        'source_url': correct_propertyengine_url,
                        'guide_price': correct_guide_price,
                        'qa_status': 'enriched'
                    }
                    
                    print(f"\n🔄 Updating row with enrichment data:")
                    print(f"   Guide Price: {correct_guide_price}")
                    print(f"   Source URL: {correct_propertyengine_url}")
                    print(f"   QA Status: enriched")
                    
                    # Try to update the existing row first
                    print(f"\n📝 Attempting to update existing row...")
                    
                    update_payload = {
                        'token': shared_token,
                        'action': 'update_row',
                        'sheet_id': os.getenv('GOOGLE_SHEETS_ID', '1ONZrugWl0amSFqGLq3_hHmR82Bps-vNxr-25gGk8B9Q'),
                        'row_index': imported_row_index,
                        'row_data': updated_row_data
                    }
                    
                    update_response = requests.post(webapp_url, json=update_payload, timeout=30)
                    
                    if update_response.status_code == 200:
                        update_result = update_response.json()
                        if update_result.get('ok'):
                            print(f"✅ Successfully updated existing row!")
                            print(f"🎉 Row {imported_row_index + 1} now has guide price and PropertyEngine URL")
                            return True
                        else:
                            print(f"❌ Failed to update row: {update_result.get('error', 'Unknown error')}")
                            print(f"📄 Full response: {update_result}")
                    else:
                        print(f"❌ HTTP error updating row: {update_response.status_code}")
                        print(f"📄 Response: {update_response.text}")
                    
                    # If update failed, try adding a new row as fallback
                    print(f"\n📝 Fallback: Adding new enriched row...")
                    add_success = sheets_manager.process_property_data_to_tab(updated_row_data, 'AUCTIONS_MASTER')
                    
                    if add_success:
                        print(f"✅ Successfully added new enriched row")
                        print(f"🎉 Now you can manually delete the old imported row (Row {imported_row_index + 1})")
                        return True
                    else:
                        print(f"❌ Failed to add new enriched row")
                        return False
                else:
                    print(f"❌ Could not find imported row for {target_address}, Lot 50")
                    return False
                
            else:
                print(f"❌ Could not fetch from Google Sheet")
                return False
        else:
            print(f"❌ HTTP error fetching from Google Sheet: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating existing row: {e}")
        return False

if __name__ == "__main__":
    success = update_existing_row()
    if success:
        print("\n🎉 Row update completed successfully!")
    else:
        print("\n💥 Row update failed!") 