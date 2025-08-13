#!/usr/bin/env python3
"""
Script to help login to EIG and save session state for automated use.
"""

from playwright.sync_api import sync_playwright
import os

def login_to_eig():
    """Login to EIG and save session state"""
    
    print("🔐 EIG Login Helper")
    print("=" * 50)
    print("This script will help you login to EIG and save your session.")
    print("A browser window will open where you can login manually.")
    print("After you login successfully, the session will be saved for automated use.")
    print()
    
    # Create sessions directory if it doesn't exist
    os.makedirs("sessions", exist_ok=True)
    
    with sync_playwright() as p:
        # Launch browser in non-headless mode so user can see and interact
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        print("🌐 Navigating to EIG main site...")
        
        # Navigate to main EIG site first
        page.goto("https://www.eigpropertyauctions.co.uk/")
        page.wait_for_timeout(3000)
        
        print("📋 Current page title:", page.title())
        print("🔗 Current URL:", page.url)
        
        # Look for login link or button
        print("🔍 Looking for login link...")
        
        login_selectors = [
            "a[href*='login']",
            "a[href*='log-in']",
            "a:has-text('Login')",
            "a:has-text('Log in')",
            "a:has-text('Sign in')",
            "button:has-text('Login')",
            "button:has-text('Log in')",
            ".login-link",
            ".login-button",
            "[class*='login']"
        ]
        
        login_found = False
        for selector in login_selectors:
            try:
                login_element = page.query_selector(selector)
                if login_element:
                    print(f"✅ Found login element with selector: {selector}")
                    login_element.click()
                    page.wait_for_timeout(2000)
                    login_found = True
                    break
            except Exception as e:
                continue
        
        if not login_found:
            print("⚠️ Could not find login link automatically.")
            print("   Please navigate to the login page manually in the browser.")
            print("   You can try going to: https://www.eigpropertyauctions.co.uk/login")
        
        print("📋 Current page title:", page.title())
        print("🔗 Current URL:", page.url)
        
        # Check if we're on a login page
        if "login" in page.title().lower() or "log-in" in page.url.lower():
            print("✅ Successfully on login page")
        else:
            print("⚠️ Not on expected login page, but continuing...")
        
        print()
        print("🔑 Please login manually in the browser window that opened.")
        print("   - Enter your username/email")
        print("   - Enter your password")
        print("   - Click login")
        print()
        print("⏳ Waiting for you to complete login...")
        print("   (The script will wait until you navigate away from the login page)")
        
        # Wait for user to login - we'll detect when they're no longer on login page
        login_completed = False
        max_wait_time = 300  # 5 minutes max wait
        wait_count = 0
        
        while not login_completed and wait_count < max_wait_time:
            try:
                current_url = page.url
                current_title = page.title()
                
                # Check if we're no longer on login page
                if ("login" not in current_url.lower() and 
                    "log-in" not in current_url.lower() and
                    "login" not in current_title.lower() and
                    "log-in" not in current_title.lower()):
                    
                    print(f"✅ Login appears successful!")
                    print(f"   Current URL: {current_url}")
                    print(f"   Current title: {current_title}")
                    login_completed = True
                    break
                
                # Wait 1 second before checking again
                page.wait_for_timeout(1000)
                wait_count += 1
                
                # Show progress every 30 seconds
                if wait_count % 30 == 0:
                    print(f"⏳ Still waiting... ({wait_count}s elapsed)")
                    
            except Exception as e:
                print(f"⚠️ Error checking page state: {e}")
                break
        
        if not login_completed:
            print("⏰ Timeout reached. Please complete login manually and press Enter when done.")
            input("Press Enter when you have completed login...")
        
        # Try to navigate to a page that requires authentication to verify login
        print("🔍 Verifying login by navigating to auction results...")
        try:
            page.goto("https://www.eigpropertyauctions.co.uk/clients/auctions/results?SelectedAuctioneerId=680")
            page.wait_for_timeout(3000)
            
            print(f"📋 Verification page title: {page.title()}")
            print(f"🔗 Verification URL: {page.url}")
            
            # Check if we're still on login page (login failed)
            if "login" in page.title().lower() or "log-in" in page.url.lower():
                print("❌ Login verification failed - still on login page")
                print("   Please try logging in again manually")
            else:
                print("✅ Login verification successful!")
                
        except Exception as e:
            print(f"⚠️ Error during verification: {e}")
        
        # Save the session state
        print("💾 Saving session state...")
        try:
            context.storage_state(path="sessions/eig.json")
            print("✅ Session saved to sessions/eig.json")
            print("   This session will be used for automated EIG access")
        except Exception as e:
            print(f"❌ Error saving session: {e}")
        
        print()
        print("🎉 Setup complete!")
        print("   You can now run the EIG workflow scripts with your saved session.")
        print("   If you need to login again in the future, run this script again.")
        
        # Keep browser open for a moment so user can see the final state
        print("   Browser will close in 5 seconds...")
        page.wait_for_timeout(5000)
        
        browser.close()

if __name__ == "__main__":
    login_to_eig() 