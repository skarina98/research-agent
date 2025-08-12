from playwright.sync_api import sync_playwright
import os
import time

def create_session_robust():
    """
    Create a session file by logging into the EIG website with better verification.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Run in visible mode so you can log in
        context = browser.new_context()
        page = context.new_page()
        
        print("Opening EIG login page...")
        page.goto("https://www.eigpropertyauctions.co.uk/account/log-in")
        page.wait_for_timeout(2000)
        
        print("Please log in manually in the browser window that opened.")
        print("After logging in successfully, we'll verify the authentication.")
        print("Press Enter when you have logged in...")
        
        input("Press Enter after logging in...")
        
        # Wait a bit for any redirects
        time.sleep(3)
        
        # Check if we're still on the login page
        current_url = page.url
        print(f"Current URL: {current_url}")
        
        if "log-in" in current_url.lower():
            print("Still on login page. Please complete the login process.")
            input("Press Enter when you have logged in...")
            time.sleep(3)
            current_url = page.url
            print(f"Current URL after second attempt: {current_url}")
        
        # Try to navigate to the auction results page to verify authentication
        print("Testing authentication by navigating to auction results...")
        try:
            page.goto("https://www.eigpropertyauctions.co.uk/clients/auctions/results?SelectedAuctioneerId=680")
            page.wait_for_timeout(3000)
            
            print(f"Page title: {page.title()}")
            print(f"Page URL: {page.url}")
            
            # Check if we're still being redirected to login
            if "login" in page.title().lower() or "log-in" in page.url.lower():
                print("Still being redirected to login. Authentication may not be complete.")
                print("Please ensure you're fully logged in and try again.")
                input("Press Enter to continue anyway...")
            else:
                print("Authentication successful! Can access auction results.")
                
        except Exception as e:
            print(f"Error testing authentication: {e}")
        
        # Save the session regardless
        session_dir = "sessions"
        if not os.path.exists(session_dir):
            os.makedirs(session_dir)
        
        session_file = os.path.join(session_dir, "eig.json")
        context.storage_state(path=session_file)
        
        print(f"Session saved to: {session_file}")
        print("You can now use this session file for automated access.")
        
        # Test the session immediately
        print("Testing the saved session...")
        test_context = browser.new_context(storage_state=session_file)
        test_page = test_context.new_page()
        
        try:
            test_page.goto("https://www.eigpropertyauctions.co.uk/clients/auctions/results?SelectedAuctioneerId=680")
            test_page.wait_for_timeout(3000)
            print(f"Test page title: {test_page.title()}")
            print(f"Test page URL: {test_page.url}")
            
            if "login" not in test_page.title().lower():
                print("✅ Session test successful!")
            else:
                print("❌ Session test failed - still redirecting to login")
                
        except Exception as e:
            print(f"Error testing session: {e}")
        
        test_context.close()
        context.close()
        browser.close()

if __name__ == "__main__":
    create_session_robust() 