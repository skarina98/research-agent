from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import os
import time

def find_auctions(start_date: str, end_date: str, auctioneer_url: str = None, auctioneer_name: str = "Auction House London", page=None):
    auctions = []
    
    # If no page provided, create our own context
    if page is None:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            
            # Check if session file exists, otherwise create context without it
            session_file = "sessions/eig.json"
            if os.path.exists(session_file):
                print("Using existing session file for authentication")
                context = browser.new_context(storage_state=session_file)
            else:
                print("No session file found, creating new context")
                context = browser.new_context()
                
            page = context.new_page()
            
            # Use provided auctioneer URL or default to Auction House London
            target_url = auctioneer_url or "https://www.eigpropertyauctions.co.uk/clients/auctions/results?SelectedAuctioneerId=680"
            page.goto(target_url)
            page.wait_for_timeout(3000)
            
            # Process the page and return results
            return _process_auction_page(page, start_date, end_date, auctioneer_url, auctioneer_name)
    else:
        # Use the provided page
        print(f"Navigating to EIG auction results...")
        # Use provided auctioneer URL or default to Auction House London
        target_url = auctioneer_url or "https://www.eigpropertyauctions.co.uk/clients/auctions/results?SelectedAuctioneerId=680"
        page.goto(target_url)
        page.wait_for_timeout(3000)
        
        # Process the page and return results
        return _process_auction_page(page, start_date, end_date, auctioneer_url, auctioneer_name)

def _process_auction_page(page, start_date, end_date, auctioneer_url, auctioneer_name):
    """Helper function to process auction page content"""
    auctions = []

    print("Page title:", page.title())
    print("Page URL:", page.url)
    
    # Check if we're on a login page
    if "login" in page.title().lower() or "log-in" in page.url.lower():
        print("Redirected to login page. Trying alternative URLs...")
        
        # Try alternative URLs that might be public
        alternative_urls = [
            "https://www.eigpropertyauctions.co.uk/auction-results",
            "https://www.eigpropertyauctions.co.uk/search/auction-results",
            "https://www.eigpropertyauctions.co.uk/auctions/results"
        ]
        
        for alt_url in alternative_urls:
            try:
                print(f"Trying alternative URL: {alt_url}")
                page.goto(alt_url)
                page.wait_for_timeout(3000)
                print(f"Page title: {page.title()}")
                
                if "login" not in page.title().lower():
                    print("Found public page!")
                    break
            except Exception as e:
                print(f"Error with {alt_url}: {e}")
                continue

    # Try different selectors for auction links
    selectors_to_try = [
        "a.catalogue-link",
        "a[href*='auction']",
        ".auction-link",
        "a[href*='catalogue']",
        "a[href*='results']",
        ".auction-result a",
        ".result-item a"
    ]
    
    links = []
    for selector in selectors_to_try:
        try:
            links = page.query_selector_all(selector)
            if links:
                print(f"Found {len(links)} links with selector: {selector}")
                break
        except Exception as e:
            print(f"Selector {selector} failed: {e}")
            continue

    if not links:
        print("No auction links found. Let's see what links are available:")
        all_links = page.query_selector_all("a")
        for i, link in enumerate(all_links[:10]):  # Show first 10 links
            try:
                href = link.get_attribute("href")
                text = link.text_content()
                print(f"Link {i}: {text} -> {href}")
            except:
                pass

    # Debug: Show what auction links we found
    print(f"\nFound {len(links)} auction links. Let's see what they contain:")
    for i, link in enumerate(links[:10]):  # Show first 10 links
        try:
            text = link.text_content().strip()
            href = link.get_attribute("href")
            print(f"Auction link {i}: '{text}' -> {href}")
        except Exception as e:
            print(f"Error reading link {i}: {e}")

    # Let's also look for auction results in different ways
    print("\nLooking for auction results in different ways...")
    
    # Try to find auction result containers
    result_selectors = [
        ".auction-result",
        ".auction-item",
        ".result-item",
        "[class*='auction']",
        "[class*='result']",
        ".lot",
        ".property",
        "tr",  # Table rows might contain auction data
        ".row",  # Bootstrap rows
        "[class*='catalogue']"
    ]
    
    for selector in result_selectors:
        try:
            results = page.query_selector_all(selector)
            if results:
                print(f"Found {len(results)} elements with selector: {selector}")
                # Show first few results
                for i, result in enumerate(results[:3]):
                    try:
                        text = result.text_content()
                        print(f"  Result {i}: {text[:100]}...")
                    except:
                        pass
        except Exception as e:
            print(f"Selector {selector} failed: {e}")

        # Look for any text that might contain auction information
        try:
            page_text = page.locator("body").text_content()
            if "Auction House London" in page_text:
                print("\nFound 'Auction House London' in page text")
                # Find the context around this text
                lines = page_text.split('\n')
                for i, line in enumerate(lines):
                    if "Auction House London" in line:
                        print(f"Line {i}: {line.strip()}")
                        # Show surrounding lines
                        for j in range(max(0, i-2), min(len(lines), i+3)):
                            if j != i:
                                print(f"  Line {j}: {lines[j].strip()}")
                        break
            else:
                print("\n'Auction House London' not found in page text")
        except Exception as e:
            print(f"Error getting page text: {e}")

        # Try to parse auction data from the page content
        try:
            # Look for table data or structured content
            tables = page.query_selector_all("table")
            print(f"Found {len(tables)} tables on the page")
            
            for i, table in enumerate(tables):
                try:
                    rows = table.query_selector_all("tr")
                    print(f"Table {i} has {len(rows)} rows")
                    
                    # Skip header row and process data rows
                    for j, row in enumerate(rows[1:], 1):  # Start from index 1 to skip header
                        try:
                            cells = row.query_selector_all("td, th")
                            if len(cells) >= 6:  # Expecting Date, Venue, Lots Offered, Lots Sold, Percent Sold, Total Raised
                                date_cell = cells[0].text_content().strip()
                                venue_cell = cells[1].text_content().strip()
                                lots_offered_cell = cells[2].text_content().strip()
                                lots_sold_cell = cells[3].text_content().strip()
                                percent_sold_cell = cells[4].text_content().strip()
                                total_raised_cell = cells[5].text_content().strip()
                                
                                print(f"  Row {j}: {date_cell} | {venue_cell} | {lots_offered_cell} | {lots_sold_cell} | {percent_sold_cell} | {total_raised_cell}")
                                
                                # Try to parse the date
                                try:
                                    # Handle different date formats
                                    if "/" in date_cell:
                                        auction_date = datetime.strptime(date_cell, "%d/%m/%Y")
                                    else:
                                        auction_date = datetime.strptime(date_cell, "%d %B %Y")
                                    
                                    # Check if auction date is in the past (not future)
                                    today = datetime.now()
                                    if auction_date > today:
                                        # Skip future auctions
                                        continue
                                    
                                    # Check if date is in the provided range
                                    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
                                    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
                                    
                                    if start_date_obj <= auction_date <= end_date_obj:
                                        # Try to get the detail URL from the date cell
                                        date_link = row.query_selector("a")
                                        detail_url = None
                                        if date_link:
                                            href = date_link.get_attribute("href")
                                            if href:
                                                if href.startswith("/"):
                                                    detail_url = "https://www.eigpropertyauctions.co.uk" + href
                                                else:
                                                    detail_url = href
                                        
                                        auctions.append({
                                            "name": auctioneer_name,  # Use dynamic auction name
                                            "date": auction_date.strftime("%Y-%m-%d"),
                                            "venue": venue_cell,
                                            "lots_offered": lots_offered_cell,
                                            "lots_sold": lots_sold_cell,
                                            "percent_sold": percent_sold_cell,
                                            "total_raised": total_raised_cell,
                                            "source_url": page.url,
                                            "detail_url": detail_url
                                        })
                                        print(f"  ✅ Added auction for {auction_date.strftime('%Y-%m-%d')} with detail URL: {detail_url}")
                                    else:
                                        # Date is outside the provided range
                                        if auction_date < start_date_obj:
                                            print(f"  ⏭️ Skipped auction {auction_date.strftime('%Y-%m-%d')} - before start date ({start_date})")
                                        elif auction_date > end_date_obj:
                                            print(f"  ⏭️ Skipped auction {auction_date.strftime('%Y-%m-%d')} - after end date ({end_date})")
                                            
                                except Exception as e:
                                    print(f"  ❌ Error parsing date '{date_cell}': {e}")
                                    continue
                                    
                        except Exception as e:
                            print(f"Error processing row {j}: {e}")
                            
                except Exception as e:
                    print(f"Error processing table {i}: {e}")
                    
        except Exception as e:
            print(f"Error looking for tables: {e}")

        for link in links:
            try:
                text = link.text_content()
                if text and "Auction House London" in text:
                    url = link.get_attribute("href")
                    date_text = text.split(" - ")[-1]
                    try:
                        auction_date = datetime.strptime(date_text, "%d %B %Y")
                        if datetime.strptime(start_date, "%Y-%m-%d") <= auction_date <= datetime.strptime(end_date, "%Y-%m-%d"):
                            auctions.append({
                                "name": text,
                                "url": "https://www.eigpropertyauctions.co.uk" + url,
                                "date": auction_date.strftime("%Y-%m-%d")
                            })
                    except Exception as e:
                        print(f"Error parsing date '{date_text}': {e}")
                        continue
            except Exception as e:
                print(f"Error processing link: {e}")
                continue

    print(f"Found {len(auctions)} auctions in date range")
    return auctions


def parse_event_days(event_url: str, auction_name: str = "", auction_date: str = "", page=None):
    lots = []
    
    # If no page provided, create our own context
    if page is None:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            
            # Check if session file exists, otherwise create context without it
            session_file = "sessions/eig.json"
            if os.path.exists(session_file):
                context = browser.new_context(storage_state=session_file)
            else:
                context = browser.new_context()
                
            page = context.new_page()
            
            # Navigate to the auction details page
            print(f"Navigating to auction details: {event_url}")
            page.goto(event_url)
            page.wait_for_timeout(3000)
            
            # Process the auction and return results
            return _process_auction_lots(page, event_url, auction_name, auction_date)
    else:
        # Use the provided page
        print(f"Navigating to auction details: {event_url}")
        page.goto(event_url)
        page.wait_for_timeout(3000)
        
        # Process the auction and return results
        return _process_auction_lots(page, event_url, auction_name, auction_date)

def _process_auction_lots(page, event_url, auction_name, auction_date):
    """Helper function to process auction lots"""
    lots = []
    
    # First, extract the auction results table to get price_bought data
    print("Extracting auction results table...")
    auction_results = extract_auction_results_table(page)
    print(f"Extracted auction results: {auction_results}")
    print(f"Debug: auction_results type: {type(auction_results)}")
    if isinstance(auction_results, dict):
        print(f"Debug: auction_results keys: {list(auction_results.keys())}")
    elif isinstance(auction_results, list):
        print(f"Debug: auction_results length: {len(auction_results)}")
        print(f"Debug: first few auction URLs: {auction_results[:3]}")
    
    print(f"Page title: {page.title()}")
    print(f"Page URL: {page.url}")
    
    # Use provided auction metadata or extract from page
    if not auction_name:
        # Try to extract auction name from page title and content
        try:
            page_title = page.title()
            page_content = page.locator("body").text_content()
            
            print(f"  Debug: Page title: '{page_title}'")
            print(f"  Debug: Page content preview: '{page_content[:200]}...'")
            
            # Check for SDL in various forms
            if any(sdl_indicator in page_title.upper() or sdl_indicator in page_content.upper() 
                   for sdl_indicator in ["SDL", "SDL PROPERTY", "SDL AUCTIONS"]):
                auction_name = "SDL Property Auctions"
            elif any(ah_indicator in page_title.upper() or ah_indicator in page_content.upper() 
                    for ah_indicator in ["AUCTION HOUSE", "AUCTION HOUSE LONDON"]):
                auction_name = "Auction House London"
            elif any(mchugh_indicator in page_title.upper() or mchugh_indicator in page_content.upper() 
                    for mchugh_indicator in ["MCHUGH", "MCHUGH & CO"]):
                auction_name = "McHugh & Co"
            elif any(bonde_indicator in page_title.upper() or bonde_indicator in page_content.upper() 
                    for bonde_indicator in ["BONDE", "BONDE WOLFE"]):
                auction_name = "Bonde Wolfe"
            elif any(ahsw_indicator in page_title.upper() or ahsw_indicator in page_content.upper() 
                    for ahsw_indicator in ["AUCTION HOUSE SOUTH WEST", "AH SOUTH WEST"]):
                auction_name = "Auction House South West"
            elif any(savills_indicator in page_title.upper() or savills_indicator in page_content.upper() 
                    for savills_indicator in ["SAVILLS", "SAVILLS AUCTIONS"]):
                auction_name = "Savills"
            else:
                auction_name = "Unknown Auctioneer"
        except Exception as e:
            print(f"  Error extracting auction name: {e}")
            auction_name = "Unknown Auctioneer"
    
    if not auction_date:
        # Try to extract date from page if not provided
        try:
            date_elements = page.query_selector_all(".auction-date, .date, [class*='date'], .event-date")
            for date_elem in date_elements:
                text = date_elem.text_content().strip()
                if text and any(char.isdigit() for char in text):
                    auction_date = text
                    break
            
            # If still no date, try to extract from page content
            if not auction_date:
                page_text = page.locator("body").text_content()
                import re
                date_patterns = [
                    r'\d{1,2}/\d{1,2}/\d{4}',
                    r'\d{1,2}\s+\w+\s+\d{4}',
                    r'\d{4}-\d{2}-\d{2}'
                ]
                
                for pattern in date_patterns:
                    match = re.search(pattern, page_text)
                    if match:
                        auction_date = match.group(0)
                        break
        except Exception as e:
            print(f"Error extracting auction date: {e}")
    
    print(f"  Using auction name: '{auction_name}'")
    print(f"  Using auction date: '{auction_date}'")
    
    # Look for lot URLs - these are the individual property listings
    print("Looking for lot URLs...")
    lot_urls = []
    
    # Find all links that contain '/lot/' in their href
    lot_links = page.query_selector_all("a[href*='/lot/']")
    print(f"Found {len(lot_links)} lot links")
    
    for link in lot_links:
        try:
            href = link.get_attribute("href")
            if href and "/lot/" in href:
                # Make sure it's a full URL
                if href.startswith("/"):
                    href = "https://www.eigpropertyauctions.co.uk" + href
                lot_urls.append(href)
        except Exception as e:
            print(f"Error extracting lot URL: {e}")
            continue
    
    print(f"Extracted {len(lot_urls)} lot URLs")
    
    # Process each lot URL to get property data
    for i, lot_url in enumerate(lot_urls):  # Process ALL lots
        try:
            print(f"Processing lot {i+1}/{len(lot_urls)}: {lot_url}")
            
            # Navigate to the lot page with better error handling
            lot_page = page.context.new_page()
            try:
                lot_page.goto(lot_url, wait_until="networkidle", timeout=30000)
                lot_page.wait_for_timeout(2000)
            except Exception as e:
                print(f"    ⚠️ Error navigating to lot page: {e}")
                lot_page.close()
                continue
            
            # Extract lot data - pass the auction results for price_bought lookup
            lot_data = extract_lot_data_from_page(lot_page, i + 1, auction_results)
            
            # Always add the lot data, even if property prices lookup failed
            if lot_data:
                # Add auction metadata
                lot_data['auction_name'] = auction_name
                lot_data['auction_date'] = auction_date
                lot_data['source_url'] = ''  # Empty until PropertyEngine enrichment
                lot_data['lot_url'] = lot_url  # Store the individual lot URL
                
                lots.append(lot_data)
                
                if i < 5:  # Show first 5 lots for debugging
                    print(f"  ✅ Lot {i+1}: {lot_data.get('address', 'No address')} - {lot_data.get('purchase_price', 'No price')}")

            else:
                # If extract_lot_data_from_page returns None, create basic lot data
                print(f"  ⚠️ Lot {i+1}: extract_lot_data_from_page returned None, creating basic data")
                
                # Create basic lot data without property prices
                basic_lot_data = {
                    'address': f"Unknown Address - Lot {i + 1}",
                    'purchase_price': '',
                    'sale_date': '',
                    'lot_number': str(i + 1),
                    'auction_sale': '',
                    'postcode': '',
                    'source_url': '',  # Empty until PropertyEngine enrichment
                    'lot_url': lot_url,  # Store the individual lot URL
                    'auction_name': auction_name,
                    'auction_date': auction_date,
                    'property_prices_status': 'extraction_failed',
                    'property_prices_postcode': '',
                    'property_prices_sale_date': '',
                    'property_prices_sale_price': '',
                    'searchland_status': 'pending'
                }
                
                lots.append(basic_lot_data)
                print(f"  📝 Lot {i+1}: Created basic data due to extraction failure")
            
            lot_page.close()
            
            # Add delay between lots to avoid rate limiting
            import time
            import random
            delay = random.uniform(1, 3)
            print(f"    ⏱️ Waiting {delay:.1f} seconds before next lot...")
            time.sleep(delay)
            
        except Exception as e:
            print(f"Error processing lot {i+1}: {e}")
            continue
    
    print(f"Successfully extracted {len(lots)} lots from auction")
    return lots

def extract_auction_results_table(page):
    """
    Extract auction URLs from the recent auctions listing page.
    Returns a list of auction URLs to process.
    """
    auction_urls = []
    
    try:
        # Look for tables with auction listings
        tables = page.query_selector_all("table")
        print(f"    🔍 Found {len(tables)} tables on the auction page")
        for i, table in enumerate(tables):
            print(f"    📋 Processing table {i+1}/{len(tables)}")
            # Check if this table has auction data
            headers = table.query_selector_all("th, td")
            
            # Find the "Lots" column (this indicates it's an auction listing)
            lots_column_index = -1
            date_column_index = -1
            
            # Find relevant columns
            print(f"    📋 Table {i+1} headers: {[h.text_content().strip() for h in headers[:5]]}...")
            for j, header in enumerate(headers):
                header_text = header.text_content().strip().lower()
                if "lots" in header_text:
                    lots_column_index = j
                    print(f"    ✅ Found 'Lots' column at index {j}")
                elif "date" in header_text:
                    date_column_index = j
                    print(f"    ✅ Found 'Date' column at index {j}")
            
            if lots_column_index >= 0:
                # Extract auction URLs from each row
                rows = table.query_selector_all("tr")
                for row in rows:
                    cells = row.query_selector_all("td")
                    if len(cells) > lots_column_index:
                        # Look for auction links in this row
                        auction_links = row.query_selector_all("a[href*='auction']")
                        for link in auction_links:
                            try:
                                href = link.get_attribute("href")
                                if href and "/auction" in href:
                                    # Make sure it's a full URL
                                    if href.startswith("/"):
                                        href = "https://www.eigpropertyauctions.co.uk" + href
                                    auction_urls.append(href)
                                    print(f"    📋 Found auction URL: {href}")
                            except Exception as e:
                                print(f"    ⚠️ Error extracting auction URL: {e}")
                                continue
        
        print(f"    ✅ Extracted {len(auction_urls)} auction URLs from table")
        return auction_urls
        
    except Exception as e:
        print(f"    ⚠️ Error extracting auction URLs table: {e}")
        return []


def lookup_property_in_prices_page(lot_page, address):
    """
    Navigate to English House Prices website and search for the given address.
    If found, extract postcode, sale date, and sale price.
    
    Args:
        page: Playwright page object
        address: Address to search for
        
    Returns:
        Dict with property data if found, None if not found
    """
    try:
        print(f"    🔍 Looking up address in English House Prices: {address}")
        
        # Extract postcode from address (last part)
        import re
        postcode_match = re.search(r'([A-Z]{1,2}\d{1,2}\s?\d[A-Z]{2})$', address, re.IGNORECASE)
        if not postcode_match:
            print(f"    ❌ Could not extract postcode from address: {address}")
            return None
        
        postcode = postcode_match.group(1).upper()
        # Format postcode properly (add space if missing)
        if len(postcode) == 6:  # e.g., "CT93EJ"
            postcode = postcode[:3] + " " + postcode[3:]  # "CT9 3EJ"
        elif len(postcode) == 7 and postcode[3] != " ":  # e.g., "WD180ES"
            postcode = postcode[:4] + " " + postcode[4:]  # "WD18 0ES"
        
        print(f"    📮 Using postcode: {postcode}")
        
        # Navigate to English House Prices with the postcode
        import urllib.parse
        encoded_postcode = urllib.parse.quote(postcode)
        property_prices_url = f"https://www.englishhouseprices.com/results.aspx?postcode={encoded_postcode}"
        
        # Add random delay to avoid rate limiting (2-5 seconds)
        import random
        import time
        delay = random.uniform(2, 5)
        print(f"    ⏱️ Waiting {delay:.1f} seconds to avoid rate limiting...")
        time.sleep(delay)
        
        print(f"    🌐 Navigating to: {property_prices_url}")
        
        # Create a separate page for property prices lookup to avoid affecting the lot page
        prices_page = lot_page.context.new_page()
        
        # Set realistic user agent and headers
        prices_page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Navigate with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                prices_page.goto(property_prices_url, wait_until="networkidle", timeout=30000)
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    retry_delay = (attempt + 1) * 5  # Exponential backoff: 5s, 10s, 15s
                    print(f"    ⚠️ Navigation failed (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s: {e}")
                    time.sleep(retry_delay)
                else:
                    print(f"    ❌ Navigation failed after {max_retries} attempts: {e}")
                    prices_page.close()
                    return None
        
        # Check if page loaded successfully
        page_title = prices_page.title()
        if "Azure WAF" in page_title or "Access Denied" in page_title:
            print(f"    ❌ Blocked by WAF/Access Denied: {page_title}")
            # Wait longer and try again
            print(f"    ⏱️ Waiting 30 seconds before next request...")
            time.sleep(30)
            return None
        
        if "EHP" not in page_title and "house prices" not in page_title.lower():
            print(f"    ❌ Page title doesn't match expected: {page_title}")
            return None
        
        print(f"    ✅ Page loaded: {page_title}")
        
        # Look for the address in the results table
        # The table has columns: Address, Postcode, Type, Tenure, New Build, Sale Date, Sale Price
        page_text = prices_page.locator("body").text_content()
        
        # Normalize the address for comparison (remove extra spaces, make lowercase)
        normalized_address = re.sub(r'\s+', ' ', address.strip()).lower()
        
        # Debug: Show some addresses from the page to understand the format
        print(f"    🔍 Page contains {len(page_text)} characters")
        
        # Look for table rows to see what addresses are available
        table_rows = prices_page.query_selector_all("table tr, .table tr")
        print(f"    📋 Found {len(table_rows)} table rows")
        
        # Show first few addresses from the page
        address_lines = []
        for row in table_rows[:5]:  # Show first 5 rows
            try:
                row_text = row.text_content().strip()
                if row_text and len(row_text) > 20:  # Skip header rows
                    address_lines.append(row_text[:100])
            except:
                continue
        
        if address_lines:
            print(f"    📋 Sample addresses from page:")
            for i, line in enumerate(address_lines):
                print(f"      {i+1}. {line}")
        
        # Try to find the exact address match
        print(f"    🔍 Looking for exact address: {address}")
        
        # First, let's see what addresses are actually on the page
        table_rows = prices_page.query_selector_all("table tr")
        print(f"    📋 Found {len(table_rows)} table rows")
        
        # Look through each row for an exact match
        exact_match = None
        for row in table_rows:
            try:
                row_text = row.text_content().strip()
                if row_text and len(row_text) > 20:  # Skip header rows
                    # Extract the address part (first column)
                    address_cell = row.query_selector("td")
                    if address_cell:
                        cell_text = address_cell.text_content().strip()
                        print(f"    📋 Checking: {cell_text}")
                        
                        # Compare with our target address
                        if cell_text.lower() == address.lower():
                            exact_match = row
                            print(f"    ✅ EXACT MATCH FOUND: {cell_text}")
                            break
                        elif cell_text.lower().startswith(address.split(',')[0].lower()):
                            # Partial match - street address matches
                            print(f"    🔍 PARTIAL MATCH: {cell_text}")
                            exact_match = row
                            break
            except Exception as e:
                continue
        
        if exact_match:
            # Extract data from the exact match row
            try:
                row_text = exact_match.text_content().strip()
                print(f"    📋 Extracting from row: {row_text[:100]}...")
                
                # Extract sale date and price from the row
                # Pattern: Sale Date | Sale Price (last two columns)
                import re
                
                # Look for date pattern (DD/MM/YYYY)
                date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', row_text)
                sale_date = date_match.group(1) if date_match else ''
                
                # Look for price pattern (£XXX,XXX)
                price_match = re.search(r'£([\d,]+)', row_text)
                sale_price = f"£{price_match.group(1)}" if price_match else ''
                
                print(f"    📅 Sale Date: {sale_date}")
                print(f"    💰 Sale Price: {sale_price}")
                
                # Check if sale date is within 6 months from today
                from datetime import datetime, timedelta
                try:
                    # Parse the sale date (format: DD/MM/YYYY)
                    sale_date_obj = datetime.strptime(sale_date, "%d/%m/%Y")
                    today = datetime.now()
                    six_months_ago = today - timedelta(days=180)  # 6 months = ~180 days
                    
                    if six_months_ago <= sale_date_obj <= today:
                        print(f"    ✅ Sale date {sale_date} is within 6 months - INCLUDING")
                        return {
                            'postcode': postcode,
                            'sale_date': sale_date,
                            'sale_price': sale_price,
                            'found_in_prices': True
                        }
                    else:
                        if sale_date_obj > today:
                            print(f"    ⏭️ Sale date {sale_date} is in the future - SKIPPING")
                        else:
                            print(f"    ⏭️ Sale date {sale_date} is older than 6 months - SKIPPING")
                        return None
                        
                except Exception as e:
                    print(f"    ⚠️ Error parsing sale date {sale_date}: {e}")
                    # If we can't parse the date, skip it to be safe
                    return None
                
            except Exception as e:
                print(f"    ⚠️ Error extracting data from row: {e}")
                return None
        else:
            print(f"    ❌ Address not found in English House Prices results")
            return None
                
    except Exception as e:
        print(f"    ⚠️ Error looking up property in English House Prices: {e}")
        return None
    finally:
        # Always close the prices page
        try:
            prices_page.close()
        except:
            pass

def extract_lot_data_from_page(lot_page, lot_number, auction_results=None):
    """
    Extract lot data from an individual lot page.
    NEW WORKFLOW: Extract basic info, then lookup in property prices page.
    
    Args:
        lot_page: Playwright page object for the lot page
        lot_number: Sequential lot number (fallback)
        
    Returns:
        Dict with lot data or None if extraction failed
    """
    try:
        lot_data = {
            'lot_number': str(lot_number),  # Default to sequential number
            'address': '',
            'auction_sale': '',
            'guide_price': None,  # Allow guide price to be null
            'purchase_price': '',
            'sale_date': '',
            'postcode': '',
            'found_in_prices': False
        }
        
        # Try multiple selectors for each field
        address_selectors = [
            ".lot-address",
            ".address",
            ".property-address",
            "[class*='address']",
            "h1", "h2", "h3", "h4", "h5",
            ".lot-title",
            ".property-title",
            ".lot-description",
            ".property-description"
        ]
        
        # First try to get lot number from auction results table by matching address
        if auction_results:
            # Extract address first to match with auction results
            address_found = False
            for selector in address_selectors:
                try:
                    if selector.startswith("text="):
                        # Text-based selector
                        text_value = selector[5:]  # Remove "text=" prefix
                        elements = lot_page.query_selector_all(f"text={text_value}")
                        for elem in elements:
                            parent = elem.evaluate("el => el.parentElement")
                            if parent:
                                siblings = parent.query_selector_all("*")
                                for sibling in siblings:
                                    text = sibling.text_content().strip()
                                    if text and len(text) > 10:  # Likely an address
                                        lot_data['address'] = text
                                        address_found = True
                                        break
                                if address_found:
                                    break
                    else:
                        # CSS selector
                        addr_elem = lot_page.query_selector(selector)
                        if addr_elem:
                            text = addr_elem.text_content().strip()
                            if text and len(text) > 10:  # Likely an address
                                lot_data['address'] = text
                                address_found = True
                                break
                except:
                    continue
                
                if address_found:
                    break
            
            # Now try to match the address with auction results to get the correct lot number
            if lot_data['address']:
                address_to_find = lot_data['address'].lower()
                for lot_num, result_text in auction_results.items():
                    # Simple matching - look for key words from address in result text
                    address_words = [word for word in address_to_find.split() if len(word) > 3]
                    if any(word in result_text.lower() for word in address_words[:3]):
                        lot_data['lot_number'] = lot_num
                        print(f"    📍 Matched lot number {lot_num} from auction results for address: {lot_data['address'][:50]}...")
                        break
        
        # If we couldn't match from auction results, extract from page
        if not auction_results or lot_data['lot_number'] == str(lot_number):
            lot_number_selectors = [
                "text=Lot Number",
                "text=lot number",
                "text=LOT NUMBER",
                ".lot-number",
                "[class*='lot-number']",
                ".lot-no",
                "[class*='lot-no']",
                ".lot",
                "[class*='lot']",
                "h1", "h2", "h3", "h4", "h5"  # Check headers for lot numbers
            ]
        
        actual_lot_number_found = False
        for selector in lot_number_selectors:
            try:
                if selector.startswith("text="):
                    # Text-based selector - look for "Lot Number" and get the next element
                    text_value = selector[5:]  # Remove "text=" prefix
                    elements = lot_page.query_selector_all(f"text={text_value}")
                    for elem in elements:
                        # Get the parent element and look for the lot number in siblings or children
                        parent = elem.evaluate("el => el.parentElement")
                        if parent:
                            # Look for the lot number in the same container
                            siblings = parent.query_selector_all("*")
                            for sibling in siblings:
                                text = sibling.text_content().strip()
                                # Check for alphanumeric lot numbers (like "156A", "157B")
                                lot_match = re.search(r'(\d+[A-Za-z]*)', text)
                                if lot_match and len(text) <= 6:  # Reasonable lot number length
                                    lot_data['lot_number'] = lot_match.group(1)
                                    actual_lot_number_found = True
                                    break
                        if actual_lot_number_found:
                            break
                else:
                    # CSS selector
                    lot_elem = lot_page.query_selector(selector)
                    if lot_elem:
                        text = lot_elem.text_content().strip()
                        if text and text.isdigit() and len(text) <= 4:
                            lot_data['lot_number'] = text
                            actual_lot_number_found = True
                            break
            except:
                continue
            
            if actual_lot_number_found:
                break
        
        # If we couldn't find the lot number with selectors, try searching the page text
        if not actual_lot_number_found:
            try:
                page_text = lot_page.locator("body").text_content()
                import re
                # Look for patterns like "Lot Number 162" or "Lot 162"
                lot_patterns = [
                    r'Lot Number\s+(\d+)',
                    r'Lot\s+(\d+)',
                    r'LOT NUMBER\s+(\d+)',
                    r'LOT\s+(\d+)',
                    r'lot\s+(\d+)',
                    r'lot number\s+(\d+)'
                ]
                
                for pattern in lot_patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        lot_data['lot_number'] = match.group(1)
                        actual_lot_number_found = True
                        print(f"    📍 Found lot number from text: {lot_data['lot_number']}")
                        break
                
                # If still not found, try to extract from URL
                if not actual_lot_number_found:
                    url = lot_page.url
                    # Look for lot number in URL
                    lot_match = re.search(r'/lot/([^/?]+)', url)
                    if lot_match:
                        # Try to extract a number from the URL
                        url_part = lot_match.group(1)
                        number_match = re.search(r'(\d+)', url_part)
                        if number_match:
                            lot_data['lot_number'] = number_match.group(1)
                            actual_lot_number_found = True
                            print(f"    📍 Found lot number from URL: {lot_data['lot_number']}")
            except Exception as e:
                print(f"    ⚠️ Error extracting lot number from text: {e}")
                pass
        
        # Extract address with better error handling
        address_found = False
        for selector in address_selectors:
            try:
                if selector.startswith("text="):
                    # Text-based selector
                    text_value = selector[5:]  # Remove "text=" prefix
                    elements = lot_page.query_selector_all(f"text={text_value}")
                    for elem in elements:
                        try:
                            address = elem.text_content().strip()
                            if address and len(address) > 5:
                                lot_data['address'] = address
                                # Extract postcode from address using regex pattern
                                import re
                                postcode_match = re.search(r'([A-Z]{1,2}\d{1,2}\s?\d[A-Z]{2})$', address, re.IGNORECASE)
                                if postcode_match:
                                    lot_data['postcode'] = postcode_match.group(1).upper()
                                else:
                                    # Fallback: use last part of address
                                    parts = address.split()
                                    if len(parts) >= 2:
                                        lot_data['postcode'] = parts[-1]
                                address_found = True
                                break
                        except Exception as e:
                            print(f"    ⚠️ Error extracting text from element: {e}")
                            continue
                else:
                    # CSS selector
                    address_elem = lot_page.query_selector(selector)
                    if address_elem:
                        try:
                            address = address_elem.text_content().strip()
                            if address and len(address) > 5:
                                lot_data['address'] = address
                                # Extract postcode from address using regex pattern
                                import re
                                postcode_match = re.search(r'([A-Z]{1,2}\d{1,2}\s?\d[A-Z]{2})$', address, re.IGNORECASE)
                                if postcode_match:
                                    lot_data['postcode'] = postcode_match.group(1).upper()
                                else:
                                    # Fallback: use last part of address
                                    parts = address.split()
                                    if len(parts) >= 2:
                                        lot_data['postcode'] = parts[-1]
                                address_found = True
                                break
                        except Exception as e:
                            print(f"    ⚠️ Error extracting text from {selector}: {e}")
                            continue
            except Exception as e:
                print(f"    ⚠️ Error with selector {selector}: {e}")
                continue
            
            if address_found:
                break
        
        # If no address found with selectors, try to get it from page title or URL
        if not address_found:
            try:
                # Try to get address from page title
                page_title = lot_page.title()
                if page_title and "lot" in page_title.lower():
                    # Extract address from title if possible
                    title_parts = page_title.split(" - ")
                    if len(title_parts) > 1:
                        potential_address = title_parts[-1].strip()
                        if len(potential_address) > 5:
                            lot_data['address'] = potential_address
                            address_found = True
                            print(f"    📍 Using address from page title: {potential_address}")
            except Exception as e:
                print(f"    ⚠️ Error extracting address from page title: {e}")
        
        # If still no address, try to extract from URL or page content
        if not address_found:
            try:
                # Try to get any text that looks like an address from the page
                page_text = lot_page.locator("body").text_content()
                if page_text:
                    # Look for patterns that might be addresses
                    import re
                    # Look for postcode patterns
                    postcode_match = re.search(r'([A-Z]{1,2}\d{1,2}\s?\d[A-Z]{2})', page_text, re.IGNORECASE)
                    if postcode_match:
                        postcode = postcode_match.group(1)
                        # Try to find the address around the postcode
                        postcode_index = page_text.find(postcode)
                        if postcode_index > 0:
                            # Get text before postcode (likely the address)
                            before_postcode = page_text[max(0, postcode_index-100):postcode_index].strip()
                            # Find the last line that might be the address
                            lines = before_postcode.split('\n')
                            for line in reversed(lines):
                                line = line.strip()
                                if line and len(line) > 10 and ',' in line:
                                    lot_data['address'] = f"{line}, {postcode}"
                                    lot_data['postcode'] = postcode
                                    address_found = True
                                    print(f"    📍 Using address from page content: {lot_data['address']}")
                                    break
            except Exception as e:
                print(f"    ⚠️ Error extracting address from page content: {e}")
        
        # If still no address found, create a generic one
        if not address_found:
            # Check if we're on a login page
            try:
                page_title = lot_page.title()
                if 'login' in page_title.lower() or 'sign in' in page_title.lower():
                    print(f"    ⚠️ Session expired - on login page")
                    return None
            except:
                pass
            
            lot_data['address'] = f"Unknown Address - Lot {lot_data['lot_number']}"
            print(f"    ⚠️ No address found, using generic: {lot_data['address']}")
        
        # Extract auction sale from the individual lot page
        # Look for auction sale information in h2/h3 elements with text-end class
        auction_sale_selectors = [
            ".text-end h2",  # Primary selector - h2 inside text-end div
            ".text-end h3",  # Secondary selector - h3 inside text-end div
            ".text-end",  # Any element with text-end class
            "h2", "h3",  # Fallback to any h2 or h3 headers
            ".auction-result",
            ".lot-result", 
            ".sale-status",
            ".auction-status",
            "[class*='result']",
            "[class*='sale']",
            "[class*='status']",
            ".price",
            ".sold-price",
            ".auction-price"
        ]
        
        auction_sale_found = False
        for selector in auction_sale_selectors:
            try:
                # Look for elements that might contain auction sale information
                elements = lot_page.query_selector_all(selector)
                for element in elements:
                    text = element.text_content().strip()
                    if text and len(text) > 3:  # Reasonable length for auction sale info
                        # Check if this looks like auction sale information
                        # Look for price patterns or status keywords
                        import re
                        
                        # Check for price patterns
                        price_patterns = [
                            r'Sold\s+for\s+£([\d,]+(?:,\d{3})*)',  # "Sold for £X"
                            r'Sold\s+at\s+£([\d,]+(?:,\d{3})*)',   # "Sold at £X"
                            r'£([\d,]+(?:,\d{3})*)',               # Standard price format
                        ]
                        
                        # Check for status keywords
                        status_keywords = ['sold', 'unsold', 'withdrawn', 'reserved', 'auctioneer']
                        
                        # If it contains price patterns or status keywords, it's likely auction sale info
                        is_price = any(re.search(pattern, text, re.IGNORECASE) for pattern in price_patterns)
                        is_status = any(keyword in text.lower() for keyword in status_keywords)
                        
                        if is_price or is_status:
                            lot_data['auction_sale'] = text
                            auction_sale_found = True
                            print(f"    📍 Captured auction sale from {selector}: {lot_data['auction_sale']}")
                            break
                
                if auction_sale_found:
                    break
                    
            except Exception as e:
                print(f"    ⚠️ Error processing selector {selector}: {e}")
                continue
        
        # If no auction sale found with selectors, try to extract from page text
        if not auction_sale_found:
            try:
                page_text = lot_page.locator("body").text_content()
                if page_text:
                    import re
                    # Look for price patterns first, then capture any text as-is
                    price_patterns = [
                        r'Sold\s+for\s+£([\d,]+(?:,\d{3})*)',  # "Sold for £306,000"
                        r'Sold\s+at\s+£([\d,]+(?:,\d{3})*)',   # "Sold at £X"
                        r'Price\s+£([\d,]+(?:,\d{3})*)',       # "Price £X"
                        r'£([\d,]+(?:,\d{3})*)',               # Standard price format like £185,000
                        r'Guide.*?£([\d,]+(?:,\d{3})*)',
                        r'Estimate.*?£([\d,]+(?:,\d{3})*)',
                    ]
                    
                    price_found = False
                    for pattern in price_patterns:
                        match = re.search(pattern, page_text, re.IGNORECASE)
                        if match:
                            lot_data['auction_sale'] = f"£{match.group(1)}"
                            price_bought_found = True
                            print(f"    📍 Found auction sale from page text: {lot_data['auction_sale']}")
                            price_found = True
                            break
                    
                    # If no price found, look for auction-related text to capture as-is
                    if not price_found:
                        auction_keywords = ['sold', 'withdrawn', 'reserved', 'unsold', 'passed', 'cancelled', 'postponed', 'adjourned', 'auction', 'lot']
                        for keyword in auction_keywords:
                            # Look for any text containing these keywords
                            keyword_pattern = rf'([^.]*{keyword}[^.]*)'
                            matches = re.findall(keyword_pattern, page_text, re.IGNORECASE)
                            for match in matches:
                                match_text = match.strip()
                                if len(match_text) > 5 and len(match_text) < 100:  # Reasonable length
                                    lot_data['auction_sale'] = match_text
                                    price_bought_found = True
                                    print(f"    📍 Captured auction-related text: {lot_data['auction_sale']}")
                                    break
                            if price_bought_found:
                                break
            except Exception as e:
                print(f"    ⚠️ Error extracting price bought from page text: {e}")
        
        # Guide price will be found later by PropertyEngine enrichment workflow
        lot_data['guide_price'] = None  # Set to None initially, will be populated by enrichment
        
        # Check if we're on a login page (session expired)
        if lot_data['address'] and ('login' in lot_data['address'].lower() or 'sign in' in lot_data['address'].lower()):
            print(f"    ⚠️ Session expired - redirected to login page")
            return None
        
        # NEW WORKFLOW: If we have an address, lookup in property prices page
        if lot_data['address']:
            # Lookup the address in property prices page
            property_data = lookup_property_in_prices_page(lot_page, lot_data['address'])
            
            if property_data and property_data.get('found_in_prices'):
                # Update lot data with property prices data
                lot_data['postcode'] = property_data.get('postcode', lot_data['postcode'])
                lot_data['sale_date'] = property_data.get('sale_date', '')
                lot_data['purchase_price'] = property_data.get('sale_price', '')  # Actual purchase price from property prices database
                
                # Keep the original price_bought from the auction listing
                # The sold_price from property prices database is separate
                # Only set to "Sold prior to auction" if the auction listing itself shows that status
                
                lot_data['property_prices_status'] = 'found'
                lot_data['property_prices_postcode'] = property_data.get('postcode', '')
                lot_data['property_prices_sale_date'] = property_data.get('sale_date', '')
                lot_data['property_prices_sale_price'] = property_data.get('sale_price', '')
                print(f"  ✅ Lot {lot_data['lot_number']}: {lot_data['address']} - Auction Sale: {lot_data['auction_sale']}, Purchase Price: {lot_data['purchase_price']} (found in property prices)")
                
                # Check street history immediately after finding property prices
                print(f"  🔍 Checking street history for property with prices...")
                transaction_info = check_street_history_for_auction_properties(lot_data, lot_page) if lot_page else {
                    'transaction_type': 'estate agent to auction',
                    'eig_street_history_url': ''
                }
                
                # Add transaction info to lot data
                lot_data['transaction_type'] = transaction_info.get('transaction_type', 'estate agent to auction')
                lot_data['eig_street_history_url'] = transaction_info.get('eig_street_history_url', '')
                print(f"  📋 Transaction type: {lot_data['transaction_type']}")
                print(f"  🔗 EIG Street History URL: {lot_data['eig_street_history_url']}")
            else:
                # Address not found in property prices - still return the lot data
                lot_data['property_prices_status'] = 'not_found'
                lot_data['property_prices_postcode'] = ''
                lot_data['property_prices_sale_date'] = ''
                lot_data['property_prices_sale_price'] = ''
                print(f"  📝 Lot {lot_data['lot_number']}: {lot_data['address']} - Auction Sale: {lot_data['auction_sale']}, Purchase Price: Not found")
                
                # Check street history even if no property prices found (for auction sale data)
                if lot_data.get('auction_sale') and lot_data['auction_sale'].strip():
                    print(f"  🔍 Checking street history for auction sale data...")
                    transaction_info = check_street_history_for_auction_properties(lot_data, lot_page) if lot_page else {
                        'transaction_type': 'estate agent to auction',
                        'eig_street_history_url': ''
                    }
                    
                    # Add transaction info to lot data
                    lot_data['transaction_type'] = transaction_info.get('transaction_type', 'estate agent to auction')
                    lot_data['eig_street_history_url'] = transaction_info.get('eig_street_history_url', '')
                    print(f"  📋 Transaction type: {lot_data['transaction_type']}")
                    print(f"  🔗 EIG Street History URL: {lot_data['eig_street_history_url']}")
                else:
                    # No auction sale data, set default transaction type
                    lot_data['transaction_type'] = 'estate agent to auction'
                    lot_data['eig_street_history_url'] = ''
                    
                    # Calculate profit even if no property prices found (if we have auction_sale)
                    if lot_data.get('auction_sale') and lot_data['auction_sale'].strip():
                        print(f"  🔍 Calculating profit for auction sale without property prices...")
                        # Profit calculation will be done in the import section
        
        # Always return the lot data, regardless of property prices status
        return lot_data
        
    except Exception as e:
        print(f"Error extracting lot data from page: {e}")
        return None

def check_street_history_for_auction_properties(lot_data, page):
    """
    Check street history for auction properties to determine transaction type.
    Returns a dictionary with 'transaction_type' and 'eig_street_history_url'.
    """
    address = lot_data.get('address', '')
    auction_name = lot_data.get('auction_name', '')
    auction_date = lot_data.get('auction_date', '')
    
    if not address or not page:
        return {
            'transaction_type': 'estate agent to auction',
            'eig_street_history_url': ''
        }
    
    print(f"   🔍 Checking street history for: {address}")
    
    # Look for the "View Street history" link on the lot page
    print(f"   🔍 Looking for 'View Street history' link on the lot page...")
    
    try:
        # Wait for the page to load properly
        page.wait_for_timeout(2000)
        
        # Try different methods to find the street history link
        street_history_link = None
        
        # Look for all links and find the one with street history text
        all_links = page.query_selector_all('a')
        street_history_link = None
        
        print(f"   📋 Checking {len(all_links)} links for street history...")
        
        for i, link in enumerate(all_links):
            try:
                link_text = link.inner_text().strip()
                
                # Debug: show links that contain "street" or "history"
                if link_text and ('street' in link_text.lower() or 'history' in link_text.lower()):
                    print(f"   🔍 Link {i+1}: '{link_text}'")
                
                if link_text and ('street history' in link_text.lower() or 
                                'view street history' in link_text.lower() or
                                'view the auction history' in link_text.lower() or
                                'auction history' in link_text.lower() or
                                'street' in link_text.lower() and 'history' in link_text.lower()):
                    street_history_link = link
                    print(f"   🎯 Found street history link: '{link_text}'")
                    break
            except Exception as e:
                continue
        
        # If we found the street history link, click on it
        if street_history_link:
            print(f"   🎯 Clicking on street history link...")
            try:
                # Try to get the href attribute first
                href = None
                try:
                    href = street_history_link.get_attribute('href')
                except:
                    pass
                
                if href:
                    print(f"   🔗 Found href: {href}")
                    # Construct full URL if needed
                    if href.startswith('/'):
                        full_url = f"https://www.eigpropertyauctions.co.uk{href}"
                    else:
                        full_url = href
                    
                    print(f"   🔗 Navigating directly to: {full_url}")
                    page.goto(full_url, wait_until="domcontentloaded")
                    time.sleep(3)
                else:
                    # Fallback to clicking
                    print(f"   🖱️ Clicking on link element...")
                    street_history_link.click()
                    time.sleep(3)
                
                # Check if we're on a street history page
                new_html_content = page.content()
                if "street" in new_html_content.lower() and "history" in new_html_content.lower():
                    print(f"   ✅ Successfully navigated to street history page!")
                    
                    # Get the street history URL
                    street_history_url = page.url
                    
                    # Parse the street history page to find relevant auction entries
                    print(f"   🔍 Parsing street history page for relevant auction entries...")
                    
                    # Parse the street history page to find entries with same address, within 6 months, but not same date
                    relevant_entries = parse_street_history_page(page, address, auction_name, auction_date)
                    
                    # For auction opportunity logic, we need to check if the current auction is within 3 months from today
                    from datetime import datetime, timedelta
                    today = datetime.now()
                    current_auction_date = datetime.strptime(auction_date, "%Y-%m-%d") if auction_date else None
                    
                    # Check if current auction is within 3 months for auction opportunity logic
                    is_within_3_months = False
                    if current_auction_date:
                        days_diff = (today - current_auction_date).days
                        is_within_3_months = days_diff <= 90  # 3 months = 90 days
                        print(f"   📅 Current auction date: {auction_date}, Days from today: {days_diff}, Within 3 months: {is_within_3_months}")
                    
                    print(f"   📊 Found {len(relevant_entries)} relevant auction entries for this address")
                    
                    # Check if current listing is withdrawn/unsold
                    current_auction_sale = lot_data.get('auction_sale', '').lower()
                    is_current_withdrawn_unsold = any(pattern in current_auction_sale for pattern in ['withdrawn', 'unsold', 'passed', 'no bids', 'no sale', 'not sold', 'failed to sell'])
                    
                    if relevant_entries:
                        # Check if we have auction opportunity case
                        # Only apply auction opportunity logic if current auction is within 3 months from today
                        if is_current_withdrawn_unsold and is_within_3_months:
                            print(f"   🎯 Checking for auction opportunity (current auction within 3 months, withdrawn/unsold)")
                            # Check if all relevant entries are also unsold/withdrawn (no sold entries)
                            all_unsold_withdrawn = True
                            has_sold_entries = False
                            
                            for entry in relevant_entries:
                                if entry.get('has_sold_indicator'):
                                    has_sold_entries = True
                                    all_unsold_withdrawn = False
                                    break
                            
                            if all_unsold_withdrawn and not has_sold_entries:
                                print(f"   🎯 TRANSACTION TYPE: auction opportunity (current listing withdrawn/unsold within 3 months, all relevant entries also unsold/withdrawn)")
                                transaction_type = 'auction opportunity'
                            else:
                                print(f"   🎯 TRANSACTION TYPE: auction to auction (found {len(relevant_entries)} relevant entries, some sold)")
                                transaction_type = 'auction to auction'
                        elif is_current_withdrawn_unsold and not is_within_3_months:
                            print(f"   ⏭️ Current auction is withdrawn/unsold but older than 3 months - not an auction opportunity")
                            print(f"   🎯 TRANSACTION TYPE: auction to auction (found {len(relevant_entries)} relevant entries, but current auction too old for opportunity)")
                            transaction_type = 'auction to auction'
                        else:
                            print(f"   🎯 TRANSACTION TYPE: auction to auction (found {len(relevant_entries)} relevant entries)")
                            transaction_type = 'auction to auction'
                        
                        # Only include the street history URL if we found relevant entries
                        return {
                            'transaction_type': transaction_type,
                            'eig_street_history_url': street_history_url
                        }
                    else:
                        print(f"   🏠 TRANSACTION TYPE: estate agent to auction (no relevant entries found)")
                        transaction_type = 'estate agent to auction'
                        # Don't include the street history URL if no relevant entries found
                        return {
                            'transaction_type': transaction_type,
                            'eig_street_history_url': ''
                        }
                    
                    # Go back to the lot page
                    page.go_back()
                    time.sleep(2)
                else:
                    print(f"   ⚠️ Not sure if we're on a street history page")
                    # Go back to the lot page
                    page.go_back()
                    time.sleep(2)
                    
            except Exception as e:
                print(f"   ❌ Error clicking on street history link: {e}")
                # Try to go back to the lot page
                try:
                    page.go_back()
                    time.sleep(2)
                except:
                    pass
        else:
            print(f"   ⚠️ No 'View Street history' link found on the lot page")
            
    except Exception as e:
        print(f"   ❌ Error looking for street history link: {e}")
    
    # Default return if no street history found or error occurred
    return {
        'transaction_type': 'estate agent to auction',
        'eig_street_history_url': ''
    }

def parse_street_history_page(page, target_address, current_auction_name, current_auction_date):
    """
    Parse the street history page to find auction entries for the target address.
    
    Args:
        page: Playwright page object
        target_address: The address we're looking for
        current_auction_name: Current auction name to compare
        current_auction_date: Current auction date to compare
        
    Returns:
        List of auction entries found for this address
    """
    try:
        auction_entries = []
        
        # Look for auction entries on the page - use improved selectors to find actual property listings
        auction_selectors = [
            '.property-item',
            '.auction-item', 
            '.result-item',
            'div[class*="property"]',
            'div[class*="lot"]',
            'div[class*="result"]',
            'div[class*="auction"]',
            'tr',
            'div'
        ]
        
        elements = []
        for selector in auction_selectors:
            elements = page.query_selector_all(selector)
            if elements:
                print(f"   🔍 Found {len(elements)} elements with selector: {selector}")
                
                # Look for elements that contain addresses
                address_elements = []
                for elem in elements:
                    try:
                        text = elem.text_content().strip()
                        if text and any(char.isdigit() for char in text) and len(text) > 20:
                            # Check if it looks like an address (contains numbers and is reasonably long)
                            address_elements.append(elem)
                    except:
                        continue
                
                if address_elements:
                    print(f"   🏠 Found {len(address_elements)} potential address elements")
                    elements = address_elements
                    break
                else:
                    print(f"   ⚠️ No address-like elements found with selector: {selector}")
                    continue
        
        if not elements:
            print(f"   ⚠️ No auction elements found on street history page")
            return []
        
        # Look for elements containing the exact address
        target_address_lower = target_address.lower()
        
        print(f"   🏠 Looking for entries with exact address: {target_address}")
        
        # Process ALL elements to find entries within 6 months
        print(f"   🔍 Processing {len(elements)} elements to find relevant auction entries...")
        
        for i, element in enumerate(elements):
            try:
                element_text = element.text_content().strip()
                
                # Check if this element contains our exact address
                # We want to find entries for the same property address
                if target_address_lower in element_text.lower():
                    
                    print(f"   📄 Found exact address match in element {i+1}/{len(elements)}: {element_text[:100]}...")
                    
                    # Extract auction information from this element
                    auction_info = extract_auction_info_from_element(element_text, current_auction_name, current_auction_date, target_address)
                    
                    if auction_info:
                        auction_entries.append(auction_info)
                        print(f"   ✅ Added auction entry: {auction_info}")
                
            except Exception as e:
                print(f"   ⚠️ Error processing element {i+1}: {e}")
                continue
        
        return auction_entries
        
    except Exception as e:
        print(f"   ❌ Error parsing street history page: {e}")
        return []

def extract_street_name(address):
    """
    Extract the street name from a full address.
    
    Args:
        address: Full address string
        
    Returns:
        Street name string
    """
    import re
    
    # Remove postcode first
    address_no_postcode = re.sub(r'\s+[A-Z]{1,2}\d{1,2}\s*\d[A-Z]{2}$', '', address)
    
    # Common patterns for UK addresses
    # Look for patterns like "123 Street Name" or "Street Name"
    patterns = [
        r'\d+\s+([A-Za-z\s]+?)(?:,\s*[A-Za-z\s]+)?$',  # "123 Street Name, City"
        r'([A-Za-z\s]+?)(?:,\s*[A-Za-z\s]+)?$',  # "Street Name, City"
        r'\d+\s+([A-Za-z\s]+?)(?:\s+[A-Za-z\s]+)?$',  # "123 Street Name City"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, address_no_postcode)
        if match:
            street_name = match.group(1).strip()
            # Clean up the street name
            street_name = re.sub(r'\s+', ' ', street_name)  # Remove extra spaces
            # Remove trailing commas and common words
            street_name = re.sub(r',\s*$', '', street_name)
            street_name = re.sub(r'\s+(Street|Lane|Road|Avenue|Drive|Close|Way|Place|Court|Terrace|Crescent|Grove|Hill|Park|Square|Mews|Gardens|Walk|Row|Yard|Alley|Bridge|Circus|Corner|Cross|End|Field|Gate|Green|Haven|Heath|Heights|Lodge|Meadow|Mount|Orchard|Parade|Passage|Path|Pond|Rise|Row|Spring|Strand|Vale|View|Villas|Wharf|Wood)\s*$', '', street_name, flags=re.IGNORECASE)
            return street_name
    
    # Fallback: try to extract just the street part
    parts = address_no_postcode.split(',')
    if len(parts) >= 2:
        # Take the first part which usually contains the street
        street_part = parts[0].strip()
        # Remove house number if present
        street_part = re.sub(r'^\d+\s+', '', street_part)
        return street_part
    
    # Final fallback: return the address without postcode
    return address_no_postcode

def extract_auction_info_from_element(element_text, current_auction_name, current_auction_date, target_address):
    """
    Extract auction information from an element's text.
    
    Args:
        element_text: Text content of the element
        current_auction_name: Current auction name for comparison
        current_auction_date: Current auction date for comparison
        
    Returns:
        Dict with auction information or None if not relevant
    """
    try:
        import re
        from datetime import datetime, timedelta
        
        # Look for auction date patterns
        date_patterns = [
            r'(\d{1,2}/\d{1,2}/\d{4})',  # DD/MM/YYYY
            r'(\d{1,2}-\d{1,2}-\d{4})',  # DD-MM-YYYY
            r'(\d{1,2}\s+[A-Za-z]+\s+\d{4})',  # DD Month YYYY
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\d{1,2}\.\d{1,2}\.\d{4})',  # DD.MM.YYYY
            r'(\d{1,2}/\d{1,2}/\d{2})',  # DD/MM/YY
            r'(\d{1,2}-\d{1,2}-\d{2})',  # DD-MM-YY
            r'(\d{1,2}\.\d{1,2}\.\d{2})',  # DD.MM.YY
            r'(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})',  # DD MMM YYYY (e.g., 15 Jan 2024)
            r'(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})',  # DD MMM YY (e.g., 15 Jan 24)
            r'([A-Za-z]+\s+\d{1,2},?\s+\d{4})',  # Month DD, YYYY (e.g., January 15, 2024)
            r'([A-Za-z]+\s+\d{1,2}\s+\d{4})',  # Month DD YYYY (e.g., January 15 2024)
        ]
        
        auction_date = None
        for pattern in date_patterns:
            match = re.search(pattern, element_text)
            if match:
                date_str = match.group(1)
                print(f"   🔍 DEBUG: Found date pattern '{pattern}' with value '{date_str}'")
                try:
                    # Try different date formats
                    date_formats = [
                        '%d/%m/%Y', '%d-%m-%Y', '%d %B %Y', '%Y-%m-%d', 
                        '%d.%m.%Y', '%d/%m/%y', '%d-%m-%y', '%d.%m.%y',
                        '%d %b %Y', '%d %b %y', '%B %d, %Y', '%B %d %Y'
                    ]
                    
                    for fmt in date_formats:
                        try:
                            auction_date = datetime.strptime(date_str, fmt)
                            print(f"   ✅ DEBUG: Successfully parsed date '{date_str}' with format '{fmt}' -> {auction_date.strftime('%Y-%m-%d')}")
                            break
                        except ValueError:
                            continue
                    else:
                        print(f"   ❌ DEBUG: Could not parse date '{date_str}' with any format")
                        continue  # No valid date format found
                    break  # Date found and parsed successfully
                except Exception as e:
                    print(f"   ❌ DEBUG: Error parsing date '{date_str}': {e}")
                    continue
        
        if not auction_date:
            print(f"   🔍 DEBUG: No auction date found in element text: {element_text[:100]}...")
            return None
        
        # Look for auction name patterns - be more specific to find actual auctioneer names
        auction_name = None
        
        # Look for specific auctioneer names in the text
        auctioneer_names = [
            "SDL Property Auctions",
            "SDL Auctions",
            "Auction House London", 
            "Auction House",
            "McHugh & Co",
            "Mchugh & Co",
            "Bonde Wolfe",
            "Auction House South West",
            "Savills",
            "Yopa",
            "Allsop",
            "Barnard Marcus",
            "Clive Emson",
            "Countrywide",
            "Eddisons",
            "GVA",
            "Hollands",
            "Lambert Smith Hampton",
            "Pugh",
            "Strettons",
            "Wilsons",
            "Andrews",
            "Bond Wolfe",
            "Cushman & Wakefield",
            "Knight Frank",
            "CBRE",
            "JLL",
            "Colliers",
            "BidX1",
            "iamsold",
            "Modern Method",
            "OpenBrix",
            "Purplebricks",
            "Strike"
        ]
        
        for name in auctioneer_names:
            if name.lower() in element_text.lower():
                auction_name = name
                print(f"   🔍 DEBUG: Found auction name '{auction_name}' in element text")
                break
        
        # If no specific name found, try pattern matching
        if not auction_name:
            print(f"   🔍 DEBUG: No auction name found in element text: {element_text[:100]}...")
            auction_name_patterns = [
                r'by\s+([A-Za-z\s]+)',  # "by Auction House London"
                r'Auctioneer[:\s]*([A-Za-z\s]+)',
                r'([A-Za-z\s]+)\s+Auction',
                r'([A-Za-z\s]+)\s+Auctioneers',
            ]
            
            for pattern in auction_name_patterns:
                match = re.search(pattern, element_text)
                if match:
                    extracted_name = match.group(1).strip()
                    # Only use if it looks like a real auctioneer name
                    if len(extracted_name) > 2 and extracted_name.lower() not in ['by', 'the', 'and', 'co']:
                        auction_name = extracted_name
                        break
        
        # Check if this auction is within 6 months of the current auction
        if current_auction_date:
            try:
                print(f"   🔍 Debug: Current auction date: '{current_auction_date}', Street history entry date: {auction_date.strftime('%Y-%m-%d')}")
                current_date = datetime.strptime(current_auction_date, "%Y-%m-%d")
                date_diff = abs((current_date - auction_date).days)
                
                print(f"   🔍 Debug: Date difference: {date_diff} days")
                
                if date_diff > 180:  # More than 6 months
                    print(f"   ⏭️ Skipping auction from {auction_date.strftime('%Y-%m-%d')} - more than 6 months from current auction date {current_date.strftime('%Y-%m-%d')} (diff: {date_diff} days)")
                    return None
                else:
                    print(f"   ✅ Date within 6 months: {auction_date.strftime('%Y-%m-%d')} vs {current_date.strftime('%Y-%m-%d')} (diff: {date_diff} days)")
                
                # Check if it's the same address with the same date (regardless of auction name)
                # DISREGARD these entries - they don't count for "auction to auction" classification
                if auction_date.date() == current_date.date():
                    print(f"   ⏭️ Disregarding same address with same date: {auction_date.strftime('%Y-%m-%d')}")
                    return None
                
                # Check if this element contains any form of "sold" - only count entries that were actually sold
                sold_patterns = [
                    "sold for",
                    "sold prior",
                    "sold post",
                    "sold at",
                    "sold by",
                    "sold to",
                    "sold -",
                    "sold:",
                    "sold."
                ]
                
                # Check for unsold/withdrawn patterns
                unsold_patterns = [
                    "unsold",
                    "withdrawn",  # Regular "withdrawn" (not "withdrawn prior")
                    "passed",
                    "no bids",
                    "no sale",
                    "not sold",
                    "failed to sell"
                ]
                
                # Check for "withdrawn prior" first (this counts as sold)
                has_sold_indicator = "withdrawn prior" in element_text.lower()
                
                # If not "withdrawn prior", check other sold patterns
                if not has_sold_indicator:
                    sold_patterns_other = [p for p in sold_patterns if p != "withdrawn prior"]
                    has_sold_indicator = any(pattern in element_text.lower() for pattern in sold_patterns_other)
                
                # Check unsold patterns, but exclude "withdrawn prior"
                unsold_patterns_filtered = [p for p in unsold_patterns if p != "withdrawn prior"]
                has_unsold_indicator = any(pattern in element_text.lower() for pattern in unsold_patterns_filtered)
                
                # For auction opportunity logic, we need to track both sold and unsold entries
                if not has_sold_indicator and not has_unsold_indicator:
                    print(f"   ⏭️ Skipping entry - no clear sale/unsold status: {element_text[:100]}...")
                    return None
                
                # Check if this entry is for the same address (exact match or same street)
                target_address_lower = target_address.lower()
                element_text_lower = element_text.lower()
                
                # Extract street name from target address
                target_street = extract_street_name(target_address).lower()
                
                # Check if this element contains the exact address or the same street number and name
                # We want to find entries for the same property address
                exact_match = target_address_lower in element_text_lower
                
                # Also check for street number and name match (ignoring property names)
                # Extract the street part from target address (e.g., "78 Oval Road" from "78 Oval Road, Birmingham, B24 8PP")
                import re
                target_street_part = target_address_lower.split(',')[0].strip()  # "78 oval road"
                
                # Look for the street number and name pattern in the element text
                street_number_name_match = False
                if target_street_part:
                    # Extract number and street name
                    street_match = re.search(r'(\d+)\s+([a-z\s]+)', target_street_part)
                    if street_match:
                        number = street_match.group(1)  # "78"
                        street_name = street_match.group(2).strip()  # "oval road"
                        # Look for this pattern in the element text
                        pattern = rf'\b{number}\s+{re.escape(street_name)}\b'
                        if re.search(pattern, element_text_lower):
                            street_number_name_match = True
                
                if exact_match or street_number_name_match:
                    
                    print(f"   ✅ Counting relevant auction entry: {auction_date.strftime('%Y-%m-%d')} by {auction_name or 'Unknown'}")
                    print(f"   📍 Address match found in: {element_text[:100]}...")
                    
                    return {
                        'auction_date': auction_date.strftime('%Y-%m-%d'),
                        'auction_name': auction_name or 'Unknown',
                        'element_text': element_text[:200],  # First 200 chars for reference
                        'address_match': True,
                        'has_sold_indicator': has_sold_indicator,
                        'has_unsold_indicator': has_unsold_indicator
                    }
                else:
                    print(f"   ⏭️ Skipping entry - address doesn't match: {element_text[:50]}...")
                    return None
                
            except Exception as e:
                print(f"   ⚠️ Error comparing dates: {e}")
        
        return None
        
    except Exception as e:
        print(f"   ❌ Error extracting auction info: {e}")
        return None

def get_processed_auctions(sheets_manager):
    """
    Get list of auctions that have already been processed
    by checking the Google Sheet for existing auction dates
    
    Args:
        sheets_manager: PropertyDataManager instance
        
    Returns:
        Set of auction dates that have been processed
    """
    processed_auctions = set()
    
    try:
        # Get existing data from the sheet
        existing_data = sheets_manager.property_data
        
        # Extract auction dates from existing data
        for property_data in existing_data:
            auction_date = property_data.get('auction_date', '')
            auction_name = property_data.get('auction_name', '')
            if auction_date and auction_name:
                # Create a unique key for each auction
                auction_key = f"{auction_name}_{auction_date}"
                processed_auctions.add(auction_key)
        
        # Also try to read from Google Sheet directly if available
        try:
            import requests
            webapp_url = sheets_manager.webapp_url
            shared_token = sheets_manager.shared_token
            
            if webapp_url and shared_token:
                payload = {
                    'token': shared_token,
                    'action': 'read',
                    'sheet_id': os.getenv('GOOGLE_SHEETS_ID', '1ONZrugWl0amSFqGLq3_hHmR82Bps-vNxr-25gGk8B9Q')
                }
                
                response = requests.post(webapp_url, json=payload, timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    if result.get('ok') and result.get('rows'):
                        for row in result.get('rows', []):
                            auction_date = row.get('auction_date', '')
                            auction_name = row.get('auction_name', '')
                            if auction_date and auction_name:
                                auction_key = f"{auction_name}_{auction_date}"
                                processed_auctions.add(auction_key)
                        print(f"📊 Also found {len(result.get('rows', []))} rows from Google Sheet")
        except Exception as e:
            print(f"⚠️ Could not read from Google Sheet directly: {e}")
        
        print(f"📊 Found {len(processed_auctions)} already processed auctions")
        
        # Show some examples of processed auctions
        if processed_auctions:
            print(f"📋 Examples of processed auctions:")
            for i, auction_key in enumerate(list(processed_auctions)[:5]):
                print(f"   - {auction_key}")
            if len(processed_auctions) > 5:
                print(f"   ... and {len(processed_auctions) - 5} more")
        
        return processed_auctions
        
    except Exception as e:
        print(f"⚠️ Error getting processed auctions: {e}")
        return set()

def process_auctions_to_sheets(start_date: str, end_date: str, page=None, auctioneer_url: str = None, auctioneer_name: str = "Auction House London"):
    """
    Main workflow function that:
    1. Finds auctions in the date range
    2. Checks which auctions have already been processed
    3. Extracts property listings from new auctions only
    4. Imports each lot immediately to sheets after processing
    5. Provides real-time progress tracking
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        page: Playwright page object for browser automation
        auctioneer_url: Optional URL for specific auctioneer results page
        
    Returns:
        Dict with processing results
    """
    from sheets_webapp import PropertyDataManagerWebApp as PropertyDataManager
    
    print(f"=== PROCESSING AUCTIONS FROM {start_date} TO {end_date} ===")
    
    # Initialize sheets manager
    sheets_manager = PropertyDataManager()
    
    # Step 1: Get already processed auctions
    print("\n1. Checking already processed auctions...")
    processed_auctions = get_processed_auctions(sheets_manager)
    
    # Step 2: Find auctions
    print("\n2. Finding auctions...")
    auctions = find_auctions(start_date, end_date, auctioneer_url, auctioneer_name, page)
    print(f"Found {len(auctions)} auctions")
    
    if not auctions:
        return {
            "status": "no_auctions",
            "message": "No auctions found in the specified date range"
        }
    
    # Step 3: Filter out already processed auctions
    new_auctions = []
    skipped_auctions = []
    
    for auction in auctions:
        auction_key = f"{auction.get('name', 'Unknown')}_{auction.get('date', '')}"
        if auction_key in processed_auctions:
            skipped_auctions.append(auction)
            print(f"   ⏭️ Skipping already processed auction: {auction.get('name', 'Unknown')} on {auction.get('date', 'Unknown')}")
        else:
            new_auctions.append(auction)
    
    print(f"\n📊 Auction Summary:")
    print(f"   ✅ New auctions to process: {len(new_auctions)}")
    print(f"   ⏭️ Already processed (skipped): {len(skipped_auctions)}")
    
    if not new_auctions:
        print("🎉 All auctions in this date range have already been processed!")
        return {
            "status": "already_processed",
            "message": "All auctions in the specified date range have already been processed",
            "total_imported": 0,
            "total_skipped": 0,
            "total_lots_found": 0
        }
    
    # Step 4: Process each new auction and import lots immediately
    total_imported = 0
    total_skipped = 0
    total_lots_found = 0
    
    for i, auction in enumerate(new_auctions):
        print(f"\n2.{i+1}. Processing auction {i+1}/{len(new_auctions)}: {auction.get('name', 'Unknown')}")
        
        if auction.get('detail_url'):
            try:
                lots = parse_event_days(
                    auction['detail_url'], 
                    auction.get('name', 'Auction House London'),
                    auction.get('date', ''),
                    page
                )
                total_lots_found += len(lots)
                
                print(f"   Found {len(lots)} lots in this auction")
                
                # Process each lot individually and import immediately when match found
                for j, lot in enumerate(lots):
                    print(f"   Processing lot {j+1}/{len(lots)}: {lot.get('address', 'No address')}")
                    print(f"   Lot property_prices_status: {lot.get('property_prices_status', 'NOT SET')}")
                    print(f"   🔍 DEBUG: lot auction_sale: '{lot.get('auction_sale', 'NOT SET')}'")
                    
                    # Check if lot should be imported based on criteria
                    has_property_prices = lot.get('property_prices_status') == 'found'
                    has_relevant_auction_entries = lot.get('transaction_type') == 'auction to auction'
                    
                    print(f"   🔍 DEBUG: has_property_prices={has_property_prices}")
                    print(f"   🔍 DEBUG: has_relevant_auction_entries={has_relevant_auction_entries}")
                    print(f"   🔍 DEBUG: property_prices_status={lot.get('property_prices_status')}")
                    print(f"   🔍 DEBUG: transaction_type={lot.get('transaction_type')}")
                    
                    # Import if we have property prices OR relevant auction entries (same address, within 6 months, but not same date)
                    if has_property_prices or has_relevant_auction_entries:
                        if has_property_prices:
                            print(f"   📍 PROPERTY PRICES FOUND! Importing lot {j+1}...")
                        if has_relevant_auction_entries:
                            print(f"   🎯 RELEVANT AUCTION ENTRIES FOUND! Importing lot {j+1}...")
                        print(f"   📍 Guide price will be found by PropertyEngine enrichment")
                        
                        # Street history already checked during lot processing
                        transaction_info = {
                            'transaction_type': lot.get('transaction_type', 'estate agent to auction'),
                            'eig_street_history_url': lot.get('eig_street_history_url', '')
                        }
                        
                        # Calculate profit: auction_sale - purchase_price
                        profit = ''
                        try:
                            auction_sale_str = lot.get('auction_sale', '').strip()
                            purchase_price_str = lot.get('purchase_price', '').strip()
                            
                            if auction_sale_str and purchase_price_str:
                                # Extract numeric values from strings (remove £, commas, etc.)
                                import re
                                
                                # Extract auction sale amount from text like "Sold for £240,000" or "Withdrawn prior"
                                auction_sale_amount = None
                                auction_sale_patterns = [
                                    r'sold\s+for\s*[£$]?([\d,]+)',  # "Sold for £240,000"
                                    r'sold\s+at\s*[£$]?([\d,]+)',   # "Sold at £240,000"
                                    r'sold\s*[£$]?([\d,]+)',        # "Sold £240,000"
                                    r'[£$]([\d,]+)',               # Just the amount with currency symbol
                                    r'([\d,]+)',                   # Any numeric amount
                                ]
                                
                                for pattern in auction_sale_patterns:
                                    match = re.search(pattern, auction_sale_str.lower())
                                    if match:
                                        auction_sale_amount = match.group(1).replace(',', '')
                                        break
                                
                                # Extract purchase price amount
                                purchase_price_amount = None
                                purchase_price_patterns = [
                                    r'[£$]([\d,]+)',               # Just the amount with currency symbol
                                    r'([\d,]+)',                   # Any numeric amount
                                ]
                                
                                for pattern in purchase_price_patterns:
                                    match = re.search(pattern, purchase_price_str.lower())
                                    if match:
                                        purchase_price_amount = match.group(1).replace(',', '')
                                        break
                                
                                if auction_sale_amount and purchase_price_amount:
                                    auction_sale_val = float(auction_sale_amount)
                                    purchase_price_val = float(purchase_price_amount)
                                    profit_val = auction_sale_val - purchase_price_val
                                    profit = f"£{profit_val:,.0f}"
                                    print(f"   💰 Calculated profit: {profit} (Sale: £{auction_sale_val:,.0f} - Purchase: £{purchase_price_val:,.0f})")
                                    print(f"   📝 From auction_sale: '{auction_sale_str}' → £{auction_sale_val:,.0f}")
                                    print(f"   📝 From purchase_price: '{purchase_price_str}' → £{purchase_price_val:,.0f}")
                                else:
                                    if not auction_sale_amount:
                                        print(f"   ⚠️ Could not extract auction sale amount from: '{auction_sale_str}'")
                                    if not purchase_price_amount:
                                        print(f"   ⚠️ Could not extract purchase price amount from: '{purchase_price_str}'")
                            else:
                                if not auction_sale_str:
                                    print(f"   ⚠️ Missing auction_sale for profit calculation")
                                if not purchase_price_str:
                                    print(f"   ⚠️ Missing purchase_price for profit calculation")
                        except Exception as e:
                            print(f"   ⚠️ Error calculating profit: {e}")
                        
                        property_data = {
                            'auction_name': auction.get('name', ''),
                            'auction_date': auction.get('date', ''),
                            'address': lot.get('address', ''),
                            'auction_sale': lot.get('auction_sale', ''),  # Auction sale price from auction listing
                            'profit': profit,  # Calculated profit: auction_sale - purchase_price
                            'guide_price': lot.get('guide_price', ''),  # Guide price will be found by PropertyEngine enrichment
                            'lot_number': lot.get('lot_number', ''),
                            'postcode': lot.get('postcode', ''),
                            'purchase_price': lot.get('purchase_price', ''),
                            'sold_date': lot.get('sale_date', ''),  # Sale date from property prices
                            'auction_url': lot.get('lot_url', ''),  # Individual lot URL
                            # Additional metadata fields
                            'source_url': '',  # Empty until PropertyEngine enrichment
                            'property_prices_status': 'found',
                            'property_prices_postcode': lot.get('property_prices_postcode', ''),
                            'property_prices_sale_date': lot.get('property_prices_sale_date', ''),
                            'property_prices_sale_price': lot.get('property_prices_sale_price', ''),
                            'searchland_status': 'pending',
                            # New fields for transaction type and EIG street history
                            'transaction_type': transaction_info.get('transaction_type', 'estate agent to auction'),
                            'eig_street_history_url': transaction_info.get('eig_street_history_url', '')
                        }
                        

                        
                        # Ensure all required fields have at least empty string values
                        for field in ['auction_name', 'auction_date', 'address', 'auction_sale', 'lot_number', 'postcode', 'purchase_price', 'sold_date', 'auction_url']:
                            if field not in property_data or property_data[field] is None:
                                property_data[field] = ''
                        
                        # Import this lot immediately to sheets
                        try:
                            print(f"   📤 Sending to Google Sheet - Guide Price: {property_data.get('guide_price', 'NOT FOUND')}")
                            result = sheets_manager.process_property_data(property_data)
                            if result.get('status') == 'success':
                                total_imported += 1
                                print(f"   ✅ Lot {j+1} imported successfully with property prices data")
                            else:
                                total_skipped += 1
                                print(f"   ⏭️ Lot {j+1} import failed: {result.get('message', 'Unknown error')}")
                        except Exception as e:
                            total_skipped += 1
                            print(f"   ❌ Error importing lot {j+1}: {e}")
                    else:
                        print(f"   ⏭️ Lot {j+1} skipped - no property prices AND no relevant auction entries found")
                        total_skipped += 1
                    
                    # Add small delay between lots
                    import time
                    import random
                    delay = random.uniform(0.5, 1.5)
                    time.sleep(delay)
                
                print(f"   ✅ Completed auction {i+1}: {len(lots)} lots processed")
                
                # Add delay between auctions to avoid rate limiting
                import time
                import random
                delay = random.uniform(3, 8)
                print(f"   ⏱️ Waiting {delay:.1f} seconds before next auction...")
                time.sleep(delay)
                
            except Exception as e:
                print(f"   Error processing auction {i+1}: {e}")
                continue
        else:
            print(f"   No detail URL available for auction {i+1}")
    
    # Summary
    print(f"\n📊 Final Summary:")
    print(f"   ✅ Total imported: {total_imported}")
    print(f"   ⏭️ Total skipped: {total_skipped}")
    print(f"   🎯 Auctions processed: {len(new_auctions)}")
    print(f"   ⏭️ Auctions skipped (already processed): {len(skipped_auctions)}")
    print(f"   📈 Success rate: {total_imported/(total_imported+total_skipped)*100:.1f}%" if (total_imported+total_skipped) > 0 else "   📈 Success rate: 0%")
    
    return {
        "status": "success",
        "total_imported": total_imported,
        "total_skipped": total_skipped,
        "total_lots_found": total_lots_found,
        "auctions_processed": len(new_auctions),
        "auctions_skipped": len(skipped_auctions),
        "message": f"Imported {total_imported} properties, processed {len(new_auctions)} auctions, skipped {len(skipped_auctions)} already processed auctions"
    }

def scrape_auctions_without_import(start_date, end_date):
    """
    Scrape auctions from EIG and import them immediately after each auction.
    This prevents the workflow from getting stuck in a long scraping phase.
    """
    print(f"🔍 Scraping EIG auctions from {start_date} to {end_date}")
    print("=" * 60)
    
    # Use the existing find_auctions function which handles its own browser
    try:
        # Find auctions in the specified date range
        auctions = find_auctions(start_date, end_date)
        
        if not auctions:
            print("❌ No auctions found in the specified date range")
            return []
        
        print(f"✅ Found {len(auctions)} auctions to process")
        
        all_lots = []
        
        # Process each auction and import immediately
        for i, auction in enumerate(auctions):
            print(f"\n📊 Processing auction {i+1}/{len(auctions)}")
            print(f"   Auction: {auction.get('name', 'Unknown')}")
            print(f"   Date: {auction.get('date', 'Unknown')}")
            print(f"   URL: {auction.get('detail_url', 'No URL')}")
            
            if auction.get('detail_url'):
                try:
                    lots = parse_event_days(
                        auction['detail_url'], 
                        auction.get('name', 'Auction House London'),
                        auction.get('date', '')
                    )
                    
                    print(f"   Found {len(lots)} lots in this auction")
                    
                    # Add auction metadata to each lot
                    for lot in lots:
                        lot['auction_name'] = auction.get('name', '')
                        lot['auction_date'] = auction.get('date', '')
                        lot['auction_detail_url'] = auction.get('detail_url', '')

                    
                    # Import these lots immediately
                    print(f"   📤 Importing {len(lots)} lots immediately...")
                    imported_count = 0
                    for lot in lots:
                        try:
                            # Import the lot using the existing import logic
                            success = process_lot_to_sheets(lot)
                            if success:
                                imported_count += 1
                        except Exception as e:
                            print(f"      ❌ Error importing lot: {e}")
                            continue
                    
                    print(f"   ✅ Imported {imported_count}/{len(lots)} lots from auction {i+1}")
                    all_lots.extend(lots)
                    
                    # Add delay between auctions to avoid rate limiting
                    import time
                    import random
                    delay = random.uniform(3, 8)
                    print(f"   ⏱️ Waiting {delay:.1f} seconds before next auction...")
                    time.sleep(delay)
                    
                except Exception as e:
                    print(f"   Error processing auction {i+1}: {e}")
                    continue
            else:
                print(f"   No detail URL available for auction {i+1}")
        
        print(f"\n📊 Scraping and importing completed: {len(all_lots)} total lots processed")
        return all_lots
        
    except Exception as e:
        print(f"❌ Error in scrape_auctions_without_import: {e}")
        return []

def process_lot_to_sheets(lot):
    """
    Process a single lot and import it to the appropriate sheet based on date.
    This function determines whether to import to AUCTION_MASTER or POTENTIAL_TRADES.
    """
    try:
        from main_workflow_controller import MainWorkflowController
        controller = MainWorkflowController()
        

        
        # Get auction date for categorization
        auction_date = lot.get('auction_date', '')
        if not auction_date:
            print(f"      ⏭️ Skipping lot - no auction date: {lot.get('address', 'Unknown')}")
            return False
        
        # Convert auction_date to proper format if needed
        try:
            if 'T' in auction_date:
                auction_date = auction_date.split('T')[0]
            elif len(auction_date) > 10:
                auction_date = auction_date[:10]
        except:
            print(f"      ⏭️ Skipping lot - invalid auction date: {auction_date}")
            return False
        
        # Categorize auction
        category = controller.categorize_auction_by_date(auction_date)
        
        if category == 'NEWER':
            print(f"      📋 Categorizing as NEWER auction (0-3 months)")
            success = controller.process_newer_lot(lot)
        elif category == 'OLDER':
            print(f"      📋 Categorizing as OLDER auction (3-12 months)")
            success = controller.process_older_lot(lot)
        else:
            print(f"      ⏭️ Skipping lot - unknown category: {category}")
            return False
        
        if success:
            print(f"      ✅ Successfully imported to {category} category")
        else:
            print(f"      ❌ Failed to import to {category} category")
        
        return success
        
    except Exception as e:
        print(f"      ❌ Error in process_lot_to_sheets: {e}")
        return False
