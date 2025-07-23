#!/usr/bin/env python3
"""
Fix Google Sheets columns order and sync missing data.
"""

import sys
import os
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.dynamic_sheets import DynamicSheetsManager
from core.logging_config import setup_logging, get_logger

# Set up logging
setup_logging(log_level="INFO")
logger = get_logger(__name__)


def main():
    """Fix columns order and sync data."""
    
    print("🔧 FIXING GOOGLE SHEETS COLUMNS ORDER")
    print("=" * 50)
    
    manager = DynamicSheetsManager()
    
    if not manager.is_available():
        print("❌ Google Sheets service not available")
        return
        
    print("✅ Google Sheets service initialized")
    
    # Step 1: Cleanup and reorganize columns
    print("\n📊 Reorganizing columns in reverse chronological order...")
    
    if manager.cleanup_and_reorganize_columns():
        print("✅ Columns reorganized successfully")
    else:
        print("❌ Failed to reorganize columns")
        return
    
    # Step 2: Sync data for the last few days
    print("\n📅 Syncing data for recent days...")
    
    days_to_sync = [
        date.today(),  # Today (23 июля)
        date.today() - timedelta(days=1),  # Yesterday (22 июля)
        date.today() - timedelta(days=2),  # 21 июля
    ]
    
    for sync_date in days_to_sync:
        date_str = sync_date.isoformat()
        print(f"\n🔄 Syncing data for {date_str}...")
        
        if manager.update_daily_data(date_str):
            print(f"✅ Successfully synced data for {date_str}")
        else:
            print(f"⚠️ Failed to sync data for {date_str}")
    
    print("\n✨ DONE! Check your Google Sheets")
    print(f"🔗 https://docs.google.com/spreadsheets/d/{os.environ.get('GOOGLE_SPREADSHEET_ID')}/edit")


if __name__ == "__main__":
    main()