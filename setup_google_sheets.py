#!/usr/bin/env python3
"""
Setup script for Google Sheets integration.

This script helps configure the Google Sheets API credentials and creates
the necessary spreadsheet for data synchronization.
"""

import os
import json
import sys
from dotenv import load_dotenv, set_key

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main setup function."""
    print("🔧 GOOGLE SHEETS INTEGRATION SETUP")
    print("=" * 50)
    
    # Load existing environment
    load_dotenv()
    
    print("\n📋 This setup will help you configure Google Sheets integration.")
    print("You'll need:")
    print("  1. A Google Cloud Project with Sheets API enabled")
    print("  2. A Service Account with JSON credentials")
    print("  3. A Google Spreadsheet ID")
    print()
    
    # Check if already configured
    existing_creds = os.environ.get('GOOGLE_CREDENTIALS_JSON')
    existing_sheet_id = os.environ.get('GOOGLE_SPREADSHEET_ID')
    
    if existing_creds and existing_sheet_id:
        print("✅ Google Sheets integration already configured!")
        print(f"   Spreadsheet ID: {existing_sheet_id}")
        
        choice = input("\nDo you want to reconfigure? (y/N): ").lower()
        if choice != 'y':
            print("Skipping setup.")
            return
    
    print("\n🔧 Configuration Steps:")
    print()
    
    # Step 1: Service Account Credentials
    print("1️⃣ SERVICE ACCOUNT SETUP")
    print("   - Go to: https://console.cloud.google.com/")
    print("   - Create or select a project")
    print("   - Enable Google Sheets API")
    print("   - Create a Service Account")
    print("   - Download the JSON credentials file")
    print()
    
    credentials_path = input("Enter path to your service account JSON file: ").strip()
    
    if not credentials_path or not os.path.exists(credentials_path):
        print("❌ Credentials file not found!")
        return
    
    try:
        with open(credentials_path, 'r') as f:
            credentials_data = json.load(f)
        
        # Validate credentials structure
        required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
        if not all(field in credentials_data for field in required_fields):
            print("❌ Invalid credentials file format!")
            return
        
        credentials_json = json.dumps(credentials_data)
        print("✅ Credentials file loaded successfully")
        
    except Exception as e:
        print(f"❌ Error reading credentials file: {e}")
        return
    
    # Step 2: Spreadsheet Setup
    print("\n2️⃣ SPREADSHEET SETUP")
    print("   - Create a new Google Spreadsheet")
    print("   - Share it with your service account email:")
    print(f"     {credentials_data['client_email']}")
    print("   - Give it Editor permissions")
    print("   - Copy the spreadsheet ID from the URL")
    print("     URL format: https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit")
    print()
    
    spreadsheet_id = input("Enter your Google Spreadsheet ID: ").strip()
    
    if not spreadsheet_id:
        print("❌ Spreadsheet ID required!")
        return
    
    # Step 3: Save to .env file
    print("\n3️⃣ SAVING CONFIGURATION")
    
    env_file = '.env'
    
    try:
        # Set environment variables
        set_key(env_file, 'GOOGLE_CREDENTIALS_JSON', credentials_json)
        set_key(env_file, 'GOOGLE_SPREADSHEET_ID', spreadsheet_id)
        
        print(f"✅ Configuration saved to {env_file}")
        
    except Exception as e:
        print(f"❌ Error saving configuration: {e}")
        return
    
    # Step 4: Test the integration
    print("\n4️⃣ TESTING INTEGRATION")
    
    try:
        from core.google_sheets import GoogleSheetsSync
        
        sheets_sync = GoogleSheetsSync()
        
        if sheets_sync.is_available():
            print("✅ Google Sheets service initialized successfully")
            
            # Test creating a sheet
            test_sheet_name = "Test_Setup"
            sheet_id = sheets_sync.get_or_create_sheet(test_sheet_name)
            
            if sheet_id:
                print(f"✅ Successfully created/accessed test sheet: {test_sheet_name}")
                print(f"   Sheet ID: {sheet_id}")
            else:
                print("❌ Failed to create test sheet")
                return
            
        else:
            print("❌ Google Sheets service not available")
            return
            
    except Exception as e:
        print(f"❌ Error testing integration: {e}")
        return
    
    # Success!
    print("\n🎉 SETUP COMPLETED SUCCESSFULLY!")
    print("=" * 50)
    print("Google Sheets integration is now configured and ready to use.")
    print()
    print("📊 Your data will be automatically synced to Google Sheets after each scraper run.")
    print(f"🔗 Spreadsheet URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
    print()
    print("🚀 To test the sync manually, run:")
    print("   python -c \"from core.google_sheets import sync_to_sheets; sync_to_sheets()\"")


if __name__ == "__main__":
    main()