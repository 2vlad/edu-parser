#!/usr/bin/env python3
"""
Resync today's data from database to Google Sheets.
"""

import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.dynamic_sheets import DynamicSheetsManager
from core.storage import Storage
from core.logging_config import setup_logging, get_logger

# Set up logging
setup_logging(log_level="INFO")
logger = get_logger(__name__)


def clear_column_data(manager, column_index):
    """Clear all data in a column except the header."""
    try:
        # Get current sheet data to determine number of rows
        data = manager.get_sheet_data()
        if not data or len(data) <= 1:
            return True
            
        num_rows = len(data)
        column_letter = chr(ord('A') + column_index)
        
        # Clear data from row 2 to the last row
        clear_range = f"{manager.master_sheet_name}!{column_letter}2:{column_letter}{num_rows}"
        
        # Clear the range
        manager.service.spreadsheets().values().clear(
            spreadsheetId=manager.spreadsheet_id,
            range=clear_range
        ).execute()
        
        logger.info(f"Cleared data in column {column_letter} (index {column_index})")
        return True
        
    except Exception as e:
        logger.error(f"Failed to clear column data: {e}")
        return False


def main():
    """Resync today's data from database."""
    
    print("🔄 RESYNCING TODAY'S DATA FROM DATABASE")
    print("=" * 50)
    
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
    
    print(f"\n📅 Resyncing data for: {formatted_date} ({today_str})")
    
    # Find the column for today
    column_index = manager.find_date_column(formatted_date)
    
    if column_index is None:
        print(f"❌ Column for {formatted_date} not found")
        return
        
    print(f"📍 Found column at index: {column_index}")
    
    # Clear existing data in the column
    print("🧹 Clearing old data...")
    if not clear_column_data(manager, column_index):
        print("❌ Failed to clear old data")
        return
        
    # Get fresh data from database
    storage = Storage()
    result = storage.client.table('applicant_counts')\
        .select('*')\
        .eq('date', today_str)\
        .eq('status', 'success')\
        .order('name')\
        .execute()
    
    if not result.data:
        print(f"❌ No data found in database for {today_str}")
        return
        
    print(f"📊 Found {len(result.data)} records in database")
    
    # Get programs mapping
    programs_mapping = manager.get_programs_mapping()
    
    # Prepare updates
    updates = []
    updated_count = 0
    missing_programs = []
    
    for record in result.data:
        # Determine university and create key
        scraper_id = record['scraper_id']
        if scraper_id.startswith('hse_'):
            university = 'НИУ ВШЭ'
        elif scraper_id.startswith('mipt_'):
            university = 'МФТИ'
        elif scraper_id.startswith('mephi_'):
            university = 'МИФИ'
        else:
            university = 'Unknown'
        
        program_name = record.get('name', record['scraper_id'])
        
        # Clean program name
        if program_name.startswith('HSE - '):
            program_name = program_name[6:]
        elif program_name.startswith('МФТИ - '):
            program_name = program_name[7:]
        elif program_name.startswith('НИЯУ МИФИ - '):
            program_name = program_name[12:]
        
        program_key = f"{university} - {program_name}"
        
        # Find row for this program
        row_index = programs_mapping.get(program_key)
        if row_index is None:
            missing_programs.append(program_key)
            continue
        
        # Convert column index to letter
        column_letter = chr(ord('A') + column_index)
        range_name = f"{manager.master_sheet_name}!{column_letter}{row_index}"
        
        # Add update
        updates.append({
            'range': range_name,
            'values': [[record.get('count', 0)]]
        })
        updated_count += 1
        
        # Show progress for first few
        if updated_count <= 5:
            print(f"  • {program_key}: {record.get('count', 0)}")
    
    if updated_count > 5:
        print(f"  ... and {updated_count - 5} more programs")
    
    # Apply all updates in batch
    if updates:
        print(f"\n📝 Updating {updated_count} programs...")
        
        manager.service.spreadsheets().values().batchUpdate(
            spreadsheetId=manager.spreadsheet_id,
            body={
                'valueInputOption': 'RAW',
                'data': updates
            }
        ).execute()
        
        print(f"✅ Successfully updated {updated_count} programs")
    else:
        print("❌ No programs to update")
    
    if missing_programs:
        print(f"\n⚠️ Found {len(missing_programs)} programs not in sheet:")
        for prog in missing_programs[:5]:
            print(f"  - {prog}")
        if len(missing_programs) > 5:
            print(f"  ... and {len(missing_programs) - 5} more")
    
    print("\n✨ DONE! Fresh data from database has been synced")
    print(f"🔗 https://docs.google.com/spreadsheets/d/{os.environ.get('GOOGLE_SPREADSHEET_ID')}/edit")


if __name__ == "__main__":
    main()