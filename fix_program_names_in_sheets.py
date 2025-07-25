#!/usr/bin/env python3
"""
Fix program names in Google Sheets to match database key format exactly.
This will ensure proper synchronization between database and Google Sheets.
"""

import sys
import os
from datetime import datetime

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
    """Fix program names in Google Sheets to match database format."""
    
    print("🔧 FIXING PROGRAM NAMES IN GOOGLE SHEETS")
    print("=" * 50)
    
    # Initialize components
    try:
        manager = DynamicSheetsManager()
        
        if not manager.is_available():
            print("❌ Google Sheets service not available")
            return 1
            
        print("✅ Google Sheets service initialized")
        
        storage = Storage()
        print("✅ Database connection established")
        
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return 1
    
    # Get all scrapers from database
    try:
        result = storage.client.table('scrapers_config')\
            .select('scraper_id, name, enabled')\
            .eq('enabled', True)\
            .execute()
        
        if not result.data:
            print("❌ No enabled scrapers found in database")
            return 1
            
        print(f"📊 Found {len(result.data)} enabled scrapers in database")
        
    except Exception as e:
        print(f"❌ Failed to fetch scrapers: {e}")
        return 1
    
    # Create mapping of correct program keys
    correct_program_keys = {}
    for scraper in result.data:
        scraper_id = scraper['scraper_id']
        name = scraper['name']
        correct_key = create_program_key(scraper_id, name)
        correct_program_keys[scraper_id] = {
            'key': correct_key,
            'name': name,
            'university': correct_key.split(' - ')[0],
            'program': correct_key.split(' - ', 1)[1]
        }
    
    print(f"✅ Generated {len(correct_program_keys)} correct program keys")
    
    # Get current sheet data
    try:
        data = manager.get_sheet_data()
        if not data or len(data) < 2:
            print("❌ No data found in Google Sheets")
            return 1
            
        print(f"📋 Current sheet has {len(data)} rows")
        
    except Exception as e:
        print(f"❌ Failed to read sheet data: {e}")
        return 1
    
    # Analyze current vs correct names
    header = data[0]
    print(f"\\n📊 Sheet structure analysis:")
    print(f"   Headers: {header[:5]}...")
    
    updates_needed = []
    
    # Check each row (skip header)
    for row_idx, row in enumerate(data[1:], start=2):
        if len(row) < 2:
            continue
            
        current_university = row[0].strip() if len(row) > 0 else ""
        current_program = row[1].strip() if len(row) > 1 else ""
        
        if not current_university or not current_program:
            continue
            
        current_key = f"{current_university} - {current_program}"
        
        # Find matching scraper by trying to match the program part
        best_match = None
        for scraper_id, info in correct_program_keys.items():
            # Try exact match first
            if info['key'] == current_key:
                best_match = (scraper_id, info, 'exact')
                break
            # Try program name match
            elif info['program'].lower() == current_program.lower():
                best_match = (scraper_id, info, 'program')
                break
            # Try partial match
            elif current_program.lower() in info['program'].lower() or info['program'].lower() in current_program.lower():
                if not best_match or best_match[2] != 'program':
                    best_match = (scraper_id, info, 'partial')
        
        if best_match:
            scraper_id, correct_info, match_type = best_match
            
            if correct_info['key'] != current_key:
                updates_needed.append({
                    'row': row_idx,
                    'current_university': current_university,
                    'current_program': current_program,
                    'current_key': current_key,
                    'correct_university': correct_info['university'],
                    'correct_program': correct_info['program'],
                    'correct_key': correct_info['key'],
                    'scraper_id': scraper_id,
                    'match_type': match_type
                })
    
    if not updates_needed:
        print("\\n✅ All program names are already correct!")
        return 0
    
    print(f"\\n🔍 Found {len(updates_needed)} programs that need updating:")
    print("-" * 80)
    
    for i, update in enumerate(updates_needed[:10], 1):  # Show first 10
        print(f"{i:2d}. Row {update['row']}: {update['match_type']} match")
        print(f"    Current: {update['current_key']}")
        print(f"    Correct: {update['correct_key']}")
        print(f"    Scraper: {update['scraper_id']}")
        print()
    
    if len(updates_needed) > 10:
        print(f"    ... and {len(updates_needed) - 10} more")
    
    # Confirm before updating
    response = input(f"\\n❓ Update {len(updates_needed)} program names in Google Sheets? (y/N): ")
    
    if response.lower() != 'y':
        print("❌ Operation cancelled")
        return 0
    
    # Perform updates
    print(f"\\n🔄 Updating program names...")
    
    successful_updates = 0
    failed_updates = 0
    
    for update in updates_needed:
        try:
            row_idx = update['row']
            
            # Update university (column A)
            range_a = f"{manager.master_sheet_name}!A{row_idx}"
            manager.service.spreadsheets().values().update(
                spreadsheetId=manager.spreadsheet_id,
                range=range_a,
                valueInputOption='RAW',
                body={'values': [[update['correct_university']]]}
            ).execute()
            
            # Update program name (column B)
            range_b = f"{manager.master_sheet_name}!B{row_idx}"
            manager.service.spreadsheets().values().update(
                spreadsheetId=manager.spreadsheet_id,
                range=range_b,
                valueInputOption='RAW',
                body={'values': [[update['correct_program']]]}
            ).execute()
            
            successful_updates += 1
            print(f"✅ Updated row {row_idx}: {update['correct_key']}")
            
        except Exception as e:
            failed_updates += 1
            print(f"❌ Failed to update row {row_idx}: {e}")
    
    print(f"\\n📊 Update Summary:")
    print(f"   ✅ Successful: {successful_updates}")
    print(f"   ❌ Failed: {failed_updates}")
    print(f"   📋 Total: {len(updates_needed)}")
    
    if successful_updates > 0:
        print(f"\\n🎉 Successfully updated {successful_updates} program names!")
        print("🔗 Check your sheet:")
        print(f"   https://docs.google.com/spreadsheets/d/{os.environ.get('GOOGLE_SPREADSHEET_ID')}/edit")
        print("\\n✅ Now data synchronization should work perfectly!")
    
    return 0 if failed_updates == 0 else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)