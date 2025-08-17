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
                    'owner': property_data.get('owner', ''),
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
        Process entries in POTENTIAL_TRADES that are 3+ months old
        
        Returns:
            int: Number of entries processed
        """
        print(f"\n🔄 Processing POTENTIAL_TRADES entries...")
        
        try:
            # Read POTENTIAL_TRADES data
            payload = {
                'token': self.sheets_manager.shared_token,
                'action': 'read',
                'sheet_name': 'POTENTIAL_TRADES'
            }
            
            import requests
            response = requests.post(self.sheets_manager.webapp_url, json=payload, timeout=30)
            
            if response.status_code != 200:
                print(f"   ❌ Failed to read POTENTIAL_TRADES: {response.status_code}")
                return 0
            
            result = response.json()
            if not result.get('ok'):
                print(f"   ❌ Failed to read POTENTIAL_TRADES: {result}")
                return 0
            
            entries = result.get('rows', [])
            print(f"   📊 Found {len(entries)} entries in POTENTIAL_TRADES")
            
            processed_count = 0
            current_date = datetime.now()
            
            for entry in entries:
                added_date_str = entry.get('added_to_potential_trades', '')
                if not added_date_str:
                    continue
                
                try:
                    added_date = datetime.fromisoformat(added_date_str.replace('Z', '+00:00'))
                    date_diff = relativedelta(current_date, added_date)
                    months_diff = date_diff.years * 12 + date_diff.months
                    
                    if months_diff >= self.potential_trades_delay_months:
                        print(f"   🔍 Processing entry: {entry.get('address', 'Unknown')} ({months_diff} months old)")
                        
                        # Run PropertyEngine enrichment
                        result = self.enrichment_workflow.extract_from_propertyengine(
                            entry.get('auction_url', ''),
                            entry.get('auction_name'),
                            entry.get('auction_date')
                        )
                        
                        if result:
                            # Update entry with enrichment results
                            entry['source_url'] = result.get('source_url', entry.get('auction_url', ''))
                            entry['guide_price'] = result.get('guide_price', entry.get('guide_price', ''))
                            entry['qa_status'] = 'enriched'
                            
                            # Check purchase price criteria again
                            meets_criteria = self.check_purchase_price_criteria(entry)
                            
                            if meets_criteria:
                                # Move to AUCTION_MASTER
                                success = self.sheets_manager.add_property(entry)
                                if success:
                                    print(f"   ✅ Moved to AUCTION_MASTER")
                                    # TODO: Remove from POTENTIAL_TRADES
                                    processed_count += 1
                                else:
                                    print(f"   ❌ Failed to move to AUCTION_MASTER")
                            else:
                                print(f"   ❌ Still doesn't meet criteria - DELETE")
                                # TODO: Remove from POTENTIAL_TRADES (DELETE)
                        else:
                            print(f"   ❌ Enrichment failed")
                            # TODO: Remove from POTENTIAL_TRADES (DELETE)
                    
                except Exception as e:
                    print(f"   ❌ Error processing entry: {e}")
                    continue
            
            print(f"   ✅ Processed {processed_count} entries from POTENTIAL_TRADES")
            return processed_count
            
        except Exception as e:
            print(f"   ❌ Error processing POTENTIAL_TRADES: {e}")
            return 0
    
    def run_full_workflow(self):
        """
        Run the complete workflow:
        1. Run EIG scraping for different date ranges (0-3 months, 3-12 months)
        2. Process the scraped data with date-based categorization
        3. Route to appropriate processing (AUCTION_MASTER vs POTENTIAL_TRADES)
        4. Process POTENTIAL_TRADES
        """
        print("🚀 Starting Main Workflow Controller")
        print("=" * 50)
        
        try:
            # Calculate date ranges for scraping
            current_date = datetime.now()
            
            # NEWER auctions: 0-3 months ago
            newer_start_date = (current_date - relativedelta(months=3)).strftime('%Y-%m-%d')
            newer_end_date = current_date.strftime('%Y-%m-%d')
            
            # OLDER auctions: 3-12 months ago
            older_start_date = (current_date - relativedelta(months=12)).strftime('%Y-%m-%d')
            older_end_date = (current_date - relativedelta(months=3)).strftime('%Y-%m-%d')
            
            print(f"📅 Date Ranges for Scraping:")
            print(f"   NEWER (0-3 months): {newer_start_date} to {newer_end_date}")
            print(f"   OLDER (3-12 months): {older_start_date} to {older_end_date}")
            
            # Step 1: Scrape NEWER auctions (0-3 months)
            print(f"\n📊 Step 1: Scraping NEWER auctions (0-3 months)...")
            try:
                import eig
                newer_result = eig.process_auctions_to_sheets(newer_start_date, newer_end_date)
                print(f"✅ NEWER auctions scraping completed: {newer_result}")
            except Exception as e:
                print(f"❌ Error scraping NEWER auctions: {e}")
                newer_result = {"status": "error", "total_imported": 0}
            
            # Step 2: Scrape OLDER auctions (3-12 months)
            print(f"\n📊 Step 2: Scraping OLDER auctions (3-12 months)...")
            try:
                older_result = eig.process_auctions_to_sheets(older_start_date, older_end_date)
                print(f"✅ OLDER auctions scraping completed: {older_result}")
            except Exception as e:
                print(f"❌ Error scraping OLDER auctions: {e}")
                older_result = {"status": "error", "total_imported": 0}
            
            # Step 3: Process POTENTIAL_TRADES
            print(f"\n🔄 Step 3: Processing POTENTIAL_TRADES...")
            potential_processed = self.process_potential_trades()
            print(f"   POTENTIAL_TRADES entries processed: {potential_processed}")
            
            # Summary
            print(f"\n📊 Final Summary:")
            print(f"   NEWER auctions imported: {newer_result.get('total_imported', 0)}")
            print(f"   OLDER auctions imported: {older_result.get('total_imported', 0)}")
            print(f"   POTENTIAL_TRADES processed: {potential_processed}")
            
            print("\n✅ Main workflow completed successfully!")
            
        except Exception as e:
            print(f"❌ Error in main workflow: {e}")
            import traceback
            traceback.print_exc()

def main():
    """Main entry point"""
    controller = MainWorkflowController()
    controller.run_full_workflow()

if __name__ == "__main__":
    main() 