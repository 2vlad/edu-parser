#!/usr/bin/env python3
"""Test CSV export functionality directly."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.storage import Storage
from datetime import datetime
import csv
import io

def test_csv_export_direct():
    """Test CSV export logic directly."""
    
    print("🧪 TESTING CSV EXPORT LOGIC")
    print("=" * 50)
    
    storage = Storage()
    today = datetime.now().strftime('%Y-%m-%d')
    
    print(f"Testing CSV export for date: {today}")
    
    # Get data from database
    result = storage.client.table('applicant_counts')\
        .select('*')\
        .eq('date', today)\
        .order('name')\
        .execute()
    
    print(f"Found {len(result.data)} records for {today}")
    
    if not result.data:
        print("❌ No data found for today")
        return
    
    # Group data by university and program (same logic as endpoint)
    programs_data = {}
    dates = set()
    
    for record in result.data:
        if record['status'] != 'success' or not record['count']:
            continue
            
        # Determine university from scraper_id or name
        scraper_id = record['scraper_id']
        name = record.get('name', scraper_id)
        
        if scraper_id.startswith('hse_'):
            university = 'НИУ ВШЭ'
        elif scraper_id.startswith('mipt_'):
            university = 'МФТИ'
        elif scraper_id.startswith('mephi_'):
            university = 'МИФИ'
        else:
            university = record.get('university', 'Unknown')
        
        program_key = f"{university} - {name}"
        date_str = record['date']
        dates.add(date_str)
        
        if program_key not in programs_data:
            programs_data[program_key] = {
                'university': university,
                'program': name,
                'url': '',
                'counts_by_date': {}
            }
        
        programs_data[program_key]['counts_by_date'][date_str] = record['count']
    
    print(f"Processed {len(programs_data)} unique programs")
    
    # Sort dates
    sorted_dates = sorted(list(dates))
    print(f"Dates found: {sorted_dates}")
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    header = ['вуз', 'программа']
    for date_str in sorted_dates:
        # Format date as "DD месяц"
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        months = ['янв', 'фев', 'мар', 'апр', 'май', 'июн',
                 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']
        formatted_date = f"{date_obj.day} {months[date_obj.month - 1]}"
        header.append(formatted_date)
    
    if len(header) > 2:
        header.append('URL')
    
    writer.writerow(header)
    print(f"Header: {header}")
    
    # Write data rows
    row_count = 0
    for program_key in sorted(programs_data.keys()):
        program_data = programs_data[program_key]
        row = [
            program_data['university'],
            program_data['program']
        ]
        
        # Add counts for each date
        for date_str in sorted_dates:
            count = program_data['counts_by_date'].get(date_str, '')
            row.append(count)
        
        # Add URL (empty for now)
        if len(header) > 2:
            row.append('')
        
        writer.writerow(row)
        row_count += 1
        
        # Show first few rows
        if row_count <= 5:
            print(f"Row {row_count}: {row}")
    
    # Get CSV content
    output.seek(0)
    csv_content = output.getvalue()
    output.close()
    
    print(f"\n✅ CSV generated successfully!")
    print(f"   Total rows: {row_count + 1} (including header)")
    print(f"   CSV size: {len(csv_content)} characters")
    
    # Show first few lines
    lines = csv_content.split('\n')[:10]
    print(f"\n📄 CSV Preview (first 10 lines):")
    for i, line in enumerate(lines, 1):
        if line.strip():
            print(f"  {i}: {line}")
    
    print("=" * 50)

if __name__ == "__main__":
    test_csv_export_direct()