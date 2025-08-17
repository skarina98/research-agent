#!/usr/bin/env python3
"""
PropertyEngine Login Session Manager
"""

import os
import json
from playwright.sync_api import sync_playwright
import time

class PropertyEngineLogin:
    def __init__(self):
        """Initialize PropertyEngine login manager"""
        self.session_file = "sessions/propertyengine.json"
        self.credentials_file = "credentials/propertyengine.json"
        
        # Create sessions directory if it doesn't exist
        os.makedirs("sessions", exist_ok=True)
        os.makedirs("credentials", exist_ok=True)
    
    def load_credentials(self):
        """Load PropertyEngine credentials"""
        try:
            if os.path.exists(self.credentials_file):
                with open(self.credentials_file, 'r') as f:
                    credentials = json.load(f)
                return credentials.get('email')
            else:
                print("❌ PropertyEngine credentials file not found!")
                print(f"   Please create: {self.credentials_file}")
                print("   Format:")
                print("   {")
                print('     "email": "your-email@example.com"')
                print("   }")
                return None
        except Exception as e:
            print(f"❌ Error loading credentials: {e}")
            return None
    
    def login(self):
        """Login to PropertyEngine and save session"""
        print("🔐 PropertyEngine Login")
        print("=" * 30)
        
        # Load credentials
        email = self.load_credentials()
        if not email:
            return False
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            
            try:
                # Navigate to PropertyEngine login page
                print("🌐 Navigating to PropertyEngine...")
                page.goto("https://propertyengine.co.uk/login", wait_until="networkidle")
                time.sleep(3)
                
                print("📋 Page title:", page.title())
                print("🔗 Current URL:", page.url)
                
                # Take screenshot of login page
                page.screenshot(path="propertyengine_login_page.png")
                print("📸 Screenshot saved: propertyengine_login_page.png")
                
                # Look for login form elements
                print("\n🔍 Looking for login form elements...")
                
                # Try to find email/username field
                email_selectors = [
                    'input[type="email"]',
                    'input[name="email"]',
                    'input[name="username"]',
                    'input[placeholder*="email"]',
                    'input[placeholder*="Email"]',
                    'input[placeholder*="username"]',
                    'input[placeholder*="Username"]',
                    'input[placeholder*="Email or username"]'
                ]
                
                email_field = None
                for selector in email_selectors:
                    email_field = page.query_selector(selector)
                    if email_field:
                        print(f"   ✅ Found email field with selector: {selector}")
                        break
                
                if not email_field:
                    print("   ❌ Could not find email field")
                    return False
                
                print(f"   ✅ Found email field with selector: {selector}")
                print(f"   Placeholder: {email_field.get_attribute('placeholder')}")
                print(f"   Type: {email_field.get_attribute('type')}")
                print(f"   Name: {email_field.get_attribute('name')}")
                
                # Fill in email
                print("📝 Filling in email...")
                email_field.fill("")
                email_field.type(email)
                time.sleep(1)
                
                # Look for submit/send code button
                submit_selectors = [
                    'button[type="submit"]',
                    'input[type="submit"]',
                    'button:has-text("Send Code")',
                    'button:has-text("Send")',
                    'button:has-text("Submit")',
                    'button:has-text("Continue")',
                    'button:has-text("Next")',
                    'button'
                ]
                
                submit_button = None
                for selector in submit_selectors:
                    submit_button = page.query_selector(selector)
                    if submit_button:
                        button_text = submit_button.text_content().strip()
                        if any(word in button_text.lower() for word in ['send', 'submit', 'continue', 'next']):
                            print(f"   ✅ Found submit button with selector: {selector}")
                            print(f"   Button text: '{button_text}'")
                            break
                
                if not submit_button:
                    print("   ❌ Could not find submit button")
                    return False
                
                # Click submit button to send code
                print("🖱️ Clicking submit button to send verification code...")
                submit_button.click()
                time.sleep(3)
                
                # Wait for user to enter verification code
                print("📱 Please check your email for the verification code")
                print("   Enter the code in the browser window that opened")
                print("   The script will wait for you to complete the login...")
                
                # Wait for user to complete login manually
                input("   Press Enter when you've completed the login in the browser...")
                
                # Check if login was successful
                print("🔍 Checking login status...")
                current_url = page.url
                page_title = page.title()
                
                print(f"   Current URL: {current_url}")
                print(f"   Page title: {page_title}")
                
                # Look for indicators of successful login
                page_text = page.locator("body").text_content()
                
                # Check for login success indicators
                success_indicators = [
                    'dashboard',
                    'welcome',
                    'logout',
                    'profile',
                    'account',
                    'property',
                    'search'
                ]
                
                # Check for login failure indicators
                failure_indicators = [
                    'invalid',
                    'incorrect',
                    'failed',
                    'error',
                    'login',
                    'code'
                ]
                
                login_successful = False
                for indicator in success_indicators:
                    if indicator.lower() in page_text.lower() or indicator.lower() in page_title.lower():
                        login_successful = True
                        print(f"   ✅ Login success indicator found: {indicator}")
                        break
                
                if not login_successful:
                    for indicator in failure_indicators:
                        if indicator.lower() in page_text.lower():
                            print(f"   ❌ Login failure indicator found: {indicator}")
                            break
                
                if login_successful:
                    print("✅ Login successful!")
                    
                    # Take screenshot of logged-in page
                    page.screenshot(path="propertyengine_logged_in.png")
                    print("📸 Screenshot saved: propertyengine_logged_in.png")
                    
                    # Save session state
                    print("💾 Saving session state...")
                    context.storage_state(path=self.session_file)
                    print(f"   Session saved to: {self.session_file}")
                    
                    return True
                else:
                    print("❌ Login failed or status unclear")
                    return False
                

                
                # Check if login was successful
                print("🔍 Checking login status...")
                current_url = page.url
                page_title = page.title()
                
                print(f"   Current URL: {current_url}")
                print(f"   Page title: {page_title}")
                
                # Look for indicators of successful login
                page_text = page.locator("body").text_content()
                
                # Check for login success indicators
                success_indicators = [
                    'dashboard',
                    'welcome',
                    'logout',
                    'profile',
                    'account'
                ]
                
                # Check for login failure indicators
                failure_indicators = [
                    'invalid',
                    'incorrect',
                    'failed',
                    'error',
                    'login'
                ]
                
                login_successful = False
                for indicator in success_indicators:
                    if indicator.lower() in page_text.lower() or indicator.lower() in page_title.lower():
                        login_successful = True
                        print(f"   ✅ Login success indicator found: {indicator}")
                        break
                
                if not login_successful:
                    for indicator in failure_indicators:
                        if indicator.lower() in page_text.lower():
                            print(f"   ❌ Login failure indicator found: {indicator}")
                            break
                
                if login_successful:
                    print("✅ Login successful!")
                    
                    # Take screenshot of logged-in page
                    page.screenshot(path="propertyengine_logged_in.png")
                    print("📸 Screenshot saved: propertyengine_logged_in.png")
                    
                    # Save session state
                    print("💾 Saving session state...")
                    context.storage_state(path=self.session_file)
                    print(f"   Session saved to: {self.session_file}")
                    
                    return True
                else:
                    print("❌ Login failed or status unclear")
                    return False
                
            except Exception as e:
                print(f"❌ Error during login: {e}")
                import traceback
                traceback.print_exc()
                return False
            finally:
                browser.close()
    
    def check_session(self):
        """Check if we have a valid session"""
        return os.path.exists(self.session_file)
    
    def get_session_path(self):
        """Get the path to the session file"""
        return self.session_file if self.check_session() else None

def main():
    """Main function to handle PropertyEngine login"""
    login_manager = PropertyEngineLogin()
    
    if login_manager.check_session():
        print("✅ PropertyEngine session found!")
        print(f"   Session file: {login_manager.get_session_path()}")
        response = input("   Do you want to create a new session? (y/N): ")
        if response.lower() != 'y':
            print("   Using existing session.")
            return True
    
    print("🔐 PropertyEngine Login Required")
    print("=" * 30)
    print("This will open a browser window for you to login to PropertyEngine.")
    print("The session will be saved for future use.")
    print()
    
    response = input("Continue with login? (Y/n): ")
    if response.lower() == 'n':
        print("Login cancelled.")
        return False
    
    success = login_manager.login()
    
    if success:
        print("\n🎉 PropertyEngine login successful!")
        print("   Session saved for future use.")
        return True
    else:
        print("\n❌ PropertyEngine login failed!")
        return False

if __name__ == "__main__":
    main() 