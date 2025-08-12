from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import os

def find_auctions(start_date: str, end_date: str):
    auctions = []
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

        print(f"Navigating directly to Auction House London results...")
        # Try the direct URL for Auction House London (ID: 680)
        page.goto("https://www.eigpropertyauctions.co.uk/clients/auctions/results?SelectedAuctioneerId=680")
        page.wait_for_timeout(3000)

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
                                    
                                    # Check if date is in range (3-12 months ago)
                                    three_months_ago = today - timedelta(days=90)
                                    twelve_months_ago = today - timedelta(days=365)
                                    
                                    if twelve_months_ago <= auction_date <= three_months_ago:
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
                                            "name": "Auction House London",  # Add auction name
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
                                        # Date is outside our 3-12 month range
                                        if auction_date < twelve_months_ago:
                                            print(f"  ⏭️ Skipped auction {auction_date.strftime('%Y-%m-%d')} - too old (>12 months)")
                                        elif auction_date > three_months_ago:
                                            print(f"  ⏭️ Skipped auction {auction_date.strftime('%Y-%m-%d')} - too recent (<3 months)")
                                            
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

        context.close()
        browser.close()
    
    print(f"Found {len(auctions)} auctions in date range")
    return auctions


def parse_event_days(event_url: str, auction_name: str = "", auction_date: str = ""):
    lots = []
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
        
        # First, extract the auction results table to get price_bought data
        print("Extracting auction results table...")
        auction_results = extract_auction_results_table(page)
        print(f"Extracted auction results: {auction_results}")
        print(f"Debug: auction_results keys: {list(auction_results.keys())}")
        
        print(f"Page title: {page.title()}")
        print(f"Page URL: {page.url}")
        
        # Use provided auction metadata or extract from page
        if not auction_name:
            auction_name = "Auction House London"  # Default fallback
        
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
                lot_page = context.new_page()
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
                    lot_data['source_url'] = lot_url
                    
                    lots.append(lot_data)
                    
                    if i < 5:  # Show first 5 lots for debugging
                        print(f"  ✅ Lot {i+1}: {lot_data.get('address', 'No address')} - {lot_data.get('sold_price', 'No price')}")
                else:
                    # If extract_lot_data_from_page returns None, create basic lot data
                    print(f"  ⚠️ Lot {i+1}: extract_lot_data_from_page returned None, creating basic data")
                    
                    # Create basic lot data without property prices
                    basic_lot_data = {
                        'address': f"Unknown Address - Lot {i + 1}",
                        'sold_price': '',
                        'sale_date': '',
                        'lot_number': str(i + 1),
                        'auction_price': '',
                        'postcode': '',
                        'source_url': lot_url,
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
        
        context.close()
        browser.close()
    
    print(f"Successfully extracted {len(lots)} lots from auction")
    return lots

def extract_auction_results_table(page):
    """
    Extract the auction results table from the main auction page.
    Returns a dictionary mapping lot numbers to their results.
    """
    auction_results = {}
    
    try:
        # Look for tables with "Result" column
        tables = page.query_selector_all("table")
        print(f"    🔍 Found {len(tables)} tables on the auction page")
        for i, table in enumerate(tables):
            print(f"    📋 Processing table {i+1}/{len(tables)}")
            # Check if this table has a "Result" column
            headers = table.query_selector_all("th, td")
            result_column_index = -1
            lot_column_index = -1
            
            # Find the "Result" and "Lot No" columns
            print(f"    📋 Table {i+1} headers: {[h.text_content().strip() for h in headers[:5]]}...")
            for j, header in enumerate(headers):
                header_text = header.text_content().strip().lower()
                if "result" in header_text:
                    result_column_index = j
                    print(f"    ✅ Found 'Result' column at index {j}")
                elif "lot" in header_text and "no" in header_text:
                    lot_column_index = j
                    print(f"    ✅ Found 'Lot No' column at index {j}")
            
            if result_column_index >= 0 and lot_column_index >= 0:
                # Extract data from each row
                rows = table.query_selector_all("tr")
                for row in rows:
                    cells = row.query_selector_all("td")
                    if len(cells) > max(result_column_index, lot_column_index):
                        # Extract lot number (can include letters like "156A", "157B")
                        lot_cell = cells[lot_column_index].text_content().strip()
                        lot_match = re.search(r'(\d+[A-Za-z]*)', lot_cell)
                        if lot_match:
                            lot_number = lot_match.group(1)
                            
                            # Extract result
                            result_cell = cells[result_column_index].text_content().strip()
                            if result_cell:
                                auction_results[lot_number] = result_cell
                                print(f"    📋 Lot {lot_number}: {result_cell}")
        
        print(f"    ✅ Extracted {len(auction_results)} lot results from auction table")
        return auction_results
        
    except Exception as e:
        print(f"    ⚠️ Error extracting auction results table: {e}")
        return {}


def lookup_property_in_prices_page(page, address):
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
        
        # Set realistic user agent and headers
        page.set_extra_http_headers({
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
                page.goto(property_prices_url, wait_until="networkidle", timeout=30000)
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    retry_delay = (attempt + 1) * 5  # Exponential backoff: 5s, 10s, 15s
                    print(f"    ⚠️ Navigation failed (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s: {e}")
                    time.sleep(retry_delay)
                else:
                    print(f"    ❌ Navigation failed after {max_retries} attempts: {e}")
                    return None
        
        # Check if page loaded successfully
        page_title = page.title()
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
        page_text = page.locator("body").text_content()
        
        # Normalize the address for comparison (remove extra spaces, make lowercase)
        normalized_address = re.sub(r'\s+', ' ', address.strip()).lower()
        
        # Debug: Show some addresses from the page to understand the format
        print(f"    🔍 Page contains {len(page_text)} characters")
        
        # Look for table rows to see what addresses are available
        table_rows = page.query_selector_all("table tr, .table tr")
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
        table_rows = page.query_selector_all("table tr")
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
            'price_bought': '',
            'sold_price': '',
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
        
        # Extract price bought from the auction results table
        # First try to get it from the auction results table we extracted earlier
        print(f"    🔍 Debug: Looking for lot_number '{lot_data['lot_number']}' in auction_results keys: {list(auction_results.keys())}")
        if auction_results and lot_data['lot_number'] in auction_results:
            result_text = auction_results[lot_data['lot_number']]
            import re
            
            # Look for "Sold for £X" format
            sold_for_match = re.search(r'Sold\s+for\s+£([\d,]+(?:,\d{3})*)', result_text, re.IGNORECASE)
            if sold_for_match:
                lot_data['price_bought'] = f"£{sold_for_match.group(1)}"
                print(f"    📍 Found price from auction results table: {lot_data['price_bought']}")
            else:
                # Use the full result text (for status like "Sold prior to auction for an undisclosed amount.")
                lot_data['price_bought'] = result_text
                print(f"    📍 Found status from auction results table: {lot_data['price_bought']}")
        else:
            # Fallback: Look for tables with "Result" column that contains "Sold for £X" or status
            price_bought_selectors = [
                "table",  # Look for any table
                ".results-table",
                ".auction-results",
                ".lot-results",
                "[class*='results']",
                "[class*='table']"
            ]
        
        price_bought_found = False
        for selector in price_bought_selectors:
            try:
                # Look for tables with "Result" column
                tables = lot_page.query_selector_all(selector)
                for table in tables:
                    # Check if this table has a "Result" column
                    headers = table.query_selector_all("th, td")
                    result_column_index = -1
                    
                    # Find the "Result" column
                    for i, header in enumerate(headers):
                        header_text = header.text_content().strip().lower()
                        if "result" in header_text:
                            result_column_index = i
                            break
                    
                    if result_column_index >= 0:
                        # Find the row that matches our lot number
                        rows = table.query_selector_all("tr")
                        for row in rows:
                            cells = row.query_selector_all("td")
                            if len(cells) > result_column_index:
                                # Check if this row is for our lot
                                first_cell = cells[0].text_content().strip()
                                if f"Lot {lot_data['lot_number']}" in first_cell or lot_data['lot_number'] in first_cell:
                                    # Extract the result text
                                    result_cell = cells[result_column_index].text_content().strip()
                                    if result_cell:
                                        # Look for "Sold for £X" or status patterns
                                        import re
                                        
                                        # Look for "Sold for £X" format
                                        sold_for_match = re.search(r'Sold\s+for\s+£([\d,]+(?:,\d{3})*)', result_cell, re.IGNORECASE)
                                        if sold_for_match:
                                            lot_data['price_bought'] = f"£{sold_for_match.group(1)}"
                                            price_bought_found = True
                                            print(f"    📍 Found price from results table: {lot_data['price_bought']}")
                                            break
                                        
                                        # Look for status patterns
                                        status_patterns = [
                                            r'(Sold\s+prior\s+to\s+auction\s+for\s+an\s+undisclosed\s+amount\.?)',
                                            r'(Withdrawn\s+Prior\.?)',
                                            r'(Sold\s+Prior\.?)',
                                            r'(Reserved\.?)',
                                            r'(Withdrawn\.?)',
                                            r'(Sold\.?)'
                                        ]
                                        
                                        for pattern in status_patterns:
                                            match = re.search(pattern, result_cell, re.IGNORECASE)
                                            if match:
                                                lot_data['price_bought'] = match.group(1)
                                                price_bought_found = True
                                                print(f"    📍 Found status from results table: {lot_data['price_bought']}")
                                                break
                                        
                                        if price_bought_found:
                                            break
                        
                        if price_bought_found:
                            break
            except Exception as e:
                print(f"    ⚠️ Error processing table {selector}: {e}")
                continue
            
            if price_bought_found:
                break
        
        # If no price bought found with selectors, try to extract from page text
        if not price_bought_found:
            try:
                page_text = lot_page.locator("body").text_content()
                if page_text:
                    import re
                    # Look for price bought patterns in the page text
                    price_patterns = [
                        r'Sold\s+for\s+£([\d,]+(?:,\d{3})*)',  # "Sold for £306,000"
                        r'£([\d,]+(?:,\d{3})*)',                # Standard price format like £185,000
                        r'Guide.*?£([\d,]+(?:,\d{3})*)',
                        r'Estimate.*?£([\d,]+(?:,\d{3})*)',
                        r'Price.*?£([\d,]+(?:,\d{3})*)',
                        r'(Withdrawn\s+Prior\.?)',    # Withdrawn status
                        r'(Sold\s+Prior\.?)',         # Sold prior status
                        r'(Reserved\.?)',             # Reserved status
                        r'(Withdrawn\.?)',            # Just Withdrawn
                        r'(Sold\.?)'                  # Just Sold
                    ]
                    
                    for pattern in price_patterns:
                        match = re.search(pattern, page_text, re.IGNORECASE)
                        if match:
                            if '£' in pattern:
                                lot_data['price_bought'] = f"£{match.group(1)}"
                            else:
                                lot_data['price_bought'] = match.group(1)
                            price_bought_found = True
                            print(f"    📍 Found price bought from page text: {lot_data['price_bought']}")
                            break
            except Exception as e:
                print(f"    ⚠️ Error extracting price bought from page text: {e}")
        
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
                lot_data['sold_price'] = property_data.get('sale_price', '')  # Actual sold price from property prices database
                
                # Keep the original price_bought from the auction listing
                # The sold_price from property prices database is separate
                # Only set to "Sold prior to auction" if the auction listing itself shows that status
                
                lot_data['property_prices_status'] = 'found'
                lot_data['property_prices_postcode'] = property_data.get('postcode', '')
                lot_data['property_prices_sale_date'] = property_data.get('sale_date', '')
                lot_data['property_prices_sale_price'] = property_data.get('sale_price', '')
                print(f"  ✅ Lot {lot_data['lot_number']}: {lot_data['address']} - Price Bought: {lot_data['price_bought']}, Sold: {lot_data['sold_price']} (found in property prices)")
            else:
                # Address not found in property prices - still return the lot data
                lot_data['property_prices_status'] = 'not_found'
                lot_data['property_prices_postcode'] = ''
                lot_data['property_prices_sale_date'] = ''
                lot_data['property_prices_sale_price'] = ''
                print(f"  📝 Lot {lot_data['lot_number']}: {lot_data['address']} - Price Bought: {lot_data['price_bought']}, Sold: Not found (will still be imported)")
        
        # Always return the lot data, regardless of property prices status
        return lot_data
        
    except Exception as e:
        print(f"Error extracting lot data from page: {e}")
        return None

def process_auctions_to_sheets(start_date: str, end_date: str):
    """
    Main workflow function that:
    1. Finds auctions in the date range
    2. Extracts property listings from each auction
    3. Imports each lot immediately to sheets after processing
    4. Provides real-time progress tracking
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        Dict with processing results
    """
    from sheets_webapp import PropertyDataManagerWebApp as PropertyDataManager
    
    print(f"=== PROCESSING AUCTIONS FROM {start_date} TO {end_date} ===")
    
    # Step 1: Find auctions
    print("\n1. Finding auctions...")
    auctions = find_auctions(start_date, end_date)
    print(f"Found {len(auctions)} auctions")
    
    if not auctions:
        return {
            "status": "no_auctions",
            "message": "No auctions found in the specified date range"
        }
    
    # Initialize sheets manager
    sheets_manager = PropertyDataManager()
    
    # Step 2: Process each auction and import lots immediately
    total_imported = 0
    total_skipped = 0
    total_lots_found = 0
    
    for i, auction in enumerate(auctions):
        print(f"\n2.{i+1}. Processing auction {i+1}/{len(auctions)}: {auction.get('name', 'Unknown')}")
        
        if auction.get('detail_url'):
            try:
                lots = parse_event_days(
                    auction['detail_url'], 
                    auction.get('name', 'Auction House London'),
                    auction.get('date', '')
                )
                total_lots_found += len(lots)
                
                print(f"   Found {len(lots)} lots in this auction")
                
                # Process each lot individually and import immediately when match found
                for j, lot in enumerate(lots):
                    print(f"   Processing lot {j+1}/{len(lots)}: {lot.get('address', 'No address')}")
                    print(f"   Lot property_prices_status: {lot.get('property_prices_status', 'NOT SET')}")
                    
                    # Import lots that have price_bought data (regardless of property prices status)
                    if lot.get('price_bought') and lot.get('price_bought').strip():
                        print(f"   🎯 PRICE FOUND! Importing lot {j+1} with price_bought: {lot.get('price_bought')}...")
                        
                        property_data = {
                            'auction_name': auction.get('name', ''),
                            'auction_date': auction.get('date', ''),
                            'address': lot.get('address', ''),
                            'price_bought': lot.get('price_bought', ''),  # Price bought from auction listing
                            'lot_number': lot.get('lot_number', ''),
                            'postcode': lot.get('postcode', ''),
                            'sold_price': lot.get('sold_price', ''),
                            'sold_date': lot.get('sale_date', ''),  # Sale date from property prices
                            'auction_url': auction.get('detail_url', ''),
                            # Additional metadata fields
                            'source_url': lot.get('source_url', ''),
                            'property_prices_status': 'found',
                            'property_prices_postcode': lot.get('property_prices_postcode', ''),
                            'property_prices_sale_date': lot.get('property_prices_sale_date', ''),
                            'property_prices_sale_price': lot.get('property_prices_sale_price', ''),
                            'searchland_status': 'pending'
                        }
                        
                        # Ensure all required fields have at least empty string values
                        for field in ['auction_name', 'auction_date', 'address', 'price_bought', 'lot_number', 'postcode', 'sold_price', 'sold_date', 'auction_url']:
                            if field not in property_data or property_data[field] is None:
                                property_data[field] = ''
                        
                        # Import this lot immediately to sheets
                        try:
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
                        print(f"   ⏭️ Lot {j+1} skipped - no price_bought data found")
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
    print(f"\n📊 Import Summary:")
    print(f"   ✅ Total imported: {total_imported}")
    print(f"   ⏭️ Total skipped: {total_skipped}")
    print(f"   📈 Success rate: {total_imported/(total_imported+total_skipped)*100:.1f}%" if (total_imported+total_skipped) > 0 else "   📈 Success rate: 0%")
    
    return {
        "status": "success",
        "total_imported": total_imported,
        "total_skipped": total_skipped,
        "total_lots_found": total_lots_found,
        "message": f"Imported {total_imported} properties, skipped {total_skipped}"
    }
