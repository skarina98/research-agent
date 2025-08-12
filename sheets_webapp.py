#!/usr/bin/env python3
"""
Google Sheets integration using Google Apps Script web app
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class PropertyDataManagerWebApp:
    """Property data manager using Google Apps Script web app"""
    
    def __init__(self, webapp_url=None, shared_token=None):
        """
        Initialize the property data manager
        
        Args:
            webapp_url: Google Apps Script web app URL
            shared_token: Shared token for authentication
        """
        self.webapp_url = webapp_url or "https://script.google.com/macros/s/AKfycbyjCzf8CA1FmK_zY3aaeYkuqXbNHS8Rm9xn7Im2LTRRtr0ftk5xNH44J1z_v7k3pztM/exec"
        self.shared_token = shared_token or os.getenv('GOOGLE_SHEETS_SHARED_TOKEN')
        
        # Fallback to local JSON file
        self.local_data_file = "property_data.json"
        self.property_data = []
        self.load_local_data()
        
        print(f"✅ WebApp Property Data Manager initialized")
        print(f"🌐 WebApp URL: {self.webapp_url}")
        print(f"🔐 Shared Token: {self.shared_token[:10] if self.shared_token else 'None'}...")
    
    def load_local_data(self):
        """Load property data from local JSON file"""
        if os.path.exists(self.local_data_file):
            try:
                with open(self.local_data_file, 'r') as f:
                    self.property_data = json.load(f)
                print(f"📁 Loaded {len(self.property_data)} properties from local file")
            except Exception as e:
                print(f"⚠️ Error loading local data: {e}")
                self.property_data = []
        else:
            self.property_data = []
    
    def save_local_data(self):
        """Save property data to local JSON file"""
        try:
            with open(self.local_data_file, 'w') as f:
                json.dump(self.property_data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving local data: {e}")
    
    def add_property(self, property_data):
        """
        Add a property to the Google Sheet via web app
        
        Args:
            property_data: Dictionary containing property information
            
        Returns:
            Dictionary with status and message
        """
        try:
            # Add timestamp for tracking
            property_data['added_timestamp'] = datetime.now().isoformat()
            
            # Prepare payload for web app in the format expected by the Google Apps Script
            # The script expects: body.rows (array) with specific field names
            script_payload = {
                'token': self.shared_token,
                'rows': [{
                    'auction_name': property_data.get('auction_name', ''),
                    'auction_date': property_data.get('auction_date', ''),
                    'address': property_data.get('address', ''),
                    'auction_sale': property_data.get('auction_sale', ''),
                    'lot_number': property_data.get('lot_number', ''),
                    'postcode': property_data.get('postcode', ''),
                    'purchase_price': property_data.get('purchase_price', ''),
                    'sold_date': property_data.get('sold_date', ''),
                    'owner': '',  # Not provided in our data
                    'guide_price': '',  # Leave guide_price empty as requested
                    'auction_url': property_data.get('auction_url', ''),  # New auction_url field
                    'source_url': '',  # Leave source_url empty as requested
                    'qa_status': 'imported',  # Default status
                    'ingested_at': property_data.get('added_timestamp', datetime.now().isoformat())
                }]
            }
            
            print(f"📤 Sending data to Google Apps Script in correct format...")
            print(f"   Rows count: {len(script_payload['rows'])}")
            print(f"   First row address: {script_payload['rows'][0].get('address', 'Unknown')}")
            
            payload = script_payload
            
            # Send request to web app
            print(f"🌐 Sending request to Google Apps Script web app...")
            print(f"📤 Payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(self.webapp_url, json=payload, timeout=30)
            
            print(f"📥 Response status: {response.status_code}")
            print(f"📥 Response text: {response.text[:500]}...")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"📥 Parsed response: {result}")
                    
                    if result.get('ok'):
                        print(f"✅ Added to Google Sheets via WebApp: {property_data.get('address', 'Unknown')}")
                        
                        # Also add to local data as backup
                        self.property_data.append(property_data)
                        self.save_local_data()
                        
                        return {
                            "status": "success",
                            "action": "added",
                            "message": f"Added property to Google Sheets via WebApp: {property_data.get('address', 'Unknown')}"
                        }
                    else:
                        print(f"⚠️ WebApp returned error: {result}")
                        # Fallback to local storage
                        self.property_data.append(property_data)
                        self.save_local_data()
                        
                        return {
                            "status": "success",
                            "action": "added_local",
                            "message": f"Added property to local storage (WebApp error): {property_data.get('address', 'Unknown')}"
                        }
                except Exception as e:
                    print(f"❌ Error parsing response JSON: {e}")
                    # Fallback to local storage
                    self.property_data.append(property_data)
                    self.save_local_data()
                    
                    return {
                        "status": "success",
                        "action": "added_local",
                        "message": f"Added property to local storage (JSON parse error): {property_data.get('address', 'Unknown')}"
                    }
            else:
                print(f"❌ HTTP error {response.status_code}: {response.text}")
                # Fallback to local storage
                self.property_data.append(property_data)
                self.save_local_data()
                
                return {
                    "status": "success",
                    "action": "added_local",
                    "message": f"Added property to local storage (HTTP error): {property_data.get('address', 'Unknown')}"
                }
                
        except Exception as e:
            print(f"❌ Error adding property: {e}")
            # Fallback to local storage
            self.property_data.append(property_data)
            self.save_local_data()
            
            return {
                "status": "success",
                "action": "added_local",
                "message": f"Added property to local storage (Exception): {property_data.get('address', 'Unknown')}"
            }
    
    def process_property_data(self, property_data):
        """
        Process property data and add to sheets
        
        Args:
            property_data: Dictionary containing property information
            
        Returns:
            Dictionary with status and message
        """
        # Validate required fields - make auction_price optional since it's not always available
        required_fields = [
            'auction_name', 'auction_date', 'address', 
            'lot_number', 'postcode', 'sold_price', 'sold_date', 'auction_url'
        ]
        
        missing_fields = []
        for field in required_fields:
            if not property_data.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            return {
                "status": "error",
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            }
        
        # Add the property
        return self.add_property(property_data)
    
    def get_all_properties(self):
        """Get all properties from local storage"""
        return self.property_data
    
    def clear_local_data(self):
        """Clear local property data"""
        self.property_data = []
        if os.path.exists(self.local_data_file):
            os.remove(self.local_data_file)
        print("🗑️ Local property data cleared") 