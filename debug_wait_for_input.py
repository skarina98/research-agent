#!/usr/bin/env python3
"""
Debug script to wait longer for the input field to appear
"""

import asyncio
import os
from playwright.async_api import async_playwright

async def debug_wait_for_input():
    """Debug waiting for the input field to appear"""
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
            else:
                print(f"❌ Could not find 'Specific address' tab")
                return
            
            # Step 3: Wait and check for the input field multiple times
            print(f"\n🔍 Step 3: Waiting for input field to appear...")
            
            for attempt in range(10):  # Try 10 times
                print(f"   Attempt {attempt + 1}: Waiting 2 seconds...")
                await page.wait_for_timeout(2000)
                
                # Check for the specific input field
                address_input = await page.query_selector("input[placeholder='Start type to search']")
                if address_input:
                    print(f"   ✅ Found input field with placeholder 'Start type to search'!")
                    
                    # Check if it's visible and enabled
                    is_visible = await address_input.is_visible()
                    is_enabled = await address_input.is_enabled()
                    print(f"   📊 Input field: visible={is_visible}, enabled={is_enabled}")
                    
                    if is_visible and is_enabled:
                        print(f"   🎉 Input field is ready to use!")
                        
                        # Try to interact with it
                        try:
                            await address_input.click()
                            print(f"   ✅ Clicked input field")
                            
                            await address_input.fill("test address")
                            print(f"   ✅ Typed 'test address'")
                            
                            await address_input.fill("")
                            print(f"   ✅ Cleared input field")
                            
                            print(f"   🎉 Input field is working perfectly!")
                            break
                            
                        except Exception as e:
                            print(f"   ❌ Error interacting with input field: {e}")
                    else:
                        print(f"   ⚠️ Input field found but not ready (visible={is_visible}, enabled={is_enabled})")
                else:
                    print(f"   ❌ Input field not found yet")
                    
                    # Show all available inputs
                    inputs = await page.query_selector_all("input")
                    print(f"   📋 Available inputs ({len(inputs)} total):")
                    for i, inp in enumerate(inputs):
                        placeholder = await inp.get_attribute("placeholder")
                        input_type = await inp.get_attribute("type")
                        input_id = await inp.get_attribute("id")
                        is_visible = await inp.is_visible()
                        print(f"      Input {i+1}: placeholder='{placeholder}', type='{input_type}', id='{input_id}', visible={is_visible}")
            
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
    asyncio.run(debug_wait_for_input()) 