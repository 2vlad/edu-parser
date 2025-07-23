#!/usr/bin/env python3
"""Final test of Google Sheets after granting permissions."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_after_permissions():
    """Test Google Sheets after granting permissions."""
    
    print("🧪 FINAL GOOGLE SHEETS TEST")
    print("=" * 40)
    
    try:
        from core.google_sheets import GoogleSheetsSync, sync_to_sheets
        
        print("1️⃣ Testing service availability...")
        sheets = GoogleSheetsSync()
        
        if sheets.is_available():
            print("✅ Service is available")
        else:
            print("❌ Service not available")
            return
        
        print("\n2️⃣ Testing sheet creation...")
        sheet_id = sheets.get_or_create_sheet("Test_Sheet")
        
        if sheet_id:
            print(f"✅ Sheet created/found: {sheet_id}")
        else:
            print("❌ Failed to create sheet")
            return
        
        print("\n3️⃣ Testing data sync...")
        result = sync_to_sheets()
        
        if result:
            print("✅ Data synced successfully!")
            print("\n🎉 Google Sheets integration is fully working!")
            print(f"📊 Check your spreadsheet:")
            print(f"   https://docs.google.com/spreadsheets/d/{sheets.spreadsheet_id}/edit")
        else:
            print("⚠️ Sync skipped (no data found for today)")
            print("This is normal if no scrapers have run today.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("- Make sure you shared the spreadsheet with the service account")
        print("- Verify the service account has Editor permissions")
        print("- Check that GOOGLE_CREDENTIALS_JSON and GOOGLE_SPREADSHEET_ID are set")

if __name__ == "__main__":
    test_after_permissions()