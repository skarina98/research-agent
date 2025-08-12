#!/usr/bin/env python3
"""
Debug script to explore Searchland app page structure
"""

import asyncio
import os
from playwright.async_api import async_playwright

BASE_URL = "https://app.searchland.co.uk"

async def debug_searchland_app():
    """Debug Searchland app page structure"""
    
    print("🔍 Debugging Searchland App Page Structure")
    print("=" * 50)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        # Use existing session if available
        session_file = "sessions/searchland.json"
        if os.path.exists(session_file):
            print(f"🔐 Using existing Searchland session")
            context = await browser.new_context(storage_state=session_file)
        else:
            print(f"⚠️ No session found, creating new context")
            context = await browser.new_context()
        
        page = await context.new_page()
        
        try:
            print(f"🌐 Navigating to Searchland app...")
            await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)
            
            # Wait a bit for the page to load
            await page.wait_for_timeout(5000)
            
            # Get page info
            title = await page.title()
            url = page.url
            print(f"📄 Page title: {title}")
            print(f"🔗 Page URL: {url}")
            
            # Look for search inputs
            print(f"\n🔍 Looking for search inputs...")
            
            # Try different selectors for search input
            search_selectors = [
                "#search-input",
                "input[placeholder*='search']",
                "input[type='search']",
                "input[name='search']",
                "input[placeholder*='Search']",
                "input[placeholder*='address']",
                "input[placeholder*='Address']",
                "input[placeholder*='property']",
                "input[placeholder*='Property']",
                ".search-input",
                ".search-box input",
                "[class*='search'] input",
                "input"
            ]
            
            for selector in search_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"✅ Found {len(elements)} elements with selector: {selector}")
                        for i, element in enumerate(elements[:5]):  # Show first 5
                            placeholder = await element.get_attribute("placeholder")
                            input_type = await element.get_attribute("type")
                            input_name = await element.get_attribute("name")
                            input_id = await element.get_attribute("id")
                            input_class = await element.get_attribute("class")
                            print(f"   Element {i+1}: placeholder='{placeholder}', type='{input_type}', name='{input_name}', id='{input_id}', class='{input_class}'")
                except Exception as e:
                    print(f"❌ Error with selector {selector}: {e}")
            
            # Look for any forms
            print(f"\n📋 Looking for forms...")
            forms = await page.query_selector_all("form")
            print(f"Found {len(forms)} forms")
            
            for i, form in enumerate(forms):
                try:
                    form_action = await form.get_attribute("action")
                    form_method = await form.get_attribute("method")
                    print(f"   Form {i+1}: action='{form_action}', method='{form_method}'")
                except:
                    pass
            
            # Look for buttons
            print(f"\n🔘 Looking for buttons...")
            buttons = await page.query_selector_all("button")
            print(f"Found {len(buttons)} buttons")
            
            for i, button in enumerate(buttons[:10]):  # Show first 10
                try:
                    button_text = await button.text_content()
                    button_type = await button.get_attribute("type")
                    button_class = await button.get_attribute("class")
                    print(f"   Button {i+1}: text='{button_text[:50].strip()}', type='{button_type}', class='{button_class}'")
                except:
                    pass
            
            # Look for any search-related elements
            print(f"\n🔍 Looking for search-related elements...")
            search_elements = await page.query_selector_all("[class*='search'], [id*='search'], [class*='Search'], [id*='Search']")
            print(f"Found {len(search_elements)} search-related elements")
            
            for i, element in enumerate(search_elements[:5]):
                try:
                    element_text = await element.text_content()
                    element_class = await element.get_attribute("class")
                    element_id = await element.get_attribute("id")
                    print(f"   Search Element {i+1}: text='{element_text[:50].strip()}', class='{element_class}', id='{element_id}'")
                except:
                    pass
            
            # Take a screenshot
            await page.screenshot(path="searchland_app_debug.png")
            print(f"\n📸 Screenshot saved as 'searchland_app_debug.png'")
            
            print(f"\n⏸️ Browser window will stay open for manual inspection...")
            print(f"   Please look for the search functionality and note what you see")
            print(f"   Close the browser window when done")
            
            # Keep browser open for manual inspection
            await page.wait_for_timeout(30000)  # Wait 30 seconds
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_searchland_app()) 