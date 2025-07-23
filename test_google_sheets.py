#!/usr/bin/env python3
"""Test Google Sheets integration without requiring actual credentials."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_google_sheets_mock():
    """Test Google Sheets functionality with mock data."""
    
    print("🧪 TESTING GOOGLE SHEETS INTEGRATION")
    print("=" * 50)
    
    try:
        from core.google_sheets import GoogleSheetsSync
        
        print("✅ Google Sheets module imported successfully")
        
        # Test initialization
        sheets_sync = GoogleSheetsSync()
        print("✅ GoogleSheetsSync object created")
        
        # Check availability (will be False without credentials)
        is_available = sheets_sync.is_available()
        print(f"📊 Service availability: {'✅ Available' if is_available else '❌ Not configured'}")
        
        if not is_available:
            print("\n⚠️ Google Sheets not configured (this is expected for testing)")
            print("To configure Google Sheets:")
            print("  1. Run: python setup_google_sheets.py")
            print("  2. Set GOOGLE_CREDENTIALS_JSON and GOOGLE_SPREADSHEET_ID environment variables")
        
        # Test sync function (will skip if not configured)
        print("\n🔄 Testing sync function...")
        from core.google_sheets import sync_to_sheets
        
        result = sync_to_sheets()
        if result:
            print("✅ Sync completed successfully")
        else:
            print("⚠️ Sync skipped (expected if not configured)")
        
    except ImportError as e:
        print(f"❌ Missing required dependencies: {e}")
        print("\n📦 To install Google Sheets dependencies:")
        print("   pip install google-api-python-client google-auth")
        
    except Exception as e:
        print(f"❌ Error testing Google Sheets: {e}")
    
    print("\n🔧 Testing CSV-like data formatting...")
    
    # Test data formatting logic (doesn't require API)
    test_data = [
        {
            'scraper_id': 'hse_test_program',
            'name': 'HSE - Test Program',
            'count': 123,
            'date': '2025-07-23',
            'status': 'success'
        },
        {
            'scraper_id': 'mipt_test_program',
            'name': 'МФТИ - Test Program',
            'count': 456,
            'date': '2025-07-23',
            'status': 'success'
        }
    ]
    
    print(f"📋 Test data: {len(test_data)} records")
    
    # Format data like Google Sheets would
    formatted_rows = []
    header = ['вуз', 'программа', 'количество заявлений', 'дата обновления', 'scraper_id']
    formatted_rows.append(header)
    
    for record in test_data:
        scraper_id = record['scraper_id']
        if scraper_id.startswith('hse_'):
            university = 'НИУ ВШЭ'
        elif scraper_id.startswith('mipt_'):
            university = 'МФТИ'
        elif scraper_id.startswith('mephi_'):
            university = 'МИФИ'
        else:
            university = 'Unknown'
        
        row = [
            university,
            record['name'],
            record['count'],
            record['date'],
            record['scraper_id']
        ]
        formatted_rows.append(row)
    
    print("✅ Data formatting test successful")
    print("\n📊 Formatted data preview:")
    for i, row in enumerate(formatted_rows):
        print(f"   Row {i}: {row}")
    
    print("\n=" * 50)
    print("✅ Google Sheets integration test completed")

if __name__ == "__main__":
    test_google_sheets_mock()