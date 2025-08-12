#!/usr/bin/env python3
"""
Debug script to test Searchland search sequence step by step
"""

import asyncio
import os
from playwright.async_api import async_playwright

async def debug_search_sequence():
    """Debug the search sequence step by step"""
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
            
            # Step 2: Look for the "Specific address" tab
            print(f"\n🔍 Step 2: Looking for 'Specific address' tab...")
            specific_address_tab = await page.query_selector("button:has-text('Specific address')")
            if specific_address_tab:
                print(f"✅ Found 'Specific address' tab")
                await specific_address_tab.click()
                print(f"✅ Clicked 'Specific address' tab")
                await page.wait_for_timeout(1000)
            else:
                print(f"❌ Could not find 'Specific address' tab")
                # Let's see what buttons are available
                buttons = await page.query_selector_all("button")
                print(f"Available buttons:")
                for i, btn in enumerate(buttons[:10]):
                    text = await btn.text_content()
                    print(f"   Button {i+1}: '{text}'")
                return
            
            # Step 3: Look for the address input field
            print(f"\n🔍 Step 3: Looking for address input field...")
            address_input = await page.query_selector("input[placeholder*='Start type to search'], input[placeholder*='type to search'], input[placeholder*='address'], input[placeholder*='Address']")
            if address_input:
                print(f"✅ Found address input field")
                placeholder = await address_input.get_attribute("placeholder")
                print(f"   Placeholder: '{placeholder}'")
            else:
                print(f"❌ Could not find address input field")
                # Let's see what inputs are available
                inputs = await page.query_selector_all("input")
                print(f"Available inputs:")
                for i, inp in enumerate(inputs[:10]):
                    placeholder = await inp.get_attribute("placeholder")
                    input_type = await inp.get_attribute("type")
                    input_id = await inp.get_attribute("id")
                    print(f"   Input {i+1}: placeholder='{placeholder}', type='{input_type}', id='{input_id}'")
            
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
    asyncio.run(debug_search_sequence()) 