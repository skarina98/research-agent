#!/usr/bin/env python3
"""
Script to login to Searchland and save session
"""

import asyncio
import os
from playwright.async_api import async_playwright

BASE_URL = "https://searchland.co.uk"

async def login_searchland():
    """Login to Searchland and save session"""
    
    print("🔐 Searchland Login Helper")
    print("=" * 40)
    print("This script will help you login to Searchland and save your session.")
    print("You'll need to manually enter your credentials in the browser window.")
    print()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            print(f"🌐 Navigating to Searchland...")
            await page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
            
            # Get page info
            title = await page.title()
            url = page.url
            print(f"📄 Page title: {title}")
            print(f"🔗 Page URL: {url}")
            
            print(f"\n📋 Instructions:")
            print(f"   1. Login to Searchland in the browser window")
            print(f"   2. Navigate to the main search page")
            print(f"   3. Make sure you can search for properties")
            print(f"   4. Press Enter here when ready to save session")
            print()
            
            input("Press Enter when you're logged in and ready to save session...")
            
            # Check if we're on a search page
            current_title = await page.title()
            current_url = page.url
            print(f"📄 Current title: {current_title}")
            print(f"🔗 Current URL: {current_url}")
            
            # Look for search functionality
            search_inputs = await page.query_selector_all("input[placeholder*='search'], input[placeholder*='Search'], input[placeholder*='address'], input[placeholder*='Address']")
            
            if search_inputs:
                print(f"✅ Found {len(search_inputs)} search inputs - looks good!")
            else:
                print(f"⚠️ No search inputs found - you may need to navigate to the search page")
                print(f"   Please navigate to the property search page and press Enter...")
                input("Press Enter when on the search page...")
            
            # Save the session
            session_file = "sessions/searchland.json"
            os.makedirs("sessions", exist_ok=True)
            
            await context.storage_state(path=session_file)
            print(f"✅ Session saved to: {session_file}")
            
            print(f"\n🎉 Login successful! You can now run the Searchland workflow.")
            print(f"   The session will be automatically used in future runs.")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(login_searchland()) 