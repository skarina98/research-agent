#!/usr/bin/env python3
"""
Listing Enrichment Workflow - Updated
Usage: python3 run_listing_enrichment_workflow.py

This workflow:
1. Reads the Google Sheet to find rows missing guide_price or source_url
2. For each missing row, Google searches: site:rightmove.co.uk "exact address"
3. If found, gets the Rightmove URL
4. Uses PropertyEngine to extract all property information
5. Updates the spreadsheet with source_url and guide_price
"""

import os
import sys
import time
import random
import re
import json
import requests
from datetime import datetime
from dateutil.relativedelta import relativedelta
from playwright.sync_api import sync_playwright
from sheets_webapp import PropertyDataManagerWebApp

class ListingEnrichmentWorkflow:
    def __init__(self):
        """Initialize the listing enrichment workflow"""
        self.sheets_manager = PropertyDataManagerWebApp()
        self.playwright = None
        self.browser = None
        self.page = None
        
    def start_browser(self):
        """Start the browser for web scraping"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)
        
        # Try to load PropertyEngine session if available
        session_file = "sessions/propertyengine.json"
        if os.path.exists(session_file):
            print(f"📁 Loading PropertyEngine session from: {session_file}")
            self.context = self.browser.new_context(storage_state=session_file)
        else:
            print("⚠️ No PropertyEngine session found, starting fresh browser")
            self.context = self.browser.new_context()
        
        self.page = self.context.new_page()
        
        # Verify PropertyEngine login status
        self.ensure_propertyengine_login()
    
    def ensure_propertyengine_login(self):
        """Ensure PropertyEngine is logged in, re-login if needed"""
        try:
            print("🔍 Checking PropertyEngine login status...")
            
            # Navigate to PropertyEngine login page to check status
            self.page.goto("https://propertyengine.co.uk/login", wait_until="networkidle")
            time.sleep(3)
            
            # Check if we're logged in by looking for login indicators
            page_text = self.page.locator("body").text_content()
            current_url = self.page.url
            
            # Check for login success indicators (if we're redirected away from login page)
            success_indicators = [
                'dashboard',
                'welcome',
                'logout',
                'profile',
                'account',
                'property',
                'search'
            ]
            
            # Check for login failure indicators (if we're still on login page)
            failure_indicators = [
                'login',
                'sign in',
                'email',
                'you@email.com',
                'enter your email'
            ]
            
            # If we're redirected away from login page, we're logged in
            if '/login' not in current_url:
                print("✅ PropertyEngine is logged in! (redirected away from login page)")
                return True
            
            # Check page content for login indicators
            is_logged_in = False
            for indicator in success_indicators:
                if indicator.lower() in page_text.lower():
                    is_logged_in = True
                    print(f"   ✅ Login indicator found: {indicator}")
                    break
            
            if not is_logged_in:
                for indicator in failure_indicators:
                    if indicator.lower() in page_text.lower():
                        print(f"   ❌ Login failure indicator found: {indicator}")
                        break
            
            if is_logged_in:
                print("✅ PropertyEngine is logged in!")
                return True
            else:
                print("❌ PropertyEngine is not logged in, attempting to login...")
                return self.login_propertyengine()
                
        except Exception as e:
            print(f"❌ Error checking PropertyEngine login: {e}")
            print("🔄 Attempting to login...")
            return self.login_propertyengine()
    
    def login_propertyengine(self):
        """Login to PropertyEngine"""
        try:
            print("🔐 Logging into PropertyEngine...")
            
            # Navigate to login page
            self.page.goto("https://propertyengine.co.uk/login", wait_until="networkidle")
            time.sleep(3)
            
            # Load credentials
            credentials_file = "credentials/propertyengine.json"
            if not os.path.exists(credentials_file):
                print("❌ PropertyEngine credentials file not found!")
                return False
            
            with open(credentials_file, 'r') as f:
                credentials = json.load(f)
                email = credentials.get('email')
            
            if not email:
                print("❌ No email found in credentials file!")
                return False
            
            # Find email field
            email_field = self.page.query_selector('input[type="email"]')
            if not email_field:
                print("❌ Could not find email field!")
                return False
            
            # Fill in email
            print(f"📝 Filling in email: {email}")
            email_field.fill("")
            email_field.type(email)
            time.sleep(1)
            
            # Find and click submit button
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Send Code")',
                'button:has-text("Send")',
                'button:has-text("Submit")',
                'button:has-text("Continue")',
                'button:has-text("Next")',
                'button'
            ]
            
            submit_button = None
            for selector in submit_selectors:
                submit_button = self.page.query_selector(selector)
                if submit_button:
                    button_text = submit_button.text_content().strip()
                    if any(word in button_text.lower() for word in ['send', 'submit', 'continue', 'next']):
                        print(f"   ✅ Found submit button: '{button_text}'")
                        break
            
            if not submit_button:
                print("❌ Could not find submit button!")
                return False
            
            # Click submit button
            print("🖱️ Clicking submit button to send verification code...")
            submit_button.click()
            time.sleep(3)
            
            # Wait for user to complete login
            print("📱 Please check your email for the verification code")
            print("   Enter the code in the browser window")
            print("   The script will wait for you to complete the login...")
            
            input("   Press Enter when you've completed the login in the browser...")
            
            # Verify login was successful
            self.page.goto("https://propertyengine.co.uk/", wait_until="networkidle")
            time.sleep(3)
            
            page_text = self.page.locator("body").text_content()
            success_indicators = ['dashboard', 'welcome', 'logout', 'profile', 'account', 'property', 'search']
            
            for indicator in success_indicators:
                if indicator.lower() in page_text.lower():
                    print("✅ PropertyEngine login successful!")
                    
                    # Save session
                    print("💾 Saving session state...")
                    self.context.storage_state(path="sessions/propertyengine.json")
                    print("   Session saved!")
                    
                    return True
            
            print("❌ PropertyEngine login verification failed!")
            return False
            
        except Exception as e:
            print(f"❌ Error during PropertyEngine login: {e}")
            return False
        
    def close_browser(self):
        """Close the browser"""
        try:
            if self.browser:
                self.browser.close()
        except Exception as e:
            print(f"⚠️ Error closing browser: {e}")
        try:
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            print(f"⚠️ Error stopping playwright: {e}")
    
    def get_missing_data_rows(self):
        """Get rows from both AUCTIONS_MASTER and POTENTIAL_TRADES sheets that are missing guide_price or source_url"""
        print("📊 Scanning both Google Sheets for rows missing guide_price or source_url...")
        
        try:
            # Always get fresh data from both Google Sheets
            print("🔄 Fetching latest data from both sheets...")
            
            import requests
            webapp_url = self.sheets_manager.webapp_url
            shared_token = self.sheets_manager.shared_token
            
            all_missing_rows = []
            
            # Process both sheets
            sheets_to_process = ['AUCTIONS_MASTER', 'POTENTIAL_TRADES']
            
            for sheet_name in sheets_to_process:
                print(f"\n📋 Processing {sheet_name} sheet...")
                
                if webapp_url and shared_token:
                    # For now, we'll use the same read action but we need to modify the Google Apps Script
                    # to support reading from different sheets. For now, let's process AUCTIONS_MASTER first
                    if sheet_name == 'AUCTIONS_MASTER':
                        payload = {
                            'token': shared_token,
                            'action': 'read',
                            'sheet_id': os.getenv('GOOGLE_SHEETS_ID', '1ONZrugWl0amSFqGLq3_hHmR82Bps-vNxr-25gGk8B9Q')
                        }
                    else:
                        # For POTENTIAL_TRADES, we'll need to implement sheet-specific reading
                        # For now, let's skip and focus on AUCTIONS_MASTER
                        print(f"   ⏭️ Skipping {sheet_name} for now - will implement sheet-specific reading")
                        continue
                    
                    response = requests.post(webapp_url, json=payload, timeout=30)
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('ok') and result.get('rows'):
                            existing_data = result.get('rows', [])
                            print(f"   ✅ Successfully fetched {len(existing_data)} rows from {sheet_name}")
                        else:
                            print(f"   ⚠️ Could not fetch from {sheet_name}, skipping")
                            continue
                    else:
                        print(f"   ⚠️ Could not fetch from {sheet_name}, skipping")
                        continue
                else:
                    print(f"   ⚠️ Could not fetch from {sheet_name}, skipping")
                    continue
                
                # Process rows from this sheet
                missing_rows = []
                for i, row in enumerate(existing_data):
                    guide_price = row.get('guide_price', '')
                    source_url = row.get('source_url', '')
                    
                    # Handle None values and convert to string
                    guide_price = str(guide_price).strip() if guide_price is not None else ''
                    source_url = str(source_url).strip() if source_url is not None else ''
                    
                    # Process rows that are missing guide_price (even if they have source_url)
                    # Skip test addresses
                    address = row.get('address', '')
                    if 'test' in address.lower():
                        print(f"      ⏭️ Row {i+1}: {address} - Skipping test address")
                        continue
                    
                    if not guide_price:
                        missing_rows.append({
                            'row_index': i,
                            'data': row,
                            'sheet_name': sheet_name,
                            'missing_guide_price': True,
                            'missing_source_url': not source_url
                        })
                        if not source_url:
                            print(f"      📋 Row {i+1}: {address} - Missing BOTH guide_price and source_url")
                        else:
                            print(f"      📋 Row {i+1}: {address} - Has source_url, missing guide_price only")
                    elif not source_url:
                        print(f"      ⏭️ Row {i+1}: {address} - Has guide_price, missing source_url only")
                    else:
                        print(f"      ✅ Row {i+1}: {address} - BOTH guide_price and source_url are filled")
                
                print(f"   📋 Found {len(missing_rows)} rows missing guide_price in {sheet_name}")
                all_missing_rows.extend(missing_rows)
            
            print(f"\n📊 Total Summary:")
            print(f"   📋 Found {len(all_missing_rows)} total rows missing guide_price across both sheets")
            if all_missing_rows:
                print(f"   📋 Will process these addresses:")
                for row_info in all_missing_rows[:5]:  # Show first 5
                    sheet_name = row_info.get('sheet_name', 'Unknown')
                    address = row_info['data'].get('address', 'Unknown')
                    print(f"      - {address} ({sheet_name})")
                if len(all_missing_rows) > 5:
                    print(f"      ... and {len(all_missing_rows) - 5} more")
            
            return all_missing_rows
            
        except Exception as e:
            print(f"❌ Error getting missing data rows: {e}")
            return []
    
    def google_search_property_sites(self, address):
        """Google search for property listings on Rightmove first, then Zoopla if needed"""
        try:
            all_links = []
            
            # Try multiple search variations for Rightmove - no quotation marks for flexibility
            search_variations = [
                f'site:rightmove.co.uk {address}',  # Full address without quotes
                f'site:rightmove.co.uk {address.replace(",", " ")}',  # Replace commas with spaces
                f'site:rightmove.co.uk {address.replace(",", "")}',  # Remove all commas
                # Street + city combinations
                f'site:rightmove.co.uk {address.split(",")[0].strip()} {address.split(",")[1].strip()}',
                f'site:rightmove.co.uk {address.split(",")[0].strip()} {address.split(",")[-1].strip()}',  # Street + postcode
                # Try without flat numbers but keep street name
                f'site:rightmove.co.uk {re.sub(r"^flat\s+\d+[,\s]*", "", address.split(",")[0].strip())} {address.split(",")[-1].strip()}',
                # Street name only
                f'site:rightmove.co.uk {address.split(",")[0].strip()}',
                # Only use postcode as last resort
                f'site:rightmove.co.uk {address.split(",")[-1].strip()}'  # Just postcode (last resort)
            ]
            
            for i, search_query in enumerate(search_variations):
                search_type = "postcode-only" if search_query.endswith(address.split(",")[-1].strip()) else "full-address"
                print(f"🔍 Step 1.{i+1}: Google searching Rightmove ({search_type}): {search_query}")
                rightmove_links = self._search_specific_site(search_query, "rightmove.co.uk", "Rightmove")
                all_links.extend(rightmove_links)
                
                # If we have enough links, stop (but don't stop if we only have postcode results)
                if len(all_links) >= 3 and search_type != "postcode-only":
                    print(f"   ✅ Found sufficient results with {search_type} search, stopping")
                    break
            
            # Remove duplicates while preserving order
            unique_links = []
            seen = set()
            for link in all_links:
                if link not in seen:
                    unique_links.append(link)
                    seen.add(link)
            
            if unique_links:
                print(f"✅ Found {len(unique_links)} unique Rightmove links")
                return unique_links[:5]  # Return first 5 unique links
            
            # If no Rightmove links found, try Zoopla
            print(f"🔍 Step 2: Google searching Zoopla: site:zoopla.co.uk {address}")
            zoopla_links = self._search_specific_site(f"site:zoopla.co.uk {address}", "zoopla.co.uk", "Zoopla")
            
            return zoopla_links
            
        except Exception as e:
            print(f"❌ Error Google searching property sites: {e}")
            return []
    
    def _search_specific_site(self, search_query, site_domain, site_name):
        """Search for listings on a specific property site"""
        try:
            # Construct the search URL
            search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
            
            # Navigate to Google search
            self.page.goto(search_url, wait_until="networkidle")
            time.sleep(random.uniform(2, 4))
            
            # Wait for CAPTCHA if present
            print("⏱️ Waiting 45 seconds for potential CAPTCHA...")
            time.sleep(45)
            
            # Look for property site links
            property_links = []
            links = self.page.query_selector_all(f"a[href*='{site_domain}']")
            
            for link in links:
                try:
                    href = link.get_attribute('href')
                    if href and f'{site_domain}/properties' in href:
                        # Extract the actual URL from Google's redirect
                        if '/url?q=' in href:
                            # Extract the actual URL from Google's redirect
                            match = re.search(r'/url\?q=([^&]+)', href)
                            if match:
                                actual_url = match.group(1)
                                actual_url = actual_url.replace('%3F', '?').replace('%3D', '=')
                                property_links.append(actual_url)
                                print(f"   ✅ Found {site_name} link: {actual_url}")
                        else:
                            property_links.append(href)
                            print(f"   ✅ Found {site_name} link: {href}")
                except Exception as e:
                    print(f"   ⚠️ Error extracting link: {e}")
                    continue
            
            print(f"📋 Found {len(property_links)} {site_name} links")
            return property_links[:3]  # Return first 3 links
            
        except Exception as e:
            print(f"❌ Error Google searching {site_name}: {e}")
            return []
    
    def verify_property_address(self, property_url, target_address):
        """Verify that the property page is for the correct address - more flexible matching"""
        try:
            # Determine the site type from URL
            if 'rightmove.co.uk' in property_url:
                site_name = "Rightmove"
            elif 'zoopla.co.uk' in property_url:
                site_name = "Zoopla"
            else:
                site_name = "Property site"
            
            print(f"🔍 Verifying address on {site_name}: {property_url}")
            
            # Navigate to the property page
            self.page.goto(property_url, wait_until="networkidle")
            time.sleep(3)
            
            # Get page content
            page_text = self.page.locator("body").text_content()
            page_title = self.page.title()
            
            # Extract key parts of the target address
            target_parts = target_address.lower().split(',')
            street_part = target_parts[0].strip() if target_parts else ""
            city_part = target_parts[1].strip() if len(target_parts) > 1 else ""
            postcode_part = target_parts[-1].strip() if len(target_parts) > 2 else ""
            
            # Clean up street part (remove flat numbers, etc.)
            street_clean = re.sub(r'^flat\s+\d+[,\s]*', '', street_part)
            # Don't remove house number for matching - we need it for exact verification
            street_clean = street_clean.strip()
            
            # Handle empty street_clean (when flat number was removed)
            if not street_clean:
                # Extract the rest of the address after the flat number
                remaining_parts = target_address.split(',')[1:] if len(target_address.split(',')) > 1 else []
                if remaining_parts:
                    street_clean = remaining_parts[0].strip()
            
            # Check for address match in page content with strict matching
            address_found = False
            match_reason = ""
            
            # Strategy 1: Full address match (exact) - highest priority
            if target_address.lower() in page_text.lower():
                address_found = True
                match_reason = "Full address match"
            
            # Strategy 2: Postcode + street number match (very reliable)
            elif postcode_part and postcode_part in page_text.lower():
                # Extract house number from street part
                house_number_match = re.search(r'^(\d+)', street_part)
                if house_number_match:
                    house_number = house_number_match.group(1)
                    if house_number in page_text.lower():
                        address_found = True
                        match_reason = f"Postcode + house number match ({house_number})"
            
            # Strategy 3: Postcode + street name match (reliable)
            elif postcode_part and postcode_part in page_text.lower():
                if street_clean and street_clean in page_text.lower():
                    address_found = True
                    match_reason = "Postcode + street name match"
                else:
                    # Try matching just the street name without house number
                    street_name_only = re.sub(r'^\d+\s+', '', street_clean)
                    if street_name_only and street_name_only in page_text.lower():
                        address_found = True
                        match_reason = f"Postcode + street name only match ({street_name_only})"
            
            # Strategy 3.5: Handle postcode format variations
            elif postcode_part:
                # Try different postcode formats
                postcode_variations = [
                    postcode_part,
                    postcode_part.replace(' ', ''),
                    postcode_part.upper(),
                    postcode_part.upper().replace(' ', '')
                ]
                
                for postcode_var in postcode_variations:
                    if postcode_var in page_text.lower():
                        # Extract house number from street part
                        house_number_match = re.search(r'^(\d+)', street_part)
                        if house_number_match:
                            house_number = house_number_match.group(1)
                            if house_number in page_text.lower():
                                address_found = True
                                match_reason = f"Postcode variation + house number match ({house_number})"
                                break
                        
                        # Also try with street name (without house number)
                        if street_clean:
                            street_name_only = re.sub(r'^\d+\s+', '', street_clean)
                            if street_name_only and street_name_only in page_text.lower():
                                address_found = True
                                match_reason = f"Postcode variation + street name match ({street_name_only})"
                                break
            
            # Strategy 4: Street number + street name + postcode (exact match)
            elif street_clean:
                house_number_match = re.search(r'^(\d+)', street_part)
                if house_number_match:
                    house_number = house_number_match.group(1)
                    street_name = street_clean
                    if (house_number in page_text.lower() and 
                        street_name in page_text.lower() and 
                        postcode_part in page_text.lower()):
                        address_found = True
                        match_reason = f"House number + street + postcode match ({house_number} {street_name} {postcode_part})"
            
            # Strategy 5: House number + street name (without postcode - for cases where postcode format differs)
            elif street_clean:
                house_number_match = re.search(r'^(\d+)', street_part)
                if house_number_match:
                    house_number = house_number_match.group(1)
                    street_name = street_clean
                    if (house_number in page_text.lower() and 
                        street_name in page_text.lower()):
                        address_found = True
                        match_reason = f"House number + street name match ({house_number} {street_name})"
            
            # Strategy 5: Check page title for exact address components
            if not address_found:
                house_number_match = re.search(r'^(\d+)', street_part)
                if house_number_match:
                    house_number = house_number_match.group(1)
                    if (house_number in page_title.lower() and 
                        street_clean in page_title.lower() and 
                        postcode_part in page_title.lower()):
                        address_found = True
                        match_reason = "Exact address in page title"
            
            if address_found:
                print(f"   ✅ Address verified: {match_reason}")
                print(f"   📄 Target: {target_address}")
                print(f"   📄 Found in: {page_title[:100]}...")
                return True
            else:
                print(f"   ❌ Address not found on {site_name} page")
                print(f"   📄 Looking for: {target_address}")
                print(f"   📄 Street part: {street_part}")
                print(f"   📄 Clean street: {street_clean}")
                print(f"   📄 Postcode: {postcode_part}")
                print(f"   📄 Page title: {page_title}")
                
                # Show what we found on the page for debugging
                house_number_match = re.search(r'^(\d+)', street_part)
                if house_number_match:
                    house_number = house_number_match.group(1)
                    print(f"   🔍 Looking for house number: {house_number}")
                    print(f"   🔍 Looking for street name: {street_clean}")
                    print(f"   🔍 Looking for postcode: {postcode_part}")
                    
                    # Check what's actually on the page
                    if house_number in page_text.lower():
                        print(f"   ✅ House number {house_number} found on page")
                    else:
                        print(f"   ❌ House number {house_number} NOT found on page")
                    
                    if street_clean in page_text.lower():
                        print(f"   ✅ Street name '{street_clean}' found on page")
                    else:
                        print(f"   ❌ Street name '{street_clean}' NOT found on page")
                    
                    # Check postcode variations
                    postcode_variations = [
                        postcode_part,
                        postcode_part.replace(' ', ''),
                        postcode_part.upper(),
                        postcode_part.upper().replace(' ', '')
                    ]
                    
                    postcode_found = False
                    for postcode_var in postcode_variations:
                        if postcode_var in page_text.lower():
                            print(f"   ✅ Postcode variation '{postcode_var}' found on page")
                            postcode_found = True
                            break
                    
                    if not postcode_found:
                        print(f"   ❌ No postcode variations found: {postcode_variations}")
                
                return False
            
        except Exception as e:
            print(f"❌ Error verifying {site_name} address: {e}")
            return False
    
    def extract_from_propertyengine(self, property_url, auction_name=None, auction_date=None):
        """Extract property information from PropertyEngine using property URL"""
        try:
            print(f"🔍 Extracting from PropertyEngine: {property_url}")
            
            # Ensure we're logged in to PropertyEngine
            if not self.ensure_propertyengine_login():
                print("❌ Could not login to PropertyEngine")
                return None
            
            # Navigate directly to PropertyEngine properties page where the paste link input is located
            propertyengine_url = "https://propertyengine.co.uk/properties"
            self.page.goto(propertyengine_url, wait_until="networkidle")
            time.sleep(3)
            
            print(f"📋 Page title: {self.page.title()}")
            print(f"🔗 Current URL: {self.page.url}")
            
            # Take screenshot to see the current state
            self.page.screenshot(path="propertyengine_current_state.png")
            print("📸 Screenshot saved: propertyengine_current_state.png")
            
            # Look for input field to paste the Rightmove URL
            # This will depend on PropertyEngine's interface
            # For now, let's assume there's an input field with a placeholder or label
            
            # Look for the "Paste Link" button in the header
            paste_link_button_selectors = [
                'button:has-text("Paste Link")',
                'a:has-text("Paste Link")',
                '[data-testid*="paste"]',
                '[class*="paste"]',
                'button[title*="Paste"]',
                'a[title*="Paste"]',
                'button:has-text("paste link")',
                'a:has-text("paste link")'
            ]
            
            paste_link_button = None
            for selector in paste_link_button_selectors:
                paste_link_button = self.page.query_selector(selector)
                if paste_link_button:
                    button_text = paste_link_button.text_content().strip()
                    print(f"   ✅ Found Paste Link button with selector: {selector}")
                    print(f"   Button text: '{button_text}'")
                    break
            
            if not paste_link_button:
                print(f"   ❌ Could not find Paste Link button on PropertyEngine")
                return None
            
            # Click on the Paste Link button
            print(f"   🖱️ Clicking on Paste Link button...")
            paste_link_button.click()
            time.sleep(2)
            
            # Now look for the input field that appears after clicking Paste Link
            input_selectors = [
                'input[placeholder*="paste"]',
                'input[placeholder*="Paste"]',
                'input[placeholder*="link"]',
                'input[placeholder*="Link"]',
                'input[placeholder*="URL"]',
                'input[placeholder*="url"]',
                'input[type="text"]',
                'input[type="url"]',
                'textarea'
            ]
            
            input_field = None
            for selector in input_selectors:
                input_field = self.page.query_selector(selector)
                if input_field:
                    placeholder = input_field.get_attribute('placeholder') or ''
                    print(f"   ✅ Found input field after clicking Paste Link: {selector}")
                    print(f"   Placeholder: '{placeholder}'")
                    break
            
            if not input_field:
                print(f"   ❌ Could not find input field after clicking Paste Link")
                return None
            
            # Clear and paste the property URL
            print(f"   📝 Pasting property URL: {property_url}")
            input_field.fill("")
            input_field.type(property_url)
            time.sleep(3)
            
            # Press Enter to trigger any validation
            print(f"   ⌨️ Pressing Enter to validate input...")
            input_field.press("Enter")
            time.sleep(2)
            
            # Look for submit button
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Search")',
                'button:has-text("Submit")',
                'button:has-text("Analyze")',
                'button:has-text("Go")',
                'button'
            ]
            
            submit_button = None
            for selector in submit_selectors:
                submit_button = self.page.query_selector(selector)
                if submit_button:
                    print(f"   ✅ Found submit button with selector: {selector}")
                    break
            
            if not submit_button:
                print(f"   ❌ Could not find submit button on PropertyEngine")
                return None
            
            # Try to submit the form
            print(f"   🖱️ Attempting to submit form...")
            
            # Try clicking the submit button first
            try:
                submit_button.click()
                print(f"   ✅ Submit button clicked successfully")
            except Exception as e:
                print(f"   ⚠️ Could not click submit button: {e}")
                
                # Try pressing Enter on the input field instead
                print(f"   ⌨️ Trying to press Enter on input field...")
                try:
                    input_field.press("Enter")
                    print(f"   ✅ Enter pressed on input field")
                except Exception as e2:
                    print(f"   ⚠️ Could not press Enter: {e2}")
                    # Continue anyway - the form might have auto-submitted
                    print(f"   🔄 Continuing with extraction...")
            
            time.sleep(5)
            
            # Get the current PropertyEngine URL - this is what we want as source_url
            propertyengine_current_url = self.page.url
            print(f"   🔗 Current PropertyEngine URL: {propertyengine_current_url}")
            
            # Validate that we're on a proper PropertyEngine property page
            if not propertyengine_current_url.startswith('https://propertyengine.co.uk/property/'):
                print(f"   ⚠️ Not on a PropertyEngine property page, trying to navigate...")
                
                # Look for property links on the current page
                property_links = self.page.query_selector_all('a[href*="/property/"]')
                if property_links:
                    print(f"   🔗 Found {len(property_links)} property links, clicking first one...")
                    property_links[0].click()
                    time.sleep(3)
                    propertyengine_current_url = self.page.url
                    print(f"   🔗 Updated PropertyEngine URL: {propertyengine_current_url}")
                else:
                    print(f"   ⚠️ No property links found, using current URL")
            
            # Final validation of PropertyEngine URL
            if not propertyengine_current_url.startswith('https://propertyengine.co.uk/property/'):
                print(f"   ❌ Invalid PropertyEngine URL: {propertyengine_current_url}")
                return None
            
            # Look for the property pop-up that appears after submitting
            print(f"   🔍 Looking for property pop-up...")
            
            # Try to find and click on the property pop-up/dialog
            popup_selectors = [
                '[role="dialog"]',
                '.modal',
                '.popup',
                '.dialog',
                '[class*="modal"]',
                '[class*="popup"]',
                '[class*="dialog"]',
                'div[class*="overlay"]',
                'div[class*="modal"]'
            ]
            
            popup = None
            for selector in popup_selectors:
                popup = self.page.query_selector(selector)
                if popup and popup.is_visible():
                    print(f"   ✅ Found property pop-up with selector: {selector}")
                    break
            
            if not popup:
                # If no popup found, try clicking on the property listing that should appear
                print(f"   🔄 No popup found, looking for property listing to click...")
                property_listing_selectors = [
                    'div[class*="property"]',
                    'div[class*="listing"]',
                    'div[class*="card"]',
                    'a[href*="property"]',
                    'div[class*="result"]'
                ]
                
                for selector in property_listing_selectors:
                    property_elem = self.page.query_selector(selector)
                    if property_elem and property_elem.is_visible():
                        print(f"   ✅ Found property listing with selector: {selector}")
                        print(f"   🖱️ Clicking on property listing...")
                        property_elem.click()
                        time.sleep(3)
                        break
            
            # Take screenshot to see current state
            self.page.screenshot(path="propertyengine_after_submit.png")
            print("📸 Screenshot saved: propertyengine_after_submit.png")
            
            # Wait a bit more for timeline to load
            print(f"   ⏳ Waiting for timeline to load...")
            time.sleep(5)
            
            # Extract property information from the current page
            page_text = self.page.locator("body").text_content()
            
            # Look for guide price in the extracted data
            guide_price = None
            
            # First, try to find guide price in the current page text
            # Prioritize exact "GUIDE PRICE" matches first
            guide_price_patterns = [
                # Most specific patterns first
                r'Guide\s+Price\s*[=:]\s*£([\d,]+(?:,\d{3})*\+?)',
                r'Guide\s+Price\s*£([\d,]+(?:,\d{3})*\+?)',
                r'GUIDE\s+PRICE\s*£([\d,]+(?:,\d{3})*\+?)',
                r'Guide\s+Price\s*:\s*£([\d,]+(?:,\d{3})*\+?)',
                # PropertyEngine specific patterns
                r'Guide\s+Price.*?£([\d,]+(?:,\d{3})*\+?)',
                r'Guide\s+price.*?£([\d,]+(?:,\d{3})*\+?)',
                # More flexible patterns
                r'Guide.*?£([\d,]+(?:,\d{3})*\+?)',
                r'Estimate.*?£([\d,]+(?:,\d{3})*\+?)',
                r'Estimated.*?£([\d,]+(?:,\d{3})*\+?)',
                r'£([\d,]+(?:,\d{3})*\+?)\s*Guide\s+Price',
                r'£([\d,]+(?:,\d{3})*\+?)\s*GUIDE\s+PRICE',
                r'£([\d,]+(?:,\d{3})*\+?)\s*guide',
                r'£([\d,]+(?:,\d{3})*\+?)\s*estimate'
            ]
            
            # Try to find guide price with context validation
            for pattern in guide_price_patterns:
                matches = re.finditer(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    price_value = match.group(1)
                    price_num = int(price_value.replace(',', ''))
                    
                    # Get context around the match
                    start = max(0, match.start() - 100)
                    end = min(len(page_text), match.end() + 100)
                    context = page_text[start:end]
                    
                    # Validate that this is likely a guide price (not a sold price, etc.)
                    context_lower = context.lower()
                    invalid_indicators = [
                        'sold for', 'sold at', 'sold price', 'purchase price',
                        'last sold', 'previously sold', 'sale price',
                        'rent', 'rental', 'per month', 'pcm'
                    ]
                    
                    is_valid_guide_price = True
                    for indicator in invalid_indicators:
                        if indicator in context_lower:
                            is_valid_guide_price = False
                            print(f"   ⚠️ Skipping price £{price_value} - found invalid indicator: {indicator}")
                            break
                    
                    # Check if price is reasonable for a guide price (typically £50k+)
                    if price_num < 50000:
                        print(f"   ⚠️ Skipping price £{price_value} - too low for guide price")
                        continue
                    
                    if is_valid_guide_price:
                        guide_price = f"£{price_value}"
                        print(f"   💰 Found valid guide price: {guide_price}")
                        print(f"   📄 Pattern: {pattern}")
                        print(f"   📄 Context: ...{context}...")
                        break
                
                if guide_price:
                    break
            
            # If not found in page text, try to find it in specific elements
            if not guide_price:
                print(f"   🔍 Looking for guide price in specific elements...")
                
                # Look for elements that might contain the guide price
                price_selectors = [
                    '[class*="price"]',
                    '[class*="guide"]',
                    '[class*="estimate"]',
                    'span[class*="price"]',
                    'div[class*="price"]',
                    'p[class*="price"]'
                ]
                
                for selector in price_selectors:
                    elements = self.page.query_selector_all(selector)
                    for element in elements:
                        element_text = element.text_content().strip()
                        if element_text and '£' in element_text and ('guide' in element_text.lower() or 'estimate' in element_text.lower()):
                            # Extract price from element text
                            price_match = re.search(r'£([\d,]+(?:,\d{3})*\+?)', element_text)
                            if price_match:
                                guide_price = f"£{price_match.group(1)}"
                                print(f"   💰 Found guide price in element: {guide_price}")
                                break
                    if guide_price:
                        break
            
            # If still not found, try to get the main price displayed
            if not guide_price:
                print(f"   🔍 Looking for any price information...")
                
                # Look for any price-like text on the page, but be more specific
                # Avoid picking up small amounts like £602
                price_matches = re.findall(r'£([\d,]+(?:,\d{3})*\+?)', page_text)
                if price_matches:
                    # Filter out small amounts (likely not guide prices)
                    valid_prices = []
                    for price in price_matches:
                        # Remove commas and convert to int for comparison
                        price_num = int(price.replace(',', ''))
                        if price_num >= 50000:  # Guide prices are typically £50k+
                            valid_prices.append(price)
                    
                    if valid_prices:
                        guide_price = f"£{valid_prices[0]}"
                        print(f"   💰 Found valid price: {guide_price}")
                    else:
                        print(f"   ⚠️ No valid guide prices found (all prices were too small)")
            
            # Now look for the activity timeline to find the original listing
            print(f"   🔍 Looking for activity timeline...")
            
            # Look for timeline/activity sections
            timeline_selectors = [
                '[class*="timeline"]',
                '[class*="activity"]',
                '[class*="history"]',
                '[class*="events"]',
                'div[class*="timeline"]',
                'div[class*="activity"]',
                'section[class*="timeline"]',
                'section[class*="activity"]'
            ]
            
            timeline_section = None
            for selector in timeline_selectors:
                timeline_section = self.page.query_selector(selector)
                if timeline_section and timeline_section.is_visible():
                    print(f"   ✅ Found timeline section with selector: {selector}")
                    break
            
            if not timeline_section:
                print(f"   ⚠️ No timeline section found, looking for any activity-related content...")
                # Try to find any content that might contain activity information
                page_text_lower = page_text.lower()
                if 'sold' in page_text_lower or 'auction' in page_text_lower or 'listed' in page_text_lower:
                    print(f"   🔍 Found activity-related content in page text")
                    timeline_section = self.page  # Use the whole page as fallback
            
            if timeline_section:
                # Use auction date from spreadsheet (passed as parameter)
                if auction_date:
                    print(f"   📅 Using auction date from spreadsheet: {auction_date}")
                else:
                    print(f"   ⚠️ No auction date provided from spreadsheet")
                
                timeline_text = timeline_section.text_content()
                print(f"   📄 Timeline text preview: {timeline_text[:2000]}...")
                
                # Debug: Look for specific keywords in the timeline text
                print(f"   🔍 Debug: Looking for keywords in timeline...")
                keywords = ['sold', 'Sold', 'Property sold', 'property sold', '£50,000', '£50000']
                for keyword in keywords:
                    if keyword in timeline_text:
                        print(f"   ✅ Found keyword: '{keyword}'")
                    else:
                        print(f"   ❌ Not found: '{keyword}'")
                
                # Look for "property sold for xxx" in the timeline
                sold_patterns = [
                    r'Property\s+sold\s+for\s+£([\d,]+(?:,\d{3})*\+?)(?:\s*\([^)]*\))?',  # Handles percentage changes
                    r'property\s+sold\s+for\s+£([\d,]+(?:,\d{3})*\+?)(?:\s*\([^)]*\))?',
                    r'Sold\s+for\s+£([\d,]+(?:,\d{3})*\+?)(?:\s*\([^)]*\))?',
                    r'sold\s+for\s+£([\d,]+(?:,\d{3})*\+?)(?:\s*\([^)]*\))?',
                    # More flexible patterns
                    r'sold\s+for\s+£([\d,]+)',
                    r'Sold\s+for\s+£([\d,]+)',
                    r'Property\s+sold.*?£([\d,]+)',
                    r'property\s+sold.*?£([\d,]+)'
                ]
                
                # Also look for specific sold patterns in the full text
                print(f"   🔍 Searching for sold patterns in timeline...")
                sold_found_in_text = False
                for pattern in sold_patterns:
                    matches = re.findall(pattern, timeline_text, re.IGNORECASE)
                    if matches:
                        print(f"   ✅ Found sold entries: {matches}")
                        sold_found_in_text = True
                        break
                
                if not sold_found_in_text:
                    print(f"   ⚠️ No sold patterns found in timeline text")
                    
                    # Try looking for the HTML structure instead
                    print(f"   🔍 Trying to find sold entries in HTML structure...")
                    
                    # Look for elements with the specific class we identified
                    print(f"   🔍 Looking for elements with class 'sc-1eup7iu-0'...")
                    sold_elements = timeline_section.query_selector_all('div.sc-1eup7iu-0')
                    
                    if not sold_elements:
                        print(f"   🔍 Trying in entire page for class 'sc-1eup7iu-0'...")
                        sold_elements = self.page.query_selector_all('div.sc-1eup7iu-0')
                    
                    if not sold_elements:
                        print(f"   🔍 Trying partial class match...")
                        sold_elements = timeline_section.query_selector_all('div[class*="sc-1eup7iu-0"]')
                    
                    if not sold_elements:
                        print(f"   🔍 Trying alternative selectors...")
                        # Fallback to text-based selectors
                        sold_elements = timeline_section.query_selector_all('div:has-text("Property sold for")')
                        sold_elements.extend(timeline_section.query_selector_all('div:has-text("property sold for")'))
                        sold_elements.extend(timeline_section.query_selector_all('div:has-text("Sold for")'))
                        sold_elements.extend(timeline_section.query_selector_all('div:has-text("sold for")'))
                    
                    if sold_elements:
                        print(f"   ✅ Found {len(sold_elements)} sold elements in HTML structure")
                        for i, element in enumerate(sold_elements):
                            element_text = element.text_content().strip()
                            print(f"   📄 Sold element {i+1}: '{element_text}'")
                            
                            # Extract price from the element
                            price_match = re.search(r'£([\d,]+(?:,\d{3})*\+?)', element_text)
                            if price_match:
                                sold_price = f"£{price_match.group(1)}"
                                print(f"   💰 Found sold price: {sold_price}")
                                
                                # Check if this is a complete sold entry
                                if ('Property sold for' in element_text or 'property sold for' in element_text or 
                                    'Sold for' in element_text and '£' in element_text):
                                    print(f"   ✅ Found complete sold entry: {element_text}")
                                    sold_found_in_text = True
                                    break
                                else:
                                    print(f"   ⚠️ Found price but not a sold entry: {element_text}")
                    else:
                        print(f"   ❌ No sold elements found in HTML structure")
                
                # Now check if we found a sold entry
                if sold_found_in_text:
                    print(f"   ✅ Found 'property sold for xxx' in timeline")
                    sold_found = True
                    sold_date = None  # We'll extract this next
                else:
                    print(f"   ⚠️ No 'property sold for xxx' found in timeline")
                    print(f"   ⏭️ No usable timeline data, but keeping guide price")
                    # Return guide price even if timeline has no usable data
                    return {
                        'source_url': propertyengine_current_url,  # Use PropertyEngine URL
                        'guide_price': guide_price if guide_price else ''
                    }
                # Extract sold date from the found sold entry
                if sold_found:
                    print(f"   🔍 Extracting sold date from timeline...")
                    
                    # First, try to find the date in the specific sold element we found
                    sold_element_text = None
                    for element in sold_elements:
                        element_text = element.text_content().strip()
                        if 'Property sold for' in element_text or 'property sold for' in element_text:
                            sold_element_text = element_text
                            print(f"   📄 Using sold element text: {sold_element_text}")
                            break
                    
                    # Look for the specific date element with class wd32zq-1
                    print(f"   🔍 Looking for date element with class 'wd32zq-1'...")
                    date_elements = timeline_section.query_selector_all('div.wd32zq-1')
                    if not date_elements:
                        date_elements = self.page.query_selector_all('div.wd32zq-1')
                    
                    if date_elements:
                        print(f"   ✅ Found {len(date_elements)} date elements")
                        
                        # Find the sold element first to get its position
                        sold_element_index = None
                        for i, element in enumerate(sold_elements):
                            element_text = element.text_content().strip()
                            if 'Property sold for' in element_text or 'property sold for' in element_text:
                                sold_element_index = i
                                print(f"   📍 Sold element found at index: {sold_element_index}")
                                break
                        
                        # Extract the sold date from the sold element text
                        if sold_element_text:
                            # Look for date pattern in the sold element text
                            date_match = re.search(r'(\w{3}\s+\w{3}\s+\d{1,2},?\s+\d{4})', sold_element_text)
                            if date_match:
                                sold_date = date_match.group(1)
                                print(f"   ✅ Found sold date in sold element text: {sold_date}")
                            else:
                                print(f"   ⚠️ Could not extract date from sold element text")
                        else:
                            print(f"   ⚠️ No sold element text found")
                    
                    # Fallback: Look for date patterns in the sold element text
                    if not sold_date and sold_element_text:
                        print(f"   🔍 Fallback: Looking for date patterns in sold element text...")
                        date_patterns = [
                            r'(\w{3}\s+\w{3}\s+\d{1,2},?\s+\d{4})',  # Mon Mar 24, 2025
                            r'(\w{3}\s+\w{3}\s+\d{1,2}\s+\d{4})',   # Mon Mar 24 2025
                            r'(\d{1,2}/\d{1,2}/\d{4})',             # 24/03/2025
                            r'(\d{1,2}-\d{1,2}-\d{4})'              # 24-03-2025
                        ]
                        
                        for pattern in date_patterns:
                            match = re.search(pattern, sold_element_text)
                            if match:
                                sold_date = match.group(1)
                                print(f"   📅 Found sold date via regex: {sold_date}")
                                break
                    
                    if not sold_date:
                        print(f"   ⚠️ Could not extract sold date from timeline")
                
                if sold_found:
                    # Look for the first listing underneath that's within 12 months
                    print(f"   🔍 Looking for original listing within 12 months...")
                    
                    # Look for "view listing" links in the timeline
                    print(f"   🔍 Looking for 'view listing' links...")
                    view_listing_links = timeline_section.query_selector_all('a:has-text("view listing")')
                    
                    if not view_listing_links:
                        print(f"   🔍 Trying alternative selectors for view listing links...")
                        view_listing_links = timeline_section.query_selector_all('a[href*="rightmove"]')
                        view_listing_links.extend(timeline_section.query_selector_all('a[href*="zoopla"]'))
                        view_listing_links.extend(timeline_section.query_selector_all('a[href*="onthemarket"]'))
                    
                    if not view_listing_links:
                        print(f"   🔍 Looking for elements containing 'view listing' text...")
                        # Look for elements that contain "view listing" text (case insensitive)
                        view_listing_elements = timeline_section.query_selector_all('div:has-text("view listing")')
                        view_listing_elements.extend(timeline_section.query_selector_all('div:has-text("View listing")'))
                        view_listing_elements.extend(timeline_section.query_selector_all('div:has-text("VIEW LISTING")'))
                        
                        if view_listing_elements:
                            print(f"   ✅ Found {len(view_listing_elements)} elements containing 'view listing' text")
                            for i, element in enumerate(view_listing_elements):
                                element_text = element.text_content().strip()
                                print(f"   📄 View listing element {i+1}: '{element_text}'")
                                
                                # Look for links within this element
                                links_in_element = element.query_selector_all('a')
                                if links_in_element:
                                    print(f"   🔗 Found {len(links_in_element)} links in element {i+1}")
                                    view_listing_links.extend(links_in_element)
                                else:
                                    print(f"   ⚠️ No links found in element {i+1}")
                    
                    # Also try looking for links with href starting with /property/
                    if not view_listing_links:
                        print(f"   🔍 Looking for PropertyEngine internal links...")
                        property_links = timeline_section.query_selector_all('a[href^="/property/"]')
                        if property_links:
                            print(f"   ✅ Found {len(property_links)} PropertyEngine property links")
                            view_listing_links.extend(property_links)
                    
                    # Try looking for any links in the timeline section
                    if not view_listing_links:
                        print(f"   🔍 Looking for the element after the sold entry...")
                        
                        # Find the sold element index
                        sold_element_index = None
                        for i, element in enumerate(sold_elements):
                            element_text = element.text_content().strip()
                            if 'Property sold for' in element_text or 'property sold for' in element_text:
                                sold_element_index = i
                                print(f"   📍 Sold element found at index: {sold_element_index}")
                                break
                        
                        # Look for the next element after the sold entry
                        if sold_element_index is not None and sold_element_index + 1 < len(sold_elements):
                            next_element = sold_elements[sold_element_index + 1]
                            next_element_text = next_element.text_content().strip()
                            print(f"   📄 Next element after sold entry: '{next_element_text}'")
                            
                            # Look for links in this next element
                            links_in_next = next_element.query_selector_all('a')
                            if links_in_next:
                                print(f"   ✅ Found {len(links_in_next)} links in next element")
                                view_listing_links.extend(links_in_next)
                            else:
                                print(f"   ⚠️ No links found in next element")
                        else:
                            print(f"   ⚠️ Could not find next element after sold entry")
                    
                    # Fallback: Try looking for any links in the timeline section
                    if not view_listing_links:
                        print(f"   🔍 Looking for any links in timeline section...")
                        all_links = timeline_section.query_selector_all('a')
                        if all_links:
                            print(f"   ✅ Found {len(all_links)} total links in timeline")
                            for i, link in enumerate(all_links):
                                link_text = link.text_content().strip()
                                link_href = link.get_attribute('href')
                                print(f"   🔗 Link {i+1}: text='{link_text}', href='{link_href}'")
                            view_listing_links = all_links
                    
                    if view_listing_links:
                        print(f"   ✅ Found {len(view_listing_links)} view listing links")
                        
                        # Initialize source_url to PropertyEngine URL
                        source_url = propertyengine_current_url
                        suitable_listing_found = False
                        
                        # Check each listing link to see if it meets our criteria
                        for i, listing_link in enumerate(view_listing_links):
                            print(f"   🔍 Checking listing link {i+1}...")
                            
                            # Get the link text and href
                            link_text = listing_link.text_content().strip()
                            link_href = listing_link.get_attribute('href')
                            print(f"   📄 Link text: '{link_text}'")
                            print(f"   🔗 Link href: '{link_href}'")
                            
                            # Click the link to go to the listing page
                            print(f"   🖱️ Clicking on view listing link...")
                            listing_link.click()
                            time.sleep(3)
                            
                            # Get the current URL (should be the original listing)
                            current_url = self.page.url
                            print(f"   🔗 Current URL: {current_url}")
                            
                            # Check the auction name on this listing page
                            listing_page_text = self.page.locator("body").text_content()
                            
                            # Look for auction name patterns on the listing page
                            auction_name_found = None
                            auction_name_patterns = [
                                r'Auction\s+House\s+([A-Za-z\s]+)',
                                r'([A-Za-z\s]+)\s+Auction',
                                r'Auctioneer[:\s]*([A-Za-z\s]+)',
                                r'([A-Za-z\s]+)\s+Auctioneers',
                                r'([A-Za-z\s]+)\s+Property\s+Auctions',
                                r'([A-Za-z\s]+)\s+Auction\s+House'
                            ]
                            
                            # First, try to find auction name in the page title
                            page_title = self.page.title()
                            print(f"   📋 Page title: {page_title}")
                            
                            for pattern in auction_name_patterns:
                                match = re.search(pattern, page_title, re.IGNORECASE)
                                if match:
                                    auction_name_found = match.group(1).strip()
                                    print(f"   🏢 Found auction name in title: {auction_name_found}")
                                    break
                            
                            # If not found in title, try the page content
                            if not auction_name_found:
                                for pattern in auction_name_patterns:
                                    match = re.search(pattern, listing_page_text, re.IGNORECASE)
                                if match:
                                    auction_name_found = match.group(1).strip()
                                    print(f"   🏢 Found auction name on listing: {auction_name_found}")
                                    break
                            
                            # Compare with auction name from our database
                            if auction_name and auction_name_found:
                                print(f"   🏢 Comparing auction names:")
                                print(f"      Database: {auction_name}")
                                print(f"      Listing: {auction_name_found}")
                                
                                # Check if auction names are different
                                if auction_name.lower() != auction_name_found.lower():
                                    print(f"   ✅ Auction names are different")
                                    
                                    # Now check the timeframe - listing should be within 12 months prior to auction date
                                    if auction_date:
                                        # Extract listing date from the timeline text
                                        listing_date_match = re.search(r'([A-Za-z]{3}\s+[A-Za-z]{3}\s+\d{1,2},?\s+\d{4})', timeline_text)
                                        if listing_date_match:
                                            listing_date_str = listing_date_match.group(1)
                                            print(f"   📅 Listing date: {listing_date_str}")
                                            print(f"   📅 Auction date: {auction_date}")
                                            
                                            # Convert dates to datetime objects for comparison
                                            try:
                                                # Parse listing date (format: "Wed Apr 30, 2025")
                                                listing_date = datetime.strptime(listing_date_str, "%a %b %d, %Y")
                                                
                                                # Parse auction date (format: "Wed Apr 30, 2025")
                                                auction_date_obj = datetime.strptime(auction_date, "%a %b %d, %Y")
                                                
                                                # Calculate difference in months
                                                date_diff = relativedelta(auction_date_obj, listing_date)
                                                months_diff = date_diff.years * 12 + date_diff.months
                                                
                                                print(f"   📊 Months between listing and auction: {months_diff}")
                                                
                                                if months_diff <= 12 and months_diff >= 0:
                                                    print(f"   ✅ Listing is within 12 months prior to auction")
                                                    source_url = current_url
                                                    suitable_listing_found = True
                                                    print(f"   🔗 Using PropertyEngine URL as source_url: {source_url}")
                                                    break
                                                else:
                                                    print(f"   ❌ Listing is outside 12-month timeframe")
                                                    # Go back to PropertyEngine page to try next listing
                                                    self.page.go_back()
                                                    time.sleep(2)
                                                    continue
                                                    
                                            except Exception as e:
                                                print(f"   ⚠️ Error parsing dates: {e}")
                                                # If date parsing fails, skip this listing
                                                self.page.go_back()
                                                time.sleep(2)
                                                continue
                                        else:
                                            print(f"   ⚠️ No listing date found")
                                            # Go back to PropertyEngine page to try next listing
                                            self.page.go_back()
                                            time.sleep(2)
                                            continue
                                    else:
                                        print(f"   ⚠️ No auction date available for timeframe check")
                                        # Use this listing if no auction date available
                                        source_url = current_url
                                        suitable_listing_found = True
                                        print(f"   🔗 Using PropertyEngine URL as source_url: {source_url}")
                                        break
                                else:
                                    print(f"   ❌ Auction names are the same, trying next listing")
                                    # Go back to PropertyEngine page to try next listing
                                    self.page.go_back()
                                    time.sleep(2)
                                    continue
                            else:
                                print(f"   ⚠️ No auction name to compare, using this listing")
                                source_url = current_url
                                suitable_listing_found = True
                                print(f"   🔗 Using PropertyEngine URL as source_url: {source_url}")
                                break
                        else:
                            if not suitable_listing_found:
                                print(f"   ⚠️ No suitable listing found")
                            else:
                                print(f"   ✅ Suitable listing found and source_url set")
                    else:
                        print(f"   ⚠️ No view listing links found in timeline")
                        source_url = propertyengine_current_url  # Use PropertyEngine URL
                else:
                    print(f"   ⚠️ No 'property sold for xxx' found in timeline")
                    print(f"   🔍 Checking all view listing links within 12 months...")
                    
                    # Look for all view listing links in the timeline
                    all_view_listing_links = timeline_section.query_selector_all('a:has-text("view listing")')
                    if not all_view_listing_links:
                        all_view_listing_links = timeline_section.query_selector_all('a[href^="/property/"]')
                    
                    if all_view_listing_links:
                        print(f"   ✅ Found {len(all_view_listing_links)} view listing links to check")
                        
                        # Initialize source_url to PropertyEngine URL
                        source_url = propertyengine_current_url
                        suitable_listing_found = False
                        
                        # Check each view listing link
                        for i, listing_link in enumerate(all_view_listing_links):
                            print(f"   🔍 Checking view listing link {i+1}/{len(all_view_listing_links)}...")
                            
                            # Get the link text and href
                            link_text = listing_link.text_content().strip()
                            link_href = listing_link.get_attribute('href')
                            print(f"   📄 Link text: '{link_text}'")
                            print(f"   🔗 Link href: '{link_href}'")
                            
                            # Click the link to go to the listing page
                            print(f"   🖱️ Clicking on view listing link...")
                            listing_link.click()
                            time.sleep(3)
                            
                            # Get the current URL
                            current_url = self.page.url
                            print(f"   🔗 Current URL: {current_url}")
                            
                            # Check the auction name on this listing page
                            listing_page_text = self.page.locator("body").text_content()
                            
                            # Look for auction name patterns on the listing page
                            auction_name_found = None
                            auction_name_patterns = [
                                r'Auction\s+House\s+([A-Za-z\s]+)',
                                r'([A-Za-z\s]+)\s+Auction',
                                r'Auctioneer[:\s]*([A-Za-z\s]+)',
                                r'([A-Za-z\s]+)\s+Auctioneers',
                                r'([A-Za-z\s]+)\s+Property\s+Auctions',
                                r'([A-Za-z\s]+)\s+Auction\s+House'
                            ]
                            
                            # First, try to find auction name in the page title
                            page_title = self.page.title()
                            print(f"   📋 Page title: {page_title}")
                            
                            for pattern in auction_name_patterns:
                                match = re.search(pattern, page_title, re.IGNORECASE)
                                if match:
                                    auction_name_found = match.group(1).strip()
                                    print(f"   🏢 Found auction name in title: {auction_name_found}")
                                    break
                            
                            # If not found in title, try the page content
                            if not auction_name_found:
                                for pattern in auction_name_patterns:
                                    match = re.search(pattern, listing_page_text, re.IGNORECASE)
                                    if match:
                                        auction_name_found = match.group(1).strip()
                                        print(f"   🏢 Found auction name on listing: {auction_name_found}")
                                        break
                            
                            # Compare with auction name from our database
                            if auction_name and auction_name_found:
                                print(f"   🏢 Comparing auction names:")
                                print(f"      Database: {auction_name}")
                                print(f"      Listing: {auction_name_found}")
                                
                                # Check if auction names are different
                                if auction_name.lower() != auction_name_found.lower():
                                    print(f"   ✅ Auction names are different")
                                    
                                    # Check if the listing date is within 12 months prior to auction date
                                    if auction_date:
                                        # Try to extract listing date from the timeline text around this link
                                        # Look for date patterns in the timeline
                                        timeline_text = timeline_section.text_content()
                                        date_patterns = [
                                            r'([A-Za-z]{3}\s+[A-Za-z]{3}\s+\d{1,2},?\s+\d{4})',
                                            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                                            r'(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})'
                                        ]
                                        
                                        listing_date_found = None
                                        for pattern in date_patterns:
                                            matches = re.findall(pattern, timeline_text)
                                            if matches:
                                                # Use the most recent date that's before the auction date
                                                for date_str in matches:
                                                    try:
                                                        if ',' in date_str:
                                                            listing_date = datetime.strptime(date_str, "%a %b %d, %Y")
                                                        else:
                                                            listing_date = datetime.strptime(date_str, "%d/%m/%Y")
                                                        
                                                        auction_date_obj = datetime.strptime(auction_date, "%Y-%m-%d")
                                                        
                                                        # Check if listing date is before auction date and within 12 months
                                                        if listing_date < auction_date_obj:
                                                            date_diff = relativedelta(auction_date_obj, listing_date)
                                                            months_diff = date_diff.years * 12 + date_diff.months
                                                            
                                                            if months_diff <= 12:
                                                                listing_date_found = date_str
                                                                print(f"   📅 Found suitable listing date: {listing_date_found} ({months_diff} months before auction)")
                                                                break
                                                    except:
                                                        continue
                                                
                                                if listing_date_found:
                                                    break
                                        
                                        if listing_date_found:
                                            print(f"   ✅ Listing is within 12 months prior to auction")
                                            source_url = current_url
                                            suitable_listing_found = True
                                            print(f"   🔗 Using PropertyEngine URL as source_url: {source_url}")
                                            break
                                        else:
                                            print(f"   ❌ Listing date not within 12-month timeframe")
                                    else:
                                        print(f"   ⚠️ No auction date available for timeframe check")
                                        # Use this listing if no auction date available
                                        source_url = current_url
                                        suitable_listing_found = True
                                        print(f"   🔗 Using PropertyEngine URL as source_url: {source_url}")
                                        break
                                else:
                                    print(f"   ❌ Auction names are the same, trying next listing")
                            else:
                                print(f"   ⚠️ No auction name to compare, trying next listing")
                            
                            # Go back to PropertyEngine page to try next listing
                            self.page.go_back()
                            time.sleep(2)
                        
                        if not suitable_listing_found:
                            print(f"   ⚠️ No suitable listing found within 12 months")
                            print(f"   ⏭️ No usable timeline data, but keeping guide price")
                            # Return guide price even if timeline has no usable data
                            return {
                                'source_url': propertyengine_current_url,  # Use PropertyEngine URL
                                'guide_price': guide_price if guide_price else ''
                            }
                    else:
                        print(f"   ⚠️ No view listing links found in timeline")
                        print(f"   ⏭️ No usable timeline data, but keeping guide price")
                        # Return guide price even if timeline has no usable data
                        return {
                            'source_url': propertyengine_current_url,  # Use PropertyEngine URL
                            'guide_price': guide_price if guide_price else ''
                        }
            else:
                print(f"   ⚠️ No timeline section found")
                print(f"   ⏭️ No timeline data, but keeping guide price")
                source_url = propertyengine_current_url  # Use PropertyEngine URL
            
            if guide_price:
                print(f"   ✅ Successfully extracted guide price: {guide_price}")
                print(f"   🔗 Source URL: {source_url}")
                return {
                    'source_url': source_url,
                    'guide_price': guide_price
                }
            else:
                print(f"   ⚠️ No guide price found in PropertyEngine results")
                return {
                    'source_url': source_url,
                    'guide_price': ''
                }
            
        except Exception as e:
            print(f"❌ Error extracting from PropertyEngine: {e}")
            # Take a screenshot to see what happened
            try:
                self.page.screenshot(path="propertyengine_error.png")
                print("📸 Error screenshot saved: propertyengine_error.png")
            except:
                pass
            return None
    
    # Note: delete_imported_row function removed - now using update_row instead of add+delete approach

    def update_spreadsheet_row(self, row_data, new_data, sheet_name='AUCTIONS_MASTER'):
        """Update existing row in the specified Google Sheet with enriched data"""
        try:
            print(f"📝 Updating existing row with enriched data in {sheet_name}...")
            
            # First, find the row to update
            webapp_url = self.sheets_manager.webapp_url
            shared_token = self.sheets_manager.shared_token
            
            # Read current data to find the row index
            read_payload = {
                'token': shared_token,
                'action': 'read',
                'sheet_id': os.getenv('GOOGLE_SHEETS_ID', '1ONZrugWl0amSFqGLq3_hHmR82Bps-vNxr-25gGk8B9Q')
            }
            
            response = requests.post(webapp_url, json=read_payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if result.get('ok') and result.get('rows'):
                    rows = result.get('rows', [])
                    
                    # Find the target row to update
                    target_row_index = None
                    for i, row in enumerate(rows):
                        # Match by address, lot_number, auction_date, and qa_status
                        if (row.get('address') == row_data.get('address') and
                            row.get('lot_number') == row_data.get('lot_number') and
                            row.get('auction_date') == row_data.get('auction_date') and
                            row.get('qa_status') == 'imported'):
                            
                            target_row_index = i
                            print(f"📋 Found target row at index {i}: {row.get('address', 'N/A')}")
                            break
                    
                    if target_row_index is not None:
                        # Create updated row data with enriched information
                        updated_row_data = row_data.copy()  # Start with exact copy of original data
                        
                        # Only update the fields that are being enriched
                        updated_row_data['source_url'] = new_data.get('source_url', '')
                        updated_row_data['guide_price'] = new_data.get('guide_price', '')
                        updated_row_data['qa_status'] = 'enriched'
                        
                        # Ensure all other fields remain exactly the same as the original
                        # This includes auction_date, purchase_price format, etc.
                        
                        # Update the existing row using the fixed update_row functionality
                        update_payload = {
                            'token': shared_token,
                            'action': 'update_row',
                            'sheet_id': os.getenv('GOOGLE_SHEETS_ID', '1ONZrugWl0amSFqGLq3_hHmR82Bps-vNxr-25gGk8B9Q'),
                            'row_index': target_row_index,
                            'row_data': updated_row_data
                        }
                        
                        update_response = requests.post(webapp_url, json=update_payload, timeout=30)
                        
                        if update_response.status_code == 200:
                            update_result = update_response.json()
                            if update_result.get('ok'):
                                print(f"✅ Successfully updated existing row with enriched data in {sheet_name}!")
                                print(f"📋 Response: {update_result}")
                                return True
                            else:
                                print(f"❌ Failed to update row: {update_result.get('error', 'Unknown error')}")
                                return False
                        else:
                            print(f"❌ HTTP error updating row: {update_response.status_code}")
                            return False
                    else:
                        print(f"⚠️ Could not find target row to update in {sheet_name}")
                        return False
                else:
                    print(f"❌ Could not fetch data from Google Sheet")
                    return False
            else:
                print(f"❌ HTTP error fetching from Google Sheet: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error updating row in spreadsheet: {e}")
            return False
    
    def process_missing_row(self, row_info):
        """Process a single row with missing data"""
        row_data = row_info['data']
        address = row_data.get('address', '')
        auction_date = row_data.get('auction_date', '')
        
        print(f"\n🔄 Processing: {address}")
        print(f"   Auction date: {auction_date}")
        print(f"   Missing guide_price: {row_info['missing_guide_price']}")
        print(f"   Missing source_url: {row_info['missing_source_url']}")
        
        # Google search for property listings (Rightmove first, then Zoopla)
        property_links = self.google_search_property_sites(address)
        
        if not property_links:
            print(f"   ⏭️ No property links found on Rightmove or Zoopla")
            return False
        
        # Try each property link with PropertyEngine
        for i, property_url in enumerate(property_links):
            print(f"   🔍 Trying property link {i+1}/{len(property_links)}")
            
            # First verify the address on the property page
            address_verified = self.verify_property_address(property_url, address)
            
            if not address_verified:
                print(f"   ⏭️ Skipping - address not verified")
                continue
            
            # If address is verified, proceed with PropertyEngine
            result = self.extract_from_propertyengine(property_url, row_data.get('auction_name'), row_data.get('auction_date'))
            
            if result:
                print(f"   ✅ Successfully extracted data from PropertyEngine!")
                
                # Update the spreadsheet
                sheet_name = row_info.get('sheet_name', 'AUCTIONS_MASTER')
                update_success = self.update_spreadsheet_row(row_data, result, sheet_name)
                
                if update_success:
                    print(f"   ✅ Successfully updated spreadsheet")
                    return True
                else:
                    print(f"   ❌ Failed to update spreadsheet")
            elif result is None:
                print(f"   ⏭️ Skipping - PropertyEngine extraction failed completely")
                # Continue to next property link
            else:
                print(f"   ❌ Failed to extract data from PropertyEngine")
            
            # Add delay between attempts
            time.sleep(random.uniform(3, 8))
        
        print(f"   ⏭️ No suitable data found from PropertyEngine")
        return False
    
    def run_workflow(self):
        """Run the complete listing enrichment workflow"""
        print("🚀 Starting Listing Enrichment Workflow (Updated)")
        print("=" * 50)
        
        try:
            # Start browser
            self.start_browser()
            
            # Get rows with missing data
            missing_rows = self.get_missing_data_rows()
            
            if not missing_rows:
                print("🎉 No rows with missing data found!")
                return
            
            print(f"\n📊 Processing {len(missing_rows)} rows with missing data...")
            
            # Process each missing row
            processed_count = 0
            for i, row_info in enumerate(missing_rows):
                print(f"\n{'='*60}")
                print(f"Processing row {i+1}/{len(missing_rows)}")
                print(f"{'='*60}")
                
                success = self.process_missing_row(row_info)
                if success:
                    processed_count += 1
                
                # Add delay between rows
                if i < len(missing_rows) - 1:  # Don't delay after last row
                    delay = random.uniform(10, 20)
                    print(f"⏱️ Waiting {delay:.1f} seconds before next row...")
                    time.sleep(delay)
            
            print(f"\n📊 Workflow Summary:")
            print(f"   ✅ Successfully processed: {processed_count}")
            print(f"   ⏭️ Failed to process: {len(missing_rows) - processed_count}")
            print(f"   📈 Success rate: {processed_count/len(missing_rows)*100:.1f}%")
            
        except Exception as e:
            print(f"❌ Error in workflow: {e}")
        finally:
            self.close_browser()

if __name__ == "__main__":
    workflow = ListingEnrichmentWorkflow()
    workflow.run_workflow() 