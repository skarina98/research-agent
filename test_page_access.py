#!/usr/bin/env python3
"""
Simple test to check Searchland page access
"""

import asyncio
import os
from playwright.async_api import async_playwright

async def test_page_access():
    """Test if we can access the Searchland page"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        # Check if session file exists
        session_file = "sessions/searchland.json"
        if os.path.exists(session_file):
            print(f"🔐 Using existing Searchland session")
            context = await browser.new_context(storage_state=session_file)
        else:
            print(f"⚠️ No Searchland session found, creating new context")
            context = await browser.new_context()
        
        page = await context.new_page()
        
        try:
            print(f"🌐 Navigating to Searchland...")
            await page.goto("https://app.searchland.co.uk", wait_until="domcontentloaded", timeout=30000)
            
            # Check page title and URL
            page_title = await page.title()
            page_url = page.url
            print(f"📄 Page title: {page_title}")
            print(f"🔗 Page URL: {page_url}")
            
            # Check if we need to login
            if "login" in page_url.lower() or "sign in" in page_title.lower():
                print(f"⚠️ Redirected to login page - you may need to login manually")
                await browser.close()
                return
            
            # Wait a bit for page to load
            await page.wait_for_timeout(3000)
            
            # Look for any elements with 'search' in their attributes
            print(f"🔍 Looking for search-related elements...")
            
            # Check for elements by ID
            search_by_id = await page.query_selector_all("[id*='search']")
            print(f"Found {len(search_by_id)} elements with 'search' in ID")
            for i, elem in enumerate(search_by_id[:3]):
                elem_id = await elem.get_attribute("id")
                elem_tag = await elem.evaluate("el => el.tagName")
                print(f"   Element {i+1}: id='{elem_id}', tag='{elem_tag}'")
            
            # Check for elements by class
            search_by_class = await page.query_selector_all("[class*='search']")
            print(f"Found {len(search_by_class)} elements with 'search' in class")
            for i, elem in enumerate(search_by_class[:3]):
                elem_class = await elem.get_attribute("class")
                elem_tag = await elem.evaluate("el => el.tagName")
                print(f"   Element {i+1}: class='{elem_class}', tag='{elem_tag}'")
            
            # Check for input elements
            inputs = await page.query_selector_all("input")
            print(f"Found {len(inputs)} input elements")
            for i, inp in enumerate(inputs[:5]):
                placeholder = await inp.get_attribute("placeholder")
                input_type = await inp.get_attribute("type")
                input_id = await inp.get_attribute("id")
                print(f"   Input {i+1}: placeholder='{placeholder}', type='{input_type}', id='{input_id}'")
            
            print(f"⏸️ Browser window will stay open for manual inspection...")
            print(f"   Please look for the search functionality and note what you see")
            print(f"   Close the browser window when done")
            
            # Keep browser open for manual inspection
            await page.wait_for_timeout(30000)  # Wait 30 seconds
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_page_access()) 