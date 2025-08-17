#!/usr/bin/env python3
"""
Test script using SerpAPI for Google search
"""

import requests
import json
import re

def search_property_listings(address, api_key):
    """
    Search for property listings using SerpAPI
    
    Args:
        address: Property address to search
        api_key: SerpAPI key
        
    Returns:
        List of property listing URLs
    """
    
    # Construct search query
    search_query = f"{address} rightmove onthemarket zoopla property"
    
    # SerpAPI endpoint
    url = "https://serpapi.com/search"
    
    params = {
        "q": search_query,
        "api_key": api_key,
        "engine": "google",
        "num": 10  # Number of results
    }
    
    try:
        print(f"🔍 Searching for: {address}")
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract organic results
            organic_results = data.get("organic_results", [])
            
            listing_links = []
            listing_domains = [
                'rightmove.co.uk',
                'onthemarket.com', 
                'zoopla.co.uk',
                'primelocation.com',
                'zoopla.com'
            ]
            
            for result in organic_results:
                link = result.get("link", "")
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                
                # Check if it's a property listing
                for domain in listing_domains:
                    if domain in link:
                        listing_links.append({
                            'url': link,
                            'title': title,
                            'snippet': snippet,
                            'domain': domain
                        })
                        break
            
            print(f"📋 Found {len(listing_links)} property listing links")
            for link in listing_links:
                print(f"   - {link['domain']}: {link['title']}")
            
            return listing_links
            
        else:
            print(f"❌ API request failed: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Error searching: {e}")
        return []

def test_serpapi():
    """Test SerpAPI search functionality"""
    
    # You'll need to get a free API key from https://serpapi.com/
    # Replace this with your actual API key
    api_key = "YOUR_SERPAPI_KEY_HERE"
    
    if api_key == "YOUR_SERPAPI_KEY_HERE":
        print("⚠️ Please get a free API key from https://serpapi.com/")
        print("   Then replace 'YOUR_SERPAPI_KEY_HERE' in the script")
        return
    
    # Test addresses
    test_addresses = [
        "39 Belham Walk, Camberwell, London, SE5 7DX",
        "123 High Street, London, SW1A 1AA"
    ]
    
    for address in test_addresses:
        print(f"\n🧪 Testing address: {address}")
        print("=" * 50)
        
        listings = search_property_listings(address, api_key)
        
        if listings:
            print(f"✅ Found {len(listings)} listings for {address}")
        else:
            print(f"❌ No listings found for {address}")
        
        print()

if __name__ == "__main__":
    test_serpapi() 