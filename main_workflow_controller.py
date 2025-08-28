#!/usr/bin/env python3
"""
Main Workflow Controller for Auction Processing System

This script orchestrates the entire auction processing workflow:
1. EIG Auction Scraping
2. Date-based categorization (0-3 months vs 3-12 months)
3. Conditional routing to appropriate workflows
4. POTENTIAL_TRADES management
5. PropertyEngine enrichment
"""

import os
import sys
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import eig
from run_listing_enrichment_workflow import ListingEnrichmentWorkflow
from sheets_webapp import PropertyDataManagerWebApp

class MainWorkflowController:
    def __init__(self):
        """Initialize the main workflow controller"""
        self.enrichment_workflow = ListingEnrichmentWorkflow()
        self.sheets_manager = PropertyDataManagerWebApp()
        
        # Configuration
        self.older_auction_months = 3  # 3-12 months
        self.newer_auction_months = 3   # 0-3 months
        self.potential_trades_delay_months = 3  # Wait 3 months before processing
        
    def categorize_auction_by_date(self, auction_date_str):
        """
        Categorize auction as OLDER (3-12 months) or NEWER (0-3 months)
        
        Args:
            auction_date_str (str): Auction date in format 'YYYY-MM-DD'
            
        Returns:
            str: 'OLDER' or 'NEWER'
        """
        try:
            auction_date = datetime.strptime(auction_date_str, '%Y-%m-%d')
            current_date = datetime.now()
            
            # Calculate months difference
            date_diff = relativedelta(current_date, auction_date)
            months_diff = date_diff.years * 12 + date_diff.months
            
            print(f"   📅 Auction date: {auction_date_str}")
            print(f"   📅 Current date: {current_date.strftime('%Y-%m-%d')}")
            print(f"   📊 Months difference: {months_diff}")
            
            if months_diff >= self.older_auction_months and months_diff <= 12:
                print(f"   ✅ Categorized as OLDER AUCTION (3-12 months)")
                return 'OLDER'
            elif months_diff >= 0 and months_diff < self.newer_auction_months:
                print(f"   ✅ Categorized as NEWER AUCTION (0-3 months)")
                return 'NEWER'
            else:
                print(f"   ⚠️ Auction outside processing range ({months_diff} months)")
                return 'SKIP'
                
        except Exception as e:
            print(f"   ❌ Error categorizing auction date: {e}")
            return 'SKIP'
    
    def check_purchase_price_criteria(self, property_data):
        """
        Check if property meets purchase price criteria
        
        Args:
            property_data (dict): Property data from EIG scraper
            
        Returns:
            bool: True if meets criteria (has purchase_price and < 6 months)
        """
        purchase_price = property_data.get('purchase_price', '')
        sold_date = property_data.get('sold_date', '')
        
        # Check if purchase price exists (handle both string and int types)
        if isinstance(purchase_price, int):
            has_purchase_price = purchase_price > 0
        else:
            has_purchase_price = purchase_price and str(purchase_price).strip() and str(purchase_price) != 'Not found'
        
        if not has_purchase_price:
            print(f"   ❌ No purchase price found")
            return False
        
        # Check if sold date is within 6 months
        if sold_date:
            try:
                # Handle ISO format dates with timezone
                if 'T' in sold_date:
                    # Remove timezone part and parse
                    sold_date_clean = sold_date.split('T')[0]
                else:
                    sold_date_clean = sold_date
                
                sold_date_obj = datetime.strptime(sold_date_clean, '%Y-%m-%d')
                current_date = datetime.now()
                
                date_diff = relativedelta(current_date, sold_date_obj)
                months_diff = date_diff.years * 12 + date_diff.months
                
                print(f"   📅 Sold date: {sold_date}")
                print(f"   📊 Months since sold: {months_diff}")
                
                if months_diff < 6:
                    print(f"   ✅ Purchase price criteria met (< 6 months)")
                    return True
                else:
                    print(f"   ❌ Sold date too old (≥ 6 months)")
                    return False
                    
            except Exception as e:
                print(f"   ⚠️ Error parsing sold date: {e}")
                return False
        else:
            print(f"   ❌ No sold date found")
            return False
    
    def process_older_auction(self, property_data):
        """
        Process OLDER auction (3-12 months)
        
        Args:
            property_data (dict): Property data from EIG scraper
            
        Returns:
            bool: True if successfully processed
        """
        print(f"\n🔄 Processing OLDER AUCTION: {property_data.get('address', 'Unknown')}")
        
        # Check purchase price criteria
        meets_criteria = self.check_purchase_price_criteria(property_data)
        
        if meets_criteria:
            print(f"   ✅ Purchase price criteria met - proceeding to enrichment")
            
            # Run PropertyEngine enrichment
            try:
                result = self.enrichment_workflow.extract_from_propertyengine(
                    property_data.get('auction_url', ''),
                    property_data.get('auction_name'),
                    property_data.get('auction_date')
                )
                
                if result:
                    # Update property data with enrichment results
                    property_data['source_url'] = result.get('source_url', property_data.get('auction_url', ''))
                    property_data['guide_price'] = result.get('guide_price', property_data.get('guide_price', ''))
                    property_data['qa_status'] = 'enriched'
                    
                    print(f"   ✅ Enrichment completed successfully")
                else:
                    print(f"   ⚠️ Enrichment failed, using original data")
                    property_data['qa_status'] = 'enrichment_failed'
                
                # Import to AUCTION_MASTER
                success = self.sheets_manager.add_property(property_data)
                if success:
                    print(f"   ✅ Successfully imported to AUCTION_MASTER")
                    return True
                else:
                    print(f"   ❌ Failed to import to AUCTION_MASTER")
                    return False
                    
            except Exception as e:
                print(f"   ❌ Error during enrichment: {e}")
                return False
        else:
            print(f"   ⏭️ Purchase price criteria not met - skipping")
            return False
    
    def process_newer_auction(self, property_data):
        """
        Process NEWER auction (0-3 months)
        
        Args:
            property_data (dict): Property data from EIG scraper
            
        Returns:
            bool: True if successfully processed
        """
        print(f"\n🔄 Processing NEWER AUCTION: {property_data.get('address', 'Unknown')}")
        
        # Check purchase price criteria
        meets_criteria = self.check_purchase_price_criteria(property_data)
        
        if meets_criteria:
            print(f"   ✅ Purchase price criteria met - direct import to AUCTION_MASTER")
            
            # Direct import to AUCTION_MASTER
            property_data['qa_status'] = 'direct_import'
            success = self.sheets_manager.add_property(property_data)
            
            if success:
                print(f"   ✅ Successfully imported to AUCTION_MASTER")
                return True
            else:
                print(f"   ❌ Failed to import to AUCTION_MASTER")
                return False
        else:
            print(f"   ⏭️ Purchase price criteria not met - storing in POTENTIAL_TRADES")
            
            # Store in POTENTIAL_TRADES
            property_data['qa_status'] = 'pending_enrichment'
            property_data['added_to_potential_trades'] = datetime.now().isoformat()
            
            success = self.add_to_potential_trades(property_data)
            
            if success:
                print(f"   ✅ Successfully stored in POTENTIAL_TRADES")
                return True
            else:
                print(f"   ❌ Failed to store in POTENTIAL_TRADES")
                return False
    
    def add_to_potential_trades(self, property_data):
        """
        Add property to POTENTIAL_TRADES tab
        
        Args:
            property_data (dict): Property data
            
        Returns:
            bool: True if successfully added
        """
        try:
            # Prepare payload for POTENTIAL_TRADES
            payload = {
                'token': self.sheets_manager.shared_token,
                'action': 'add',
                'sheet_name': 'POTENTIAL_TRADES',  # Specify the tab name
                'rows': [{
                    'auction_name': property_data.get('auction_name', ''),
                    'auction_date': property_data.get('auction_date', ''),
                    'address': property_data.get('address', ''),
                    'auction_sale': property_data.get('auction_sale', ''),
                    'lot_number': property_data.get('lot_number', ''),
                    'postcode': property_data.get('postcode', ''),
                    'purchase_price': property_data.get('purchase_price', ''),
                    'sold_date': property_data.get('sold_date', ''),
                    'auction_url': property_data.get('auction_url', ''),
                    'source_url': property_data.get('source_url', ''),
                    'guide_price': property_data.get('guide_price', ''),

                    'qa_status': property_data.get('qa_status', 'pending_enrichment'),
                    'added_to_potential_trades': property_data.get('added_to_potential_trades', ''),
                    'ingested_at': property_data.get('added_timestamp', datetime.now().isoformat())
                }]
            }
            
            # Send request to Google Apps Script
            import requests
            response = requests.post(self.sheets_manager.webapp_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    print(f"   ✅ Added to POTENTIAL_TRADES successfully")
                    return True
                else:
                    print(f"   ❌ Failed to add to POTENTIAL_TRADES: {result}")
                    return False
            else:
                print(f"   ❌ HTTP error adding to POTENTIAL_TRADES: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error adding to POTENTIAL_TRADES: {e}")
            return False
    
    def process_potential_trades(self):
        """
        Process POTENTIAL_TRADES entries with PropertyEngine enrichment.
        """
        try:
            print(f"🔄 Processing POTENTIAL_TRADES entries...")
            
            # Read POTENTIAL_TRADES data
            payload = {
                'token': self.sheets_manager.shared_token,
                'action': 'read',
                'sheet_name': 'POTENTIAL_TRADES'
            }
            
            import requests
            response = requests.post(self.sheets_manager.webapp_url, json=payload, timeout=30)
            
            if response.status_code != 200:
                print(f"❌ Failed to read POTENTIAL_TRADES: {response.status_code}")
                return 0
            
            result = response.json()
            if not result.get('ok'):
                print(f"❌ Failed to read POTENTIAL_TRADES: {result}")
                return 0
            
            potential_trades = result.get('rows', [])
            print(f"✅ Found {len(potential_trades)} entries in POTENTIAL_TRADES")
            
            if not potential_trades:
                print("📋 No POTENTIAL_TRADES entries to process")
                return 0
            
            # Process each entry with PropertyEngine enrichment
            processed_count = 0
            for i, entry in enumerate(potential_trades):
                print(f"\n🔍 Processing POTENTIAL_TRADES entry {i+1}/{len(potential_trades)}")
                print(f"   Address: {entry.get('address', 'No address')}")
                
                # Check if already has source_url
                if entry.get('source_url') and entry.get('source_url').strip():
                    print(f"   ⏭️ Already has source_url, skipping")
                    continue
                
                # Run PropertyEngine enrichment
                try:
                    enriched_data = self.enrich_with_propertyengine(entry)
                    if enriched_data:
                        # Update the entry in POTENTIAL_TRADES
                        update_result = self.update_potential_trades_entry(entry, enriched_data)
                        if update_result:
                            processed_count += 1
                            print(f"   ✅ Successfully enriched and updated")
                        else:
                            print(f"   ❌ Failed to update entry")
                    else:
                        print(f"   ⏭️ No enrichment data found")
                        
                except Exception as e:
                    print(f"   ❌ Error enriching entry: {e}")
                    continue
            
            print(f"\n📊 POTENTIAL_TRADES processing completed: {processed_count} entries enriched")
            return processed_count
            
        except Exception as e:
            print(f"❌ Error processing POTENTIAL_TRADES: {e}")
            return 0
    
    def enrich_with_propertyengine(self, entry):
        """
        Enrich a POTENTIAL_TRADES entry with PropertyEngine data.
        """
        try:
            address = entry.get('address', '')
            if not address:
                return None
            
            print(f"      🔍 Running PropertyEngine enrichment for: {address}")
            
            # Import and run the PropertyEngine enrichment
            from run_listing_enrichment_workflow import ListingEnrichmentWorkflow
            
            # Create enrichment workflow instance
            enrichment_workflow = ListingEnrichmentWorkflow()
            
            # Start browser
            enrichment_workflow.start_browser()
            
            try:
                # Create row data structure that the enrichment expects
                row_data = {
                    'address': address,
                    'auction_name': entry.get('auction_name', ''),
                    'auction_date': entry.get('auction_date', ''),
                    'guide_price': entry.get('guide_price', ''),
                    'source_url': entry.get('source_url', '')
                }
                
                # Create row info structure
                row_info = {
                    'row_data': row_data,
                    'missing_guide_price': not entry.get('guide_price'),
                    'missing_source_url': not entry.get('source_url')
                }
                
                # Process the row using the enrichment workflow
                success = enrichment_workflow.process_missing_row(row_info)
                
                if success:
                    # Get the updated data from the enrichment
                    # The enrichment workflow updates the spreadsheet directly
                    # So we need to read the updated data back
                    updated_data = self.get_updated_entry_data(entry)
                    if updated_data:
                        print(f"      ✅ Successfully enriched with PropertyEngine")
                        return updated_data
                    else:
                        print(f"      ⏭️ Enrichment succeeded but couldn't read updated data")
                        return None
                else:
                    print(f"      ⏭️ PropertyEngine enrichment failed")
                    return None
                    
            finally:
                # Always close the browser
                enrichment_workflow.close_browser()
                
        except Exception as e:
            print(f"      ❌ Error in PropertyEngine enrichment: {e}")
            return None
    
    def get_updated_entry_data(self, original_entry):
        """
        Get the updated entry data after PropertyEngine enrichment.
        """
        try:
            # Read the POTENTIAL_TRADES data again to get the updated entry
            payload = {
                'token': self.sheets_manager.shared_token,
                'action': 'read',
                'sheet_name': 'POTENTIAL_TRADES'
            }
            
            import requests
            response = requests.post(self.sheets_manager.webapp_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    potential_trades = result.get('rows', [])
                    
                    # Find the matching entry
                    for entry in potential_trades:
                        if (entry.get('address') == original_entry.get('address') and 
                            entry.get('auction_name') == original_entry.get('auction_name') and
                            entry.get('auction_date') == original_entry.get('auction_date')):
                            
                            # Check if source_url was updated
                            if entry.get('source_url') and entry.get('source_url') != original_entry.get('source_url'):
                                return {
                                    'source_url': entry.get('source_url'),
                                    'guide_price': entry.get('guide_price', original_entry.get('guide_price'))
                                }
                    
                    print(f"      ⚠️ Couldn't find updated entry data")
                    return None
                else:
                    print(f"      ❌ Failed to read updated data: {result}")
                    return None
            else:
                print(f"      ❌ HTTP error reading updated data: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"      ❌ Error getting updated entry data: {e}")
            return None
    
    def update_potential_trades_entry(self, original_entry, enriched_data):
        """
        Update a POTENTIAL_TRADES entry with enriched data.
        """
        try:
            # Prepare update data
            update_data = {
                'auction_name': original_entry.get('auction_name', ''),
                'auction_date': original_entry.get('auction_date', ''),
                'address': original_entry.get('address', ''),
                'auction_sale': original_entry.get('auction_sale', ''),
                'guide_price': original_entry.get('guide_price', ''),
                'lot_number': original_entry.get('lot_number', ''),
                'postcode': original_entry.get('postcode', ''),
                'purchase_price': original_entry.get('purchase_price', ''),
                'sold_date': original_entry.get('sold_date', ''),
                'auction_url': original_entry.get('auction_url', ''),
                'source_url': enriched_data.get('source_url', original_entry.get('source_url', '')),
                'added_to_potential_trades': original_entry.get('added_to_potential_trades', ''),
                'qa_status': 'enriched'
            }
            
            # Update the entry
            payload = {
                'token': self.sheets_manager.shared_token,
                'action': 'update_row',
                'sheet_name': 'POTENTIAL_TRADES',
                'row_data': update_data
            }
            
            import requests
            response = requests.post(self.sheets_manager.webapp_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    return True
                else:
                    print(f"      ❌ Update failed: {result.get('error', 'Unknown error')}")
                    return False
            else:
                print(f"      ❌ HTTP error {response.status_code}")
                return False
                
        except Exception as e:
            print(f"      ❌ Error updating entry: {e}")
            return False
    
    def run_full_workflow(self):
        """
        Run the complete workflow:
        1. Scrape ALL auctions from the last 12 months and import immediately after each auction
        2. Process POTENTIAL_TRADES for enrichment
        """
        print("🚀 Starting Main Workflow Controller")
        print("=" * 50)
        
        try:
            # Calculate date range for ALL auctions (last 12 months)
            current_date = datetime.now()
            all_auctions_start_date = (current_date - relativedelta(months=12)).strftime('%Y-%m-%d')
            all_auctions_end_date = current_date.strftime('%Y-%m-%d')
            
            print(f"📅 Scraping ALL auctions from the last 12 months:")
            print(f"   Date range: {all_auctions_start_date} to {all_auctions_end_date}")
            print(f"   Current date: {current_date.strftime('%Y-%m-%d')}")
            
            # Step 1: Scrape ALL auctions and import immediately after each auction
            print(f"\n📊 Step 1: Scraping and importing auctions from the last 12 months...")
            try:
                import eig
                all_lots = eig.scrape_auctions_without_import(all_auctions_start_date, all_auctions_end_date)
                print(f"✅ ALL auctions scraping and importing completed: {len(all_lots)} lots processed")
            except Exception as e:
                print(f"❌ Error scraping and importing auctions: {e}")
                all_lots = []
            
            # Step 2: Process POTENTIAL_TRADES for enrichment
            print(f"\n🔄 Step 2: Processing POTENTIAL_TRADES for enrichment...")
            potential_processed = self.process_potential_trades()
            print(f"   POTENTIAL_TRADES entries processed: {potential_processed}")
            
            # Summary
            print(f"\n📊 Final Summary:")
            print(f"   Total lots scraped and imported: {len(all_lots)}")
            print(f"   POTENTIAL_TRADES processed: {potential_processed}")
            
            print("\n✅ Main workflow completed successfully!")
            
        except Exception as e:
            print(f"❌ Error in main workflow: {e}")
            import traceback
            traceback.print_exc()

    def process_newer_lot(self, lot):
        """
        Process a NEWER lot (0-3 months old).
        Everything goes to POTENTIAL_TRADES unless it has purchase_price, then AUCTION_MASTER.
        PropertyEngine enrichment will happen later in post-import processing.
        """
        try:
            print(f"   🔍 Processing NEWER lot: {lot.get('address', 'No address')}")
            
            # Skip land/garage/part of lots
            address = lot.get('address', '').lower()
            if any(keyword in address for keyword in ['land', 'garage', 'plot', 'parking space', 'car park', 'part of']):
                print(f"   ⏭️ Skipping - land/garage/part of lot: {lot.get('address', 'No address')}")
                return False
            
            # Check if lot has purchase_price
            has_purchase_price = lot.get('purchase_price') and lot.get('purchase_price') != 'Not found'
            
            if has_purchase_price:
                print(f"   ✅ Direct import to AUCTION_MASTER - has purchase price")
                return self.import_lot_to_auction_master(lot)
            else:
                print(f"   📋 Adding to POTENTIAL_TRADES - no purchase price")
                return self.import_lot_to_potential_trades(lot)
                
        except Exception as e:
            print(f"   ❌ Error processing NEWER lot: {e}")
            return False
    
    def process_older_lot(self, lot):
        """
        Process an OLDER lot (3-12 months old).
        Only import to AUCTION_MASTER if it has purchase_price, otherwise skip.
        PropertyEngine enrichment will happen later in post-import processing.
        """
        try:
            print(f"   🔍 Processing OLDER lot: {lot.get('address', 'No address')}")
            
            # Skip land/garage/part of lots
            address = lot.get('address', '').lower()
            if any(keyword in address for keyword in ['land', 'garage', 'plot', 'parking space', 'car park', 'part of']):
                print(f"   ⏭️ Skipping - land/garage/part of lot: {lot.get('address', 'No address')}")
                return False
            
            # Check if lot has purchase_price
            has_purchase_price = lot.get('purchase_price') and lot.get('purchase_price') != 'Not found'
            
            if has_purchase_price:
                print(f"   ✅ Direct import to AUCTION_MASTER - has purchase price")
                return self.import_lot_to_auction_master(lot)
            else:
                print(f"   ⏭️ Skipping - no purchase price")
                return False
                
        except Exception as e:
            print(f"   ❌ Error processing OLDER lot: {e}")
            return False
    
    def check_purchase_price_criteria_for_lot(self, lot):
        """
        Check if a lot meets the purchase price criteria (sold within 6 months).
        """
        purchase_price = lot.get('purchase_price', '')
        sold_date = lot.get('sale_date', '')
        
        if isinstance(purchase_price, int):
            has_purchase_price = purchase_price > 0
        else:
            has_purchase_price = purchase_price and str(purchase_price).strip() and str(purchase_price) != 'Not found'
        
        if not has_purchase_price:
            print(f"      ❌ No purchase price found")
            return False
        
        if sold_date:
            try:
                if 'T' in sold_date:
                    sold_date_clean = sold_date.split('T')[0]
                else:
                    sold_date_clean = sold_date
                
                sold_date_obj = datetime.strptime(sold_date_clean, '%Y-%m-%d')
                current_date = datetime.now()
                
                date_diff = relativedelta(current_date, sold_date_obj)
                months_diff = date_diff.years * 12 + date_diff.months
                
                print(f"      📅 Sold date: {sold_date}")
                print(f"      📊 Months since sold: {months_diff}")
                
                if months_diff < 6:
                    print(f"      ✅ Purchase price criteria met (< 6 months)")
                    return True
                else:
                    print(f"      ❌ Sold date too old (≥ 6 months)")
                    return False
                    
            except Exception as e:
                print(f"      ⚠️ Error parsing sold date: {e}")
                return False
        else:
            print(f"      ❌ No sold date found")
            return False
    
    def import_lot_to_auction_master(self, lot):
        """
        Import a lot directly to AUCTION_MASTER.
        """
        try:
            property_data = {
                'auction_name': lot.get('auction_name', ''),
                'auction_date': lot.get('auction_date', ''),
                'address': lot.get('address', ''),
                'auction_sale': lot.get('auction_sale', ''),
                'guide_price': lot.get('guide_price', ''),
                'lot_number': lot.get('lot_number', ''),
                'postcode': lot.get('postcode', ''),
                'purchase_price': lot.get('purchase_price', ''),
                'sold_date': lot.get('sale_date', ''),
                'auction_url': lot.get('lot_url', ''),
                'source_url': lot.get('source_url', ''),
                'qa_status': 'imported'
            }
            
            # Ensure all required fields have at least empty string values
            for field in ['auction_name', 'auction_date', 'address', 'auction_sale', 'lot_number', 'postcode', 'purchase_price', 'sold_date', 'auction_url']:
                if field not in property_data or property_data[field] is None:
                    property_data[field] = ''
            
            result = self.sheets_manager.process_property_data(property_data)
            if result.get('status') == 'success':
                print(f"      ✅ Successfully imported to AUCTION_MASTER")
                return True
            else:
                print(f"      ❌ Failed to import to AUCTION_MASTER: {result.get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"      ❌ Error importing to AUCTION_MASTER: {e}")
            return False
    
    def import_lot_to_potential_trades(self, lot):
        """
        Import a lot to POTENTIAL_TRADES.
        """
        try:
            property_data = {
                'auction_name': lot.get('auction_name', ''),
                'auction_date': lot.get('auction_date', ''),
                'address': lot.get('address', ''),
                'auction_sale': lot.get('auction_sale', ''),
                'guide_price': lot.get('guide_price', ''),
                'lot_number': lot.get('lot_number', ''),
                'postcode': lot.get('postcode', ''),
                'purchase_price': lot.get('purchase_price', ''),
                'sold_date': lot.get('sale_date', ''),
                'auction_url': lot.get('lot_url', ''),
                'source_url': lot.get('source_url', ''),
                'added_to_potential_trades': 'yes',
                'qa_status': 'pending'
            }
            
            # Ensure all required fields have at least empty string values
            for field in ['auction_name', 'auction_date', 'address', 'auction_sale', 'lot_number', 'postcode', 'purchase_price', 'sold_date', 'auction_url']:
                if field not in property_data or property_data[field] is None:
                    property_data[field] = ''
            
            # Import to POTENTIAL_TRADES tab
            result = self.sheets_manager.process_property_data_to_tab(property_data, 'POTENTIAL_TRADES')
            if result.get('status') == 'success':
                print(f"      ✅ Successfully imported to POTENTIAL_TRADES")
                return True
            else:
                print(f"      ❌ Failed to import to POTENTIAL_TRADES: {result.get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"      ❌ Error importing to POTENTIAL_TRADES: {e}")
            return False

def main():
    """Main entry point"""
    controller = MainWorkflowController()
    controller.run_full_workflow()

if __name__ == "__main__":
    main() 