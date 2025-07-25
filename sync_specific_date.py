#!/usr/bin/env python3
"""
Safely sync data for a specific date to Google Sheets.
This script will update only the specified date column without affecting other data.
"""

import sys
import os
from datetime import datetime, date
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.dynamic_sheets import DynamicSheetsManager
from core.logging_config import setup_logging, get_logger
from core.storage import Storage

# Set up logging
setup_logging(log_level="INFO")
logger = get_logger(__name__)


def main():
    """Safely sync data for a specific date."""
    
    parser = argparse.ArgumentParser(description='Sync specific date to Google Sheets')
    parser.add_argument('--date', '-d', 
                       help='Date in YYYY-MM-DD format (e.g., 2025-07-24)', 
                       required=True)
    parser.add_argument('--force', '-f', 
                       action='store_true',
                       help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    # Validate date format
    try:
        target_date_obj = datetime.strptime(args.date, '%Y-%m-%d')
        target_date = args.date
    except ValueError:
        print("❌ Invalid date format. Use YYYY-MM-DD (e.g., 2025-07-24)")
        return 1
    
    # Format date for display
    months = ['янв', 'фев', 'мар', 'апр', 'май', 'июн',
             'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']
    formatted_date = f"{target_date_obj.day} {months[target_date_obj.month - 1]}"
    
    print("🔒 SAFE DATE-SPECIFIC SYNC")
    print("=" * 40)
    print(f"📅 Target date: {formatted_date} ({target_date})")
    
    # Check if we have data for this date in database
    storage = Storage()
    result = storage.client.table('applicant_counts')\
        .select('count()')\
        .eq('date', target_date)\
        .eq('status', 'success')\
        .execute()
    
    if not result.data or result.data[0]['count'] == 0:
        print(f"❌ No data found in database for {target_date}")
        print("   Make sure scrapers have run for this date first.")
        return 1
    
    record_count = result.data[0]['count']
    print(f"✅ Found {record_count} records in database for {target_date}")
    
    # Initialize Google Sheets manager
    manager = DynamicSheetsManager()
    
    if not manager.is_available():
        print("❌ Google Sheets service not available")
        return 1
        
    print("✅ Google Sheets service initialized")
    
    # Check current sheet structure
    data = manager.get_sheet_data()
    if data and len(data) > 0:
        header = data[0]
        print(f"\\n📊 Current sheet structure:")
        for i, col in enumerate(header[:10]):
            if col.strip():
                print(f"  Column {chr(ord('A') + i)}: {col}")
    
    # Find target date column
    target_column_index = manager.find_date_column(formatted_date)
    
    if target_column_index is not None:
        column_letter = chr(ord('A') + target_column_index)
        print(f"\\n📍 Found target column at {column_letter} (index {target_column_index})")
    else:
        print(f"\\n❓ Column for {formatted_date} not found.")
        if not args.force:
            response = input("Create new column and sync data? (y/N): ")
            if response.lower() != 'y':
                print("❌ Operation cancelled")
                return 1
    
    # Confirm operation
    if not args.force:
        print(f"\\n⚠️  This will:")
        print(f"   • Clear existing data in {formatted_date} column")
        print(f"   • Write fresh data from database ({record_count} records)")
        print(f"   • Preserve all other date columns")
        
        response = input(f"\\n❓ Proceed with sync for {formatted_date}? (y/N): ")
        
        if response.lower() != 'y':
            print("❌ Operation cancelled")
            return 1
    
    # Perform the sync
    print(f"\\n🔄 Syncing data for {formatted_date}...")
    
    if manager.update_daily_data(target_date):
        print(f"✅ Successfully synced data for {formatted_date}")
        print(f"✅ All other date columns preserved")
        print(f"\\n🔗 Check your sheet: https://docs.google.com/spreadsheets/d/{os.environ.get('GOOGLE_SPREADSHEET_ID')}/edit")
        return 0
    else:
        print(f"❌ Failed to sync data for {formatted_date}")
        print("   Check the logs for detailed error information")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)