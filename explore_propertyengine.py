#!/usr/bin/env python3
"""
Explore PropertyEngine interface to find correct selectors
"""

from playwright.sync_api import sync_playwright
import time

def explore_propertyengine():
    """Explore PropertyEngine interface"""
    
    print("🔍 Exploring PropertyEngine Interface")
    print("=" * 50)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            # Navigate to PropertyEngine
            print("🌐 Navigating to PropertyEngine...")
            page.goto("https://propertyengine.co.uk/", wait_until="networkidle")
            time.sleep(5)
            
            print("📋 Page title:", page.title())
            print("🔗 Current URL:", page.url)
            
            # Take a screenshot
            page.screenshot(path="propertyengine_homepage.png")
            print("📸 Screenshot saved: propertyengine_homepage.png")
            
            # Look for all input fields
            print("\n🔍 Looking for input fields...")
            input_fields = page.query_selector_all("input, textarea")
            print(f"Found {len(input_fields)} input fields")
            
            for i, field in enumerate(input_fields[:10]):  # Show first 10
                try:
                    field_type = field.get_attribute("type") or "text"
                    placeholder = field.get_attribute("placeholder") or "No placeholder"
                    id_attr = field.get_attribute("id") or "No ID"
                    class_attr = field.get_attribute("class") or "No class"
                    
                    print(f"  Input {i+1}:")
                    print(f"    Type: {field_type}")
                    print(f"    Placeholder: {placeholder}")
                    print(f"    ID: {id_attr}")
                    print(f"    Class: {class_attr}")
                    print()
                except Exception as e:
                    print(f"  Input {i+1}: Error reading attributes - {e}")
            
            # Look for buttons
            print("🔍 Looking for buttons...")
            buttons = page.query_selector_all("button, input[type='submit'], input[type='button']")
            print(f"Found {len(buttons)} buttons")
            
            for i, button in enumerate(buttons[:10]):  # Show first 10
                try:
                    button_text = button.text_content().strip() or "No text"
                    button_type = button.get_attribute("type") or "button"
                    button_id = button.get_attribute("id") or "No ID"
                    button_class = button.get_attribute("class") or "No class"
                    
                    print(f"  Button {i+1}:")
                    print(f"    Text: '{button_text}'")
                    print(f"    Type: {button_type}")
                    print(f"    ID: {button_id}")
                    print(f"    Class: {button_class}")
                    print()
                except Exception as e:
                    print(f"  Button {i+1}: Error reading attributes - {e}")
            
            # Look for forms
            print("🔍 Looking for forms...")
            forms = page.query_selector_all("form")
            print(f"Found {len(forms)} forms")
            
            for i, form in enumerate(forms):
                try:
                    form_action = form.get_attribute("action") or "No action"
                    form_method = form.get_attribute("method") or "No method"
                    form_id = form.get_attribute("id") or "No ID"
                    form_class = form.get_attribute("class") or "No class"
                    
                    print(f"  Form {i+1}:")
                    print(f"    Action: {form_action}")
                    print(f"    Method: {form_method}")
                    print(f"    ID: {form_id}")
                    print(f"    Class: {form_class}")
                    print()
                except Exception as e:
                    print(f"  Form {i+1}: Error reading attributes - {e}")
            
            # Get page content to understand the interface
            print("📄 Page content preview:")
            page_text = page.locator("body").text_content()
            print(page_text[:1000] + "..." if len(page_text) > 1000 else page_text)
            
        except Exception as e:
            print(f"❌ Error exploring PropertyEngine: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()
    
    print("\n✅ PropertyEngine exploration completed!")

if __name__ == "__main__":
    explore_propertyengine() 