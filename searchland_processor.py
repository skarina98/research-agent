#!/usr/bin/env python3
"""
Complete Searchland processor for Google Sheets integration
Reads data from Google Sheet, processes with Searchland, and updates the sheet
"""

import asyncio
import os
import json
import time
import random
import requests
from datetime import datetime
from playwright.async_api import async_playwright

BASE_URL = "https://app.searchland.co.uk"

class SearchlandSheetProcessor:
    """Process Searchland data for properties in Google Sheet"""
    
    def __init__(self):
        """Initialize the Searchland processor"""
        self.webapp_url = "https://script.google.com/macros/s/AKfycbyp2RXahUVgZW9xMJyVYdCuyOcBoVqfpN_XeOQF91s8GjryvAakoCB2FdqVvlQ9Vtd2/exec"
        self.shared_token = os.getenv('GOOGLE_SHEETS_SHARED_TOKEN', '3c4ebe48f035fd3f68ccd5c9f619d7aa3f686d2d7637dc54324d979acc066feb')
        self.sheet_id = os.getenv('GOOGLE_SHEETS_ID', '1ONZrugWl0amSFqGLq3_hHmR82Bps-vNxr-25gGk8B9Q')
        self.processed_count = 0
        self.error_count = 0
        
    async def get_sheet_data(self):
        """Get data from Google Sheet"""
        try:
            print("📊 Reading data from Google Sheet...")
            
            # Request to read sheet data
            payload = {
                'token': self.shared_token,
                'action': 'read',
                'sheet_id': self.sheet_id
            }
            
            response = requests.post(self.webapp_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    rows = result.get('rows', [])
                    print(f"✅ Read {len(rows)} rows from Google Sheet")
                    return rows
                else:
                    print(f"❌ Error reading sheet: {result.get('message', 'Unknown error')}")
                    return []
            else:
                print(f"❌ HTTP error {response.status_code}: {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Error reading Google Sheet: {e}")
            return []
    
    async def update_sheet_row(self, row_data, row_index):
        """Update a specific row in Google Sheet with Searchland data"""
        try:
            print(f"📝 Updating row {row_index} in Google Sheet...")
            
            # Prepare the update payload
            update_payload = {
                'token': self.shared_token,
                'action': 'update_row',
                'sheet_id': self.sheet_id,
                'row_index': row_index,
                'data': {
                    'owner': row_data.get('owner_name', ''),
                    'guide_price': row_data.get('guide_price', ''),
                    'listing_link': row_data.get('listing_link', ''),
                    'searchland_status': 'processed',
                    'searchland_processed_at': datetime.now().isoformat()
                }
            }
            
            response = requests.post(self.webapp_url, json=update_payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    print(f"✅ Row {row_index} updated successfully")
                    return True
                else:
                    print(f"❌ Error updating row {row_index}: {result.get('message', 'Unknown error')}")
                    return False
            else:
                print(f"❌ HTTP error {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error updating row {row_index}: {e}")
            return False
    
    async def search_property_in_searchland(self, address, postcode):
        """
        Search for a property in Searchland and extract data
        
        Args:
            address: Property address
            postcode: Property postcode
            
        Returns:
            Dict with extracted data
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            # Check if session file exists
            session_file = "sessions/searchland.json"
            if os.path.exists(session_file):
                print(f"    🔐 Using existing Searchland session")
                context = await browser.new_context(storage_state=session_file)
            else:
                print(f"    ⚠️ No Searchland session found, creating new context")
                context = await browser.new_context()
            
            page = await context.new_page()
            
            try:
                print(f"    🌐 Navigating to Searchland...")
                await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)
                
                # Wait a bit for page to fully load
                await page.wait_for_timeout(2000)
                
                # Check if we need to login
                page_title = await page.title()
                if "login" in page.url.lower() or "sign in" in page_title.lower():
                    print(f"    ⚠️ Redirected to login page - you may need to login manually")
                    await browser.close()
                    return None
                
                print(f"    🔍 Searching for: {address}, {postcode}")
                
                # Wait for the search bar to appear
                try:
                    await page.wait_for_selector("#navigation-bar-search", timeout=10000)
                except:
                    print(f"    ⚠️ Search bar not found after waiting")
                
                # Find and click the main search bar to open dropdown
                search_bar = await page.query_selector("#navigation-bar-search")
                if not search_bar:
                    print(f"    ❌ Could not find main search bar")
                    print(f"    🔍 Available inputs:")
                    inputs = await page.query_selector_all("input")
                    for i, inp in enumerate(inputs[:5]):
                        placeholder = await inp.get_attribute("placeholder")
                        input_type = await inp.get_attribute("type")
                        input_name = await inp.get_attribute("name")
                        print(f"       Input {i+1}: placeholder='{placeholder}', type='{input_type}', name='{input_name}'")
                    
                    print(f"    🔍 Available search elements:")
                    search_elements = await page.query_selector_all("[id*='search'], [class*='search'], [placeholder*='Search']")
                    for i, elem in enumerate(search_elements[:5]):
                        elem_id = await elem.get_attribute("id")
                        elem_class = await elem.get_attribute("class")
                        elem_placeholder = await elem.get_attribute("placeholder")
                        print(f"       Search Element {i+1}: id='{elem_id}', class='{elem_class}', placeholder='{elem_placeholder}'")
                    
                    await browser.close()
                    return None
                
                # Click on search bar to open dropdown
                await search_bar.click()
                await page.wait_for_timeout(1000)
                
                # Click on "Specific address" tab
                specific_address_tab = await page.query_selector("button:has-text('Specific address'), [data-testid='specific-address'], .specific-address-tab")
                if not specific_address_tab:
                    print(f"    ❌ Could not find 'Specific address' tab")
                    await browser.close()
                    return None
                
                await specific_address_tab.click()
                await page.wait_for_timeout(1000)
                
                # Find the address input field that appears after clicking "Specific address"
                # Wait a bit longer for the input to appear
                await page.wait_for_timeout(2000)
                
                address_input = await page.query_selector("input[placeholder='Search']")
                if not address_input:
                    print(f"    ❌ Could not find address input field")
                    print(f"    🔍 Available inputs after clicking 'Specific address':")
                    inputs = await page.query_selector_all("input")
                    for i, inp in enumerate(inputs[:10]):
                        placeholder = await inp.get_attribute("placeholder")
                        input_type = await inp.get_attribute("type")
                        input_id = await inp.get_attribute("id")
                        print(f"       Input {i+1}: placeholder='{placeholder}', type='{input_type}', id='{input_id}'")
                    await browser.close()
                    return None
                
                # Ensure the input field is visible and focused
                await address_input.scroll_into_view_if_needed()
                await address_input.click()
                await page.wait_for_timeout(500)
                
                # Clear and fill address input
                await address_input.fill("")
                await address_input.fill(f"{address}, {postcode}")
                await address_input.press("Enter")
                
                # Wait for results to load
                try:
                    await page.wait_for_selector(".property-result, .search-result, [class*='result'], .property-card", timeout=10000)
                except:
                    print(f"    ⚠️ No search results found")
                    await browser.close()
                    return None
                
                # Extract data from the property page
                data = await self.extract_property_data(page)
                
                await browser.close()
                return data
                
            except Exception as e:
                print(f"    ❌ Error searching property: {e}")
                await browser.close()
                return None
    
    async def extract_property_data(self, page):
        """
        Extract property data from Searchland page
        
        Args:
            page: Playwright page object
            
        Returns:
            Dict with extracted data
        """
        data = {
            'owner_name': '',
            'guide_price': '',
            'listing_link': '',
            'extraction_status': 'failed'
        }
        
        try:
            print(f"    📋 Extracting property data...")
            
            # Extract owner name from ownership tab
            owner_name = await self.extract_owner_name(page)
            if owner_name:
                data['owner_name'] = owner_name
                print(f"    👤 Owner: {owner_name}")
            
            # Extract guide price from residential sales tab
            guide_price = await self.extract_guide_price(page)
            if guide_price:
                data['guide_price'] = guide_price
                print(f"    💰 Guide Price: {guide_price}")
            
            # Extract listing link
            listing_link = await self.extract_listing_link(page)
            if listing_link:
                data['listing_link'] = listing_link
                print(f"    🔗 Listing Link: {listing_link}")
            
            if data['owner_name'] or data['guide_price'] or data['listing_link']:
                data['extraction_status'] = 'success'
                print(f"    ✅ Data extraction successful")
            else:
                print(f"    ⚠️ No data extracted")
            
            return data
            
        except Exception as e:
            print(f"    ❌ Error extracting data: {e}")
            return data
    
    async def extract_owner_name(self, page):
        """Extract owner name from ownership tab"""
        try:
            # Try to find and click ownership tab
            ownership_tab = await page.query_selector("text=Ownership, [data-tab='ownership'], .ownership-tab, button:has-text('Ownership')")
            if ownership_tab:
                await ownership_tab.click()
                await page.wait_for_timeout(2000)
            
            # Look for owner name in various selectors
            owner_selectors = [
                ".owner-name",
                ".current-owner",
                "[class*='owner']",
                ".property-owner",
                "text=Current Owner",
                "text=Owner",
                ".owner",
                "[data-testid='owner']"
            ]
            
            for selector in owner_selectors:
                try:
                    if selector.startswith("text="):
                        # Text-based selector
                        text_value = selector[5:]
                        elements = await page.query_selector_all(f"text={text_value}")
                        for element in elements:
                            # Get the next element or parent that might contain the owner name
                            parent = await element.query_selector("xpath=..")
                            if parent:
                                owner_text = await parent.text_content()
                                if owner_text and len(owner_text.strip()) > 3:
                                    return owner_text.strip()
                    else:
                        # CSS selector
                        owner_element = await page.query_selector(selector)
                        if owner_element:
                            owner_text = await owner_element.text_content()
                            if owner_text and len(owner_text.strip()) > 3:
                                return owner_text.strip()
                except:
                    continue
            
            return None
            
        except Exception as e:
            print(f"    ⚠️ Error extracting owner name: {e}")
            return None
    
    async def extract_guide_price(self, page):
        """Extract guide price from residential sales tab"""
        try:
            # Try to find and click residential sales tab
            sales_tab = await page.query_selector("text=Residential Sales, [data-tab='sales'], .sales-tab, button:has-text('Sales')")
            if sales_tab:
                await sales_tab.click()
                await page.wait_for_timeout(2000)
            
            # Look for guide price in various selectors
            price_selectors = [
                ".guide-price",
                ".asking-price",
                "[class*='price']",
                ".property-price",
                "text=Guide Price",
                "text=Asking Price",
                ".price",
                "[data-testid='price']"
            ]
            
            for selector in price_selectors:
                try:
                    if selector.startswith("text="):
                        # Text-based selector
                        text_value = selector[5:]
                        elements = await page.query_selector_all(f"text={text_value}")
                        for element in elements:
                            # Get the next element or parent that might contain the price
                            parent = await element.query_selector("xpath=..")
                            if parent:
                                price_text = await parent.text_content()
                                if price_text and "£" in price_text:
                                    return price_text.strip()
                    else:
                        # CSS selector
                        price_element = await page.query_selector(selector)
                        if price_element:
                            price_text = await price_element.text_content()
                            if price_text and "£" in price_text:
                                return price_text.strip()
                except:
                    continue
            
            return None
            
        except Exception as e:
            print(f"    ⚠️ Error extracting guide price: {e}")
            return None
    
    async def extract_listing_link(self, page):
        """Extract listing link"""
        try:
            # Look for listing link in various selectors
            link_selectors = [
                "a[href*='listing']",
                "a[href*='property']",
                "text=Go See Listing",
                "text=View Listing",
                ".listing-link",
                "[class*='listing']",
                "a:has-text('Go See Listing')",
                "a:has-text('View Listing')"
            ]
            
            for selector in link_selectors:
                try:
                    if selector.startswith("text="):
                        # Text-based selector
                        text_value = selector[5:]
                        elements = await page.query_selector_all(f"text={text_value}")
                        for element in elements:
                            # Get the href attribute
                            href = await element.get_attribute("href")
                            if href:
                                if href.startswith("/"):
                                    return f"https://searchland.co.uk{href}"
                                elif href.startswith("http"):
                                    return href
                    else:
                        # CSS selector
                        link_element = await page.query_selector(selector)
                        if link_element:
                            href = await link_element.get_attribute("href")
                            if href:
                                if href.startswith("/"):
                                    return f"https://searchland.co.uk{href}"
                                elif href.startswith("http"):
                                    return href
                except:
                    continue
            
            return None
            
        except Exception as e:
            print(f"    ⚠️ Error extracting listing link: {e}")
            return None
    
    async def process_google_sheet_data(self):
        """Process all rows in Google Sheet and update with Searchland data"""
        print("🚀 Starting Searchland data processing")
        print("=" * 50)
        
        try:
            # Get data from Google Sheet
            sheet_data = await self.get_sheet_data()
            
            if not sheet_data:
                print("❌ No data found in Google Sheet")
                return
            
            print(f"📊 Found {len(sheet_data)} rows to process")
            
            for i, row in enumerate(sheet_data):
                print(f"\n📋 Processing row {i+1}/{len(sheet_data)}")
                print(f"   Address: {row.get('address', 'N/A')}")
                print(f"   Postcode: {row.get('postcode', 'N/A')}")
                
                # Skip if already processed
                if row.get('searchland_status') == 'processed':
                    print(f"   ⏭️ Row {i+1} already processed, skipping")
                    continue
                
                # Search in Searchland
                searchland_data = await self.search_property_in_searchland(
                    row.get('address', ''),
                    row.get('postcode', '')
                )
                
                if searchland_data and searchland_data.get('extraction_status') == 'success':
                    # Update the row with Searchland data
                    updated_row = {**row, **searchland_data}
                    
                    # Update Google Sheet
                    success = await self.update_sheet_row(updated_row, i + 2)  # +2 because sheets are 1-indexed and have header
                    
                    if success:
                        self.processed_count += 1
                        print(f"   ✅ Row {i+1} processed successfully")
                    else:
                        self.error_count += 1
                        print(f"   ❌ Row {i+1} failed to update sheet")
                else:
                    self.error_count += 1
                    print(f"   ❌ Row {i+1} failed to process in Searchland")
                
                # Add delay between requests
                delay = random.uniform(2, 5)
                print(f"   ⏱️ Waiting {delay:.1f} seconds...")
                await asyncio.sleep(delay)
            
            print(f"\n📊 Processing Complete!")
            print(f"   ✅ Successfully processed: {self.processed_count}")
            print(f"   ❌ Failed: {self.error_count}")
            
        except Exception as e:
            print(f"❌ Error processing Google Sheet data: {e}")

async def main():
    """Main function to run Searchland processing"""
    processor = SearchlandSheetProcessor()
    await processor.process_google_sheet_data()

if __name__ == "__main__":
    asyncio.run(main()) 