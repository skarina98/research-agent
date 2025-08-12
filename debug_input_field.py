#!/usr/bin/env python3
"""
Debug script to investigate the input field after clicking Specific address tab
"""

import asyncio
import os
from playwright.async_api import async_playwright

async def debug_input_field():
    """Debug the input field after clicking Specific address tab"""
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
                await page.wait_for_timeout(2000)
            else:
                print(f"❌ Could not find 'Specific address' tab")
                return
            
            # Step 3: Check all inputs and their visibility
            print(f"\n🔍 Step 3: Checking all inputs and their visibility...")
            inputs = await page.query_selector_all("input")
            print(f"Found {len(inputs)} input elements")
            
            for i, inp in enumerate(inputs):
                placeholder = await inp.get_attribute("placeholder")
                input_type = await inp.get_attribute("type")
                input_id = await inp.get_attribute("id")
                
                # Check if element is visible
                is_visible = await inp.is_visible()
                is_enabled = await inp.is_enabled()
                
                print(f"   Input {i+1}: placeholder='{placeholder}', type='{input_type}', id='{input_id}', visible={is_visible}, enabled={is_enabled}")
                
                # If this looks like the address input, try to interact with it
                if placeholder and ("search" in placeholder.lower() or "address" in placeholder.lower() or "type" in placeholder.lower()):
                    print(f"      🎯 This looks like the address input!")
                    try:
                        # Try to scroll it into view
                        await inp.scroll_into_view_if_needed()
                        print(f"      ✅ Scrolled into view")
                        
                        # Try to click it
                        await inp.click()
                        print(f"      ✅ Clicked successfully")
                        
                        # Try to type something
                        await inp.fill("test")
                        print(f"      ✅ Typed 'test' successfully")
                        
                        # Clear it
                        await inp.fill("")
                        print(f"      ✅ Cleared successfully")
                        
                        print(f"      🎉 This input field is working!")
                        break
                        
                    except Exception as e:
                        print(f"      ❌ Error interacting with this input: {e}")
            
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
    asyncio.run(debug_input_field()) 