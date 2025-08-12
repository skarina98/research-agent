#!/usr/bin/env python3
"""
Debug script to explore Searchland page structure
"""

import asyncio
import os
from playwright.async_api import async_playwright

BASE_URL = "https://searchland.co.uk"

async def debug_searchland():
    """Debug Searchland page structure"""
    
    print("🔍 Debugging Searchland page structure")
    print("=" * 40)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Set to False to see what's happening
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
            
            # Check if we're on a login page
            if "login" in title.lower() or "sign in" in title.lower():
                print(f"⚠️ On login page - you may need to login manually")
                print(f"   Please login in the browser window and press Enter to continue...")
                input("Press Enter after logging in...")
            
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
                        for i, element in enumerate(elements[:3]):  # Show first 3
                            placeholder = await element.get_attribute("placeholder")
                            input_type = await element.get_attribute("type")
                            input_name = await element.get_attribute("name")
                            input_id = await element.get_attribute("id")
                            print(f"   Element {i+1}: placeholder='{placeholder}', type='{input_type}', name='{input_name}', id='{input_id}'")
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
            
            for i, button in enumerate(buttons[:5]):  # Show first 5
                try:
                    button_text = await button.text_content()
                    button_type = await button.get_attribute("type")
                    print(f"   Button {i+1}: text='{button_text[:50]}', type='{button_type}'")
                except:
                    pass
            
            # Take a screenshot
            await page.screenshot(path="searchland_debug.png")
            print(f"\n📸 Screenshot saved as 'searchland_debug.png'")
            
            print(f"\n⏸️ Browser window will stay open for manual inspection...")
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
    asyncio.run(debug_searchland()) 