#!/usr/bin/env python3
"""
Update the web app URL for the Google Apps Script
"""

import os

def update_webapp_url():
    """Update the web app URL in sheets_webapp.py"""
    
    print("🔧 Update Google Apps Script Web App URL")
    print("=" * 50)
    
    print("📋 Instructions:")
    print("1. Go to Google Apps Script: https://script.google.com/")
    print("2. Open your project (Property Data Management)")
    print("3. Deploy > New deployment")
    print("4. Choose 'Web app' as type")
    print("5. Set access to 'Anyone'")
    print("6. Deploy")
    print("7. Copy the new web app URL")
    print()
    
    # Get the new URL from user
    new_url = input("🔗 Enter your new Google Apps Script web app URL: ").strip()
    
    if not new_url:
        print("❌ No URL provided. Exiting.")
        return
    
    if not new_url.startswith("https://script.google.com/macros/s/"):
        print("⚠️ Warning: URL doesn't look like a Google Apps Script web app URL")
        print("   Expected format: https://script.google.com/macros/s/.../exec")
    
    # Update the sheets_webapp.py file
    try:
        with open("sheets_webapp.py", "r") as f:
            content = f.read()
        
        # Replace the placeholder URL
        updated_content = content.replace(
            'self.webapp_url = webapp_url or "YOUR_NEW_WEBAPP_URL_HERE"  # Replace with your updated Google Apps Script web app URL',
            f'self.webapp_url = webapp_url or "{new_url}"'
        )
        
        with open("sheets_webapp.py", "w") as f:
            f.write(updated_content)
        
        print("✅ Successfully updated sheets_webapp.py with new web app URL")
        print(f"🔗 New URL: {new_url}")
        
        # Test the connection
        print("\n🧪 Testing the new web app URL...")
        test_connection(new_url)
        
    except Exception as e:
        print(f"❌ Error updating file: {e}")

def test_connection(webapp_url):
    """Test the web app connection"""
    try:
        import requests
        import json
        
        # Test payload
        test_payload = {
            "token": "3c4ebe48f035fd3f68ccd5c9f619d7aa3f686d2d7637dc54324d979acc066feb",
            "action": "read"
        }
        
        print(f"🌐 Testing connection to: {webapp_url}")
        response = requests.post(webapp_url, json=test_payload, timeout=30)
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get('ok'):
                    print("✅ Connection successful! Web app is working correctly.")
                    print(f"📊 Found {result.get('count', 0)} rows in the sheet")
                else:
                    print(f"⚠️ Web app returned error: {result.get('error', 'Unknown error')}")
            except Exception as e:
                print(f"⚠️ Error parsing response: {e}")
        else:
            print(f"❌ HTTP error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")

if __name__ == "__main__":
    update_webapp_url() 