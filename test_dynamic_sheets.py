#!/usr/bin/env python3
"""Test dynamic Google Sheets functionality."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_dynamic_sheets():
    """Test dynamic sheets after sharing spreadsheet with service account."""
    
    print("🧪 TESTING DYNAMIC GOOGLE SHEETS")
    print("=" * 45)
    
    try:
        from core.dynamic_sheets import DynamicSheetsManager, update_dynamic_sheets
        
        print("1️⃣ Testing service availability...")
        manager = DynamicSheetsManager()
        
        if manager.is_available():
            print("✅ Dynamic Sheets service is available")
        else:
            print("❌ Dynamic Sheets service not available")
            print("Make sure GOOGLE_CREDENTIALS_JSON and GOOGLE_SPREADSHEET_ID are set")
            return
        
        print("\n2️⃣ Testing sheet data access...")
        data = manager.get_sheet_data()
        
        if data:
            print(f"✅ Sheet data retrieved: {len(data)} rows")
            if len(data) > 0:
                print(f"   Header row: {data[0][:5]}...")  # First 5 columns
        else:
            print("❌ Could not retrieve sheet data")
            return
        
        print("\n3️⃣ Testing date column detection...")
        from datetime import datetime
        today = datetime.now()
        months = ['янв', 'фев', 'мар', 'апр', 'май', 'июн',
                 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']
        formatted_date = f"{today.day} {months[today.month - 1]}"
        
        column_index = manager.find_date_column(formatted_date)
        if column_index is not None:
            print(f"✅ Found existing column for '{formatted_date}' at index {column_index}")
        else:
            print(f"⚠️ No existing column for '{formatted_date}' - will be created")
        
        print("\n4️⃣ Testing programs mapping...")
        programs_mapping = manager.get_programs_mapping()
        
        if programs_mapping:
            print(f"✅ Programs mapping retrieved: {len(programs_mapping)} programs")
            # Show first few programs
            for i, (key, row) in enumerate(programs_mapping.items()):
                if i < 3:
                    print(f"   {key} -> row {row}")
                elif i == 3:
                    print(f"   ... and {len(programs_mapping) - 3} more")
                    break
        else:
            print("❌ No programs mapping found - check sheet structure")
            return
        
        print("\n5️⃣ Testing daily data update...")
        success = update_dynamic_sheets()
        
        if success:
            print("✅ Daily data update completed successfully!")
            print(f"\n🎉 Dynamic Google Sheets integration is working!")
            print(f"📊 Check your spreadsheet for today's column:")
            print(f"   https://docs.google.com/spreadsheets/d/{manager.spreadsheet_id}/edit")
        else:
            print("⚠️ Daily data update skipped (no data for today or other issue)")
            print("This is normal if no scrapers have run today.")
        
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("Run: pip install google-api-python-client google-auth")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("- Make sure you shared the spreadsheet with the service account")
        print("- Verify the service account has Editor permissions")
        print("- Check that the sheet has the correct structure:")
        print("  Column A: вуз")
        print("  Column B: программа") 
        print("  Column C: URL")
        print("  Columns D+: date columns")

if __name__ == "__main__":
    test_dynamic_sheets()