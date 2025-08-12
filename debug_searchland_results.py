#!/usr/bin/env python3
"""
Debug script to see what happens after Searchland search
"""

import asyncio
import os
from playwright.async_api import async_playwright

async def debug_searchland_results():
    """Debug what happens after Searchland search"""
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
            
            # Wait a bit for page to fully load
            await page.wait_for_timeout(2000)
            
            print(f"📄 Page title: {await page.title()}")
            print(f"🔗 Page URL: {page.url}")
            
            # Step 1: Find and click the search bar
            print(f"\n🔍 Step 1: Looking for search bar...")
            search_bar = await page.query_selector("#navigation-bar-search")
            if search_bar:
                print(f"✅ Found search bar")
                await search_bar.click()
                print(f"✅ Clicked search bar")
                await page.wait_for_timeout(1000)
            else:
                print(f"❌ Could not find search bar")
                return
            
            # Step 2: Click on "Specific address" tab
            print(f"\n🔍 Step 2: Looking for 'Specific address' tab...")
            specific_address_tab = await page.query_selector("button:has-text('Specific address')")
            if specific_address_tab:
                print(f"✅ Found 'Specific address' tab")
                await specific_address_tab.click()
                print(f"✅ Clicked 'Specific address' tab")
                await page.wait_for_timeout(1000)
            else:
                print(f"❌ Could not find 'Specific address' tab")
                return
            
            # Step 3: Find and fill the address input
            print(f"\n🔍 Step 3: Looking for address input...")
            address_input = await page.query_selector("input[placeholder='Start type to search']")
            if address_input:
                print(f"✅ Found address input")
                await address_input.fill("123 Oxford Street, London")
                print(f"✅ Filled address input")
                await address_input.press("Enter")
                print(f"✅ Pressed Enter")
                await page.wait_for_timeout(3000)
            else:
                print(f"❌ Could not find address input")
                return
            
            # Step 4: Check what appears after search
            print(f"\n🔍 Step 4: Checking for search results...")
            
            # Wait a bit for results to load
            await page.wait_for_timeout(5000)
            
            # Check page title and URL
            print(f"📄 Page title after search: {await page.title()}")
            print(f"🔗 Page URL after search: {page.url}")
            
            # Look for any elements that might be search results
            result_selectors = [
                ".property-result",
                ".search-result",
                "[class*='result']",
                ".property-card",
                ".result-item",
                ".property-item",
                ".search-item",
                ".listing",
                ".property",
                ".result",
                ".card",
                ".item"
            ]
            
            for selector in result_selectors:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"✅ Found {len(elements)} elements with selector: {selector}")
                    for i, elem in enumerate(elements[:3]):
                        try:
                            text = await elem.text_content()
                            print(f"   Element {i+1}: {text[:100]}...")
                        except:
                            pass
                else:
                    print(f"❌ No elements found with selector: {selector}")
            
            # Look for any text that might indicate results
            page_text = await page.locator("body").text_content()
            if "no results" in page_text.lower() or "not found" in page_text.lower():
                print(f"📋 Page contains 'no results' or 'not found' text")
            elif "results" in page_text.lower():
                print(f"📋 Page contains 'results' text")
            
            # Take a screenshot
            await page.screenshot(path="searchland_debug.png")
            print(f"📸 Screenshot saved as 'searchland_debug.png'")
            
            print(f"\n⏸️ Browser window will stay open for manual inspection...")
            print(f"   Please look at the current state and note what you see")
            print(f"   Close the browser window when done")
            
            # Keep browser open for manual inspection
            await page.wait_for_timeout(30000)  # Wait 30 seconds
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_searchland_results()) 