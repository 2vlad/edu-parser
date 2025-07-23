#!/usr/bin/env python3
"""
Safely sync only today's data without touching previous days.
"""

import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.dynamic_sheets import DynamicSheetsManager
from core.logging_config import setup_logging, get_logger

# Set up logging
setup_logging(log_level="INFO")
logger = get_logger(__name__)


def main():
    """Safely sync only today's data."""
    
    print("🔒 SAFE SYNC - TODAY'S DATA ONLY")
    print("=" * 40)
    
    manager = DynamicSheetsManager()
    
    if not manager.is_available():
        print("❌ Google Sheets service not available")
        return
        
    print("✅ Google Sheets service initialized")
    
    # Get today's date
    today = date.today()
    today_str = today.isoformat()
    
    # Format date for column header
    months = ['янв', 'фев', 'мар', 'апр', 'май', 'июн',
             'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']
    formatted_date = f"{today.day} {months[today.month - 1]}"
    
    print(f"\n📅 Syncing ONLY today's data: {formatted_date} ({today_str})")
    print("⚠️  Previous days' data will remain untouched")
    
    # Check current sheet structure
    data = manager.get_sheet_data()
    if data and len(data) > 0:
        header = data[0]
        print(f"\n📊 Current sheet structure:")
        for i, col in enumerate(header[:10]):
            if col.strip():
                print(f"  Column {i}: {col}")
    
    # Find today's column
    today_column_index = manager.find_date_column(formatted_date)
    
    if today_column_index is not None:
        print(f"\n📍 Found today's column at index: {today_column_index}")
        
        # Confirm before proceeding
        response = input(f"\n❓ Update ONLY column '{formatted_date}' with fresh data from database? (y/N): ")
        
        if response.lower() != 'y':
            print("❌ Operation cancelled")
            return
            
        # Update only today's data
        print(f"\n🔄 Updating data for {formatted_date}...")
        
        if manager.update_daily_data(today_str):
            print(f"✅ Successfully updated today's data")
            print("✅ Previous days' data preserved")
        else:
            print("❌ Failed to update today's data")
            
    else:
        print(f"\n❓ Column for {formatted_date} not found. Create it?")
        response = input("Create new column and sync data? (y/N): ")
        
        if response.lower() != 'y':
            print("❌ Operation cancelled")
            return
            
        # Create column and sync data
        if manager.update_daily_data(today_str):
            print(f"✅ Created column and synced data for {formatted_date}")
        else:
            print("❌ Failed to create column and sync data")
    
    print(f"\n🔗 Check your sheet: https://docs.google.com/spreadsheets/d/{os.environ.get('GOOGLE_SPREADSHEET_ID')}/edit")
    print("\n📝 Note: This script only modifies today's column, leaving all other data intact.")


if __name__ == "__main__":
    main()