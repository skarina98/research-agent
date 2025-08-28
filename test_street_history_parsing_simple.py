#!/usr/bin/env python3
"""
Simple test to debug street history parsing logic
"""

import re
from datetime import datetime, timedelta

def test_extract_auction_info():
    """Test the extract_auction_info_from_element function logic"""
    
    print("🔍 Testing Street History Parsing Logic")
    print("=" * 45)
    
    # Mock data based on the log output
    current_auction_name = "SDL Property Auctions"
    current_auction_date = "2025-01-15"
    target_address = "Flat 25, Wadhurst Court, Downview Road, Worthing, BN11 4QX"
    
    # Mock element texts that might be found (based on typical EIG street history format)
    mock_elements = [
        # Element 1: Typical format with date and auction info
        """Flat 25, Wadhurst Court, Downview Road, Worthing, BN11 4QX
Auction House London
15/10/2024
Sold for £220,000""",
        
        # Element 2: Different date format
        """Flat 25, Wadhurst Court, Downview Road, Worthing, BN11 4QX
SDL Property Auctions
20-11-2024
Unsold""",
        
        # Element 3: Another format
        """Flat 25, Wadhurst Court, Downview Road, Worthing, BN11 4QX
Auction House London
01 December 2024
Sold prior for £235,000""",
        
        # Element 4: Same date as current auction (should be disregarded)
        """Flat 25, Wadhurst Court, Downview Road, Worthing, BN11 4QX
SDL Property Auctions
15/01/2025
Sold for £240,000"""
    ]
    
    print(f"📅 Current auction date: {current_auction_date}")
    print(f"🏢 Current auction name: {current_auction_name}")
    print(f"📍 Target address: {target_address}")
    print()
    
    for i, element_text in enumerate(mock_elements, 1):
        print(f"📄 Testing Element {i}:")
        print(f"   Text: {element_text}")
        
        # Test the date extraction logic
        date_patterns = [
            r'(\d{1,2}/\d{1,2}/\d{4})',  # DD/MM/YYYY
            r'(\d{1,2}-\d{1,2}-\d{4})',  # DD-MM-YYYY
            r'(\d{1,2}\s+[A-Za-z]+\s+\d{4})',  # DD Month YYYY
        ]
        
        auction_date = None
        for pattern in date_patterns:
            match = re.search(pattern, element_text)
            if match:
                date_str = match.group(1)
                try:
                    if '/' in date_str:
                        auction_date = datetime.strptime(date_str, "%d/%m/%Y")
                    elif '-' in date_str:
                        auction_date = datetime.strptime(date_str, "%d-%m-%Y")
                    else:
                        auction_date = datetime.strptime(date_str, "%d %B %Y")
                    print(f"   📅 Extracted date: {auction_date.strftime('%Y-%m-%d')}")
                    break
                except Exception as e:
                    print(f"   ❌ Error parsing date '{date_str}': {e}")
                    continue
        
        if not auction_date:
            print(f"   ❌ No valid date found")
            continue
        
        # Test auction name extraction
        auctioneer_names = [
            "SDL Property Auctions",
            "Auction House London", 
            "McHugh & Co",
            "Bonde Wolfe",
            "Auction House South West",
            "Savills"
        ]
        
        auction_name = None
        for name in auctioneer_names:
            if name.lower() in element_text.lower():
                auction_name = name
                print(f"   🏢 Found auction name: {auction_name}")
                break
        
        if not auction_name:
            print(f"   ❌ No auction name found")
            continue
        
        # Test date comparison logic
        try:
            current_date = datetime.strptime(current_auction_date, "%Y-%m-%d")
            date_diff = abs((current_date - auction_date).days)
            print(f"   ⏰ Date difference: {date_diff} days")
            
            if date_diff > 180:
                print(f"   ❌ More than 6 months - skipping")
                continue
            
            if auction_date.date() == current_date.date():
                print(f"   ❌ Same date as current auction - disregarding")
                continue
            
            print(f"   ✅ Date is within 6 months and different from current")
            
        except Exception as e:
            print(f"   ❌ Error comparing dates: {e}")
            continue
        
        # Test sold/unsold pattern detection
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
        
        unsold_patterns = [
            "unsold",
            "withdrawn",
            "passed",
            "no bids",
            "no sale",
            "not sold",
            "failed to sell"
        ]
        
        has_sold_indicator = "withdrawn prior" in element_text.lower()
        if not has_sold_indicator:
            has_sold_indicator = any(pattern in element_text.lower() for pattern in sold_patterns)
        
        has_unsold_indicator = any(pattern in element_text.lower() for pattern in unsold_patterns)
        
        print(f"   💰 Has sold indicator: {has_sold_indicator}")
        print(f"   ❌ Has unsold indicator: {has_unsold_indicator}")
        
        if not has_sold_indicator and not has_unsold_indicator:
            print(f"   ❌ No clear sale/unsold status")
            continue
        
        # Test address matching
        target_address_lower = target_address.lower()
        element_text_lower = element_text.lower()
        
        exact_match = target_address_lower in element_text_lower
        print(f"   📍 Exact address match: {exact_match}")
        
        if exact_match:
            print(f"   🎯 RELEVANT ENTRY FOUND!")
            print(f"   📊 Would return auction info for this entry")
        else:
            print(f"   ❌ Address doesn't match")
        
        print()

if __name__ == "__main__":
    test_extract_auction_info() 