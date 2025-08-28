#!/usr/bin/env python3
"""
Date formatting utility to convert various date formats to standard YYYY-MM-DD
"""

from datetime import datetime
import re

def format_date_to_standard(date_input):
    """
    Convert various date formats to standard YYYY-MM-DD format
    
    Args:
        date_input (str): Date in various formats
        
    Returns:
        str: Date in YYYY-MM-DD format
    """
    if not date_input or date_input.strip() == "":
        return ""
    
    date_str = str(date_input).strip()
    
    # If already in YYYY-MM-DD format, return as is
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return date_str
    
    # Handle ISO 8601 timestamps like "2025-08-05T23:00:00.000Z" or "2025-08-05T23:00:00"
    if 'T' in date_str:
        try:
            # Handle different ISO formats
            if date_str.endswith('Z'):
                # UTC timezone
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            elif '+' in date_str or '-' in date_str[-6:]:
                # Has timezone info
                dt = datetime.fromisoformat(date_str)
            else:
                # No timezone info, assume local
                dt = datetime.fromisoformat(date_str)
            return dt.strftime('%Y-%m-%d')
        except:
            pass
    
    # Handle other common formats
    date_formats = [
        '%Y-%m-%dT%H:%M:%S.%fZ',  # 2025-08-05T23:00:00.000Z
        '%Y-%m-%dT%H:%M:%SZ',     # 2025-08-05T23:00:00Z
        '%Y-%m-%d %H:%M:%S',      # 2025-08-05 23:00:00
        '%d/%m/%Y',               # 05/08/2025
        '%m/%d/%Y',               # 08/05/2025
        '%d-%m-%Y',               # 05-08-2025
        '%m-%d-%Y',               # 08-05-2025
        '%d %B %Y',               # 05 August 2025
        '%d %b %Y',               # 05 Aug 2025
        '%B %d, %Y',              # August 05, 2025
    ]
    
    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    # If no format matches, return original
    return date_str

def format_dates_list(date_list):
    """
    Format a list of dates to standard YYYY-MM-DD format
    
    Args:
        date_list (list): List of dates in various formats
        
    Returns:
        list: List of dates in YYYY-MM-DD format
    """
    return [format_date_to_standard(date) for date in date_list]

def demonstrate_formatting():
    """Demonstrate the date formatting with your examples"""
    
    # Your example dates
    iso_dates = [
        "2025-08-05T23:00:00.000Z",
        "2025-08-05T23:00:00.000Z", 
        "2025-08-05T23:00:00.000Z",
        "2025-08-05T23:00:00.000Z",
        "2025-07-02T23:00:00.000Z",
        "2025-05-27T23:00:00.000Z"
    ]
    
    print("📅 Date Formatting Demo:")
    print("\n🔧 Original ISO Format:")
    for date in iso_dates:
        print(f"   {date}")
    
    print("\n✨ Converted to Standard Format:")
    formatted_dates = format_dates_list(iso_dates)
    for original, formatted in zip(iso_dates, formatted_dates):
        print(f"   {original} → {formatted}")
    
    print("\n📊 Summary:")
    unique_dates = list(set(formatted_dates))
    print(f"   Original count: {len(iso_dates)} dates")
    print(f"   Unique dates: {len(unique_dates)} dates")
    print(f"   Unique dates: {', '.join(unique_dates)}")

if __name__ == "__main__":
    demonstrate_formatting() 