#!/usr/bin/env python3
"""
Verify that all programs with data in database are properly synced to Google Sheets.
This script should be run after automatic scraper runs to ensure data integrity.
"""

import sys
import os
from datetime import datetime, date
from typing import Dict, List, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.dynamic_sheets import DynamicSheetsManager
from core.storage import Storage
from core.logging_config import setup_logging, get_logger

# Set up logging
setup_logging(log_level="INFO")
logger = get_logger(__name__)


def create_program_key(scraper_id, name):
    """Create program key exactly as done in dynamic_sheets.py sync logic."""
    
    # Determine university from scraper_id
    if scraper_id.startswith('hse_'):
        university = 'НИУ ВШЭ'
    elif scraper_id.startswith('mipt_'):
        university = 'МФТИ'
    elif scraper_id.startswith('mephi_'):
        university = 'МИФИ'
    else:
        university = 'Unknown'
    
    program_name = name
    
    # Clean program name - remove university prefix if present
    if program_name.startswith('HSE - '):
        program_name = program_name[6:]  # Remove "HSE - "
    elif program_name.startswith('МФТИ - '):
        program_name = program_name[7:]  # Remove "МФТИ - "
    elif program_name.startswith('НИЯУ МИФИ - '):
        program_name = program_name[12:]  # Remove "НИЯУ МИФИ - "
    elif program_name.startswith('МИФИ - '):
        program_name = program_name[7:]  # Remove "МИФИ - "
    elif program_name.startswith('MEPhI - '):
        program_name = program_name[8:]  # Remove "MEPhI - "
    
    program_key = f"{university} - {program_name}"
    return program_key


def main():
    """Verify Google Sheets sync after scraper run."""
    
    target_date = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()
    
    print("🔍 GOOGLE SHEETS SYNC VERIFICATION")
    print("=" * 50)
    print(f"📅 Checking date: {target_date}")
    
    # Initialize components
    try:
        manager = DynamicSheetsManager()
        
        if not manager.is_available():
            print("❌ Google Sheets service not available")
            logger.error("Google Sheets service not available for verification")
            return 1
            
        storage = Storage()
        logger.info("Verification components initialized successfully")
        
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        logger.error(f"Failed to initialize verification components: {e}")
        return 1
    
    # Get data from database for target date
    try:
        db_result = storage.client.table('applicant_counts')\
            .select('scraper_id, name, count, status')\
            .eq('date', target_date)\
            .eq('status', 'success')\
            .execute()
        
        if not db_result.data:
            print(f"❌ No successful data found in database for {target_date}")
            logger.warning(f"No database data found for {target_date}")
            return 1
            
        print(f"📊 Found {len(db_result.data)} successful records in database")
        logger.info(f"Found {len(db_result.data)} database records for {target_date}")
        
    except Exception as e:
        print(f"❌ Failed to fetch database data: {e}")
        logger.error(f"Failed to fetch database data: {e}")
        return 1
    
    # Create mapping of database data
    db_programs = {}
    for record in db_result.data:
        scraper_id = record['scraper_id']
        name = record['name']
        count = record['count']
        
        program_key = create_program_key(scraper_id, name)
        db_programs[program_key] = {
            'scraper_id': scraper_id,
            'name': name,
            'count': count,
            'db_count': count
        }
    
    print(f"✅ Processed {len(db_programs)} unique programs from database")
    
    # Get data from Google Sheets
    try:
        sheet_data = manager.get_sheet_data()
        if not sheet_data or len(sheet_data) < 2:
            print("❌ No data found in Google Sheets")
            logger.error("No Google Sheets data found")
            return 1
            
        print(f"📋 Found {len(sheet_data)} rows in Google Sheets")
        
    except Exception as e:
        print(f"❌ Failed to read Google Sheets: {e}")
        logger.error(f"Failed to read Google Sheets: {e}")
        return 1
    
    # Find target date column
    header = sheet_data[0]
    date_obj = datetime.strptime(target_date, '%Y-%m-%d')
    months = ['янв', 'фев', 'мар', 'апр', 'май', 'июн',
             'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']
    formatted_date = f"{date_obj.day} {months[date_obj.month - 1]}"
    
    target_column_index = None
    for i, col_header in enumerate(header):
        if col_header.strip() == formatted_date:
            target_column_index = i
            break
    
    if target_column_index is None:
        print(f"❌ Column '{formatted_date}' not found in Google Sheets")
        logger.error(f"Target date column '{formatted_date}' not found in sheets")
        return 1
        
    print(f"📍 Found target column '{formatted_date}' at index {target_column_index}")
    
    # Extract sheets data for target date
    sheets_programs = {}
    missing_in_sheets = []
    data_mismatches = []
    
    for row_idx, row in enumerate(sheet_data[1:], start=2):
        if len(row) < 2:
            continue
            
        university = row[0].strip() if len(row) > 0 else ""
        program = row[1].strip() if len(row) > 1 else ""
        
        if not university or not program:
            continue
            
        program_key = f"{university} - {program}"
        
        # Get count from target column
        sheets_count = None
        if target_column_index < len(row):
            cell_value = str(row[target_column_index]).strip()
            if cell_value and cell_value != '-':
                try:
                    sheets_count = int(cell_value)
                except ValueError:
                    sheets_count = None
        
        sheets_programs[program_key] = {
            'row': row_idx,
            'university': university,
            'program': program,
            'sheets_count': sheets_count
        }
    
    print(f"✅ Processed {len(sheets_programs)} programs from Google Sheets")
    
    # Compare database vs sheets
    print(f"\\n🔍 COMPARISON RESULTS:")
    print("-" * 50)
    
    perfect_matches = 0
    missing_in_sheets = 0
    count_mismatches = 0
    extra_in_sheets = 0
    
    # Check each database program
    for db_key, db_info in db_programs.items():
        if db_key in sheets_programs:
            sheets_info = sheets_programs[db_key]
            db_count = db_info['db_count']
            sheets_count = sheets_info['sheets_count']
            
            if sheets_count == db_count:
                perfect_matches += 1
                logger.debug(f"✅ Perfect match: {db_key} = {db_count}")
            else:
                count_mismatches += 1
                print(f"⚠️  Count mismatch: {db_key}")
                print(f"    Database: {db_count}, Sheets: {sheets_count}")
                logger.warning(f"Count mismatch for {db_key}: DB={db_count}, Sheets={sheets_count}")
        else:
            missing_in_sheets += 1
            print(f"❌ Missing in sheets: {db_key} (count: {db_info['db_count']})")
            logger.error(f"Program missing in sheets: {db_key}")
    
    # Check for extra programs in sheets
    for sheets_key, sheets_info in sheets_programs.items():
        if sheets_key not in db_programs and sheets_info['sheets_count'] is not None:
            extra_in_sheets += 1
            print(f"➕ Extra in sheets: {sheets_key} (count: {sheets_info['sheets_count']})")
            logger.warning(f"Extra program in sheets: {sheets_key}")
    
    # Summary
    print(f"\\n📊 VERIFICATION SUMMARY:")
    print(f"   ✅ Perfect matches: {perfect_matches}")
    print(f"   ⚠️  Count mismatches: {count_mismatches}")
    print(f"   ❌ Missing in sheets: {missing_in_sheets}")
    print(f"   ➕ Extra in sheets: {extra_in_sheets}")
    print(f"   📋 Total DB programs: {len(db_programs)}")
    print(f"   📋 Total sheet programs: {len([p for p in sheets_programs.values() if p['sheets_count'] is not None])}")
    
    # Log summary
    logger.info(f"Sync verification complete: {perfect_matches} perfect, {count_mismatches} mismatched, {missing_in_sheets} missing")
    
    # Determine overall status
    if missing_in_sheets == 0 and count_mismatches == 0:
        print(f"\\n🎉 SYNC VERIFICATION: PERFECT!")
        print(f"All {perfect_matches} programs are correctly synced to Google Sheets")
        logger.info("✅ Sync verification: PERFECT - all data synced correctly")
        return 0
    elif missing_in_sheets == 0:
        print(f"\\n✅ SYNC VERIFICATION: GOOD")
        print(f"All programs present, but {count_mismatches} have count differences")
        logger.warning(f"Sync verification: GOOD - all present but {count_mismatches} count mismatches")
        return 0
    else:
        print(f"\\n❌ SYNC VERIFICATION: ISSUES FOUND")
        print(f"Missing programs or count mismatches detected")
        print(f"Consider running manual sync or checking program name formatting")
        logger.error(f"Sync verification: FAILED - {missing_in_sheets} missing programs")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)