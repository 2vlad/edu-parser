#!/usr/bin/env python3
"""Debug MIPT IT Products Management scraper."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.mipt import fetch_mipt_html
from bs4 import BeautifulSoup

def debug_it_products():
    """Debug the IT Products Management page structure."""
    
    url = "https://priem.mipt.ru/applications_v2/bWFzdGVyL1VwcmF2bGVuaWUgSVQtcHJvZHVrdGFtaV9Lb250cmFrdC5odG1s"
    
    print("🔍 DEBUGGING MIPT Управление IT-продуктами")
    print("=" * 50)
    print(f"URL: {url}")
    
    # Fetch HTML
    html_content = fetch_mipt_html(url)
    if not html_content:
        print("❌ Failed to fetch HTML")
        return
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Check all table rows with different classes
    all_rows = []
    for row_class in ['R0', 'R11', 'R13', 'R18', 'R19', 'R45']:  # Adding R45 which was visible in screenshot
        elements = soup.find_all('tr', class_=row_class)
        if elements:
            print(f"\n🎯 Found {len(elements)} rows with class '{row_class}':")
            
            for elem in elements:
                cells = elem.find_all(['td', 'th'])
                if cells and len(cells) > 0:
                    first_cell_text = cells[0].get_text().strip()
                    if first_cell_text.isdigit():
                        row_number = int(first_cell_text)
                        all_rows.append((row_number, elem, row_class))
                        
                        # Show a few examples
                        if len(all_rows) <= 5 or row_number % 50 == 0:
                            cell_texts = [cell.get_text().strip() for cell in cells[:6]]
                            print(f"    Row {row_number}: {cell_texts} (class: {row_class})")
    
    if all_rows:
        # Sort all rows by number
        all_rows.sort(key=lambda x: x[0])
        
        print(f"\n📊 TOTAL DATA ROWS FOUND: {len(all_rows)}")
        print(f"Row numbers range: {all_rows[0][0]} to {all_rows[-1][0]}")
        
        # Show last 10 rows
        print(f"\n📋 Last 10 rows:")
        for row_number, elem, row_class in all_rows[-10:]:
            cells = elem.find_all(['td', 'th'])
            cell_texts = [cell.get_text().strip() for cell in cells[:6]]
            print(f"  Row {row_number}: {cell_texts} (class: {row_class})")
        
        # What our current scraper would return
        last_row_number = all_rows[-1][0]
        print(f"\n🎯 Current scraper logic would return: {last_row_number}")
        print(f"Expected from screenshot: 239")
        
        if last_row_number != 239:
            print(f"❌ MISMATCH! Found {last_row_number}, expected 239")
            
            # Check for missing row classes
            print(f"\n🔍 Checking for additional row classes...")
            all_trs = soup.find_all('tr')
            class_counts = {}
            numeric_rows_by_class = {}
            
            for tr in all_trs:
                tr_class = tr.get('class')
                if tr_class:
                    class_name = ' '.join(tr_class)
                    class_counts[class_name] = class_counts.get(class_name, 0) + 1
                    
                    # Check if first cell is numeric
                    cells = tr.find_all(['td', 'th'])
                    if cells:
                        first_cell_text = cells[0].get_text().strip()
                        if first_cell_text.isdigit():
                            if class_name not in numeric_rows_by_class:
                                numeric_rows_by_class[class_name] = []
                            numeric_rows_by_class[class_name].append(int(first_cell_text))
            
            print(f"\nAll row classes found:")
            for class_name, count in sorted(class_counts.items()):
                if class_name in numeric_rows_by_class:
                    numbers = numeric_rows_by_class[class_name]
                    min_num = min(numbers) if numbers else 0
                    max_num = max(numbers) if numbers else 0
                    print(f"  {class_name}: {count} rows (numeric: {len(numbers)}, range: {min_num}-{max_num})")
                else:
                    print(f"  {class_name}: {count} rows (no numeric data)")
    else:
        print("❌ No data rows found!")

if __name__ == "__main__":
    debug_it_products()