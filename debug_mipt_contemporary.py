#!/usr/bin/env python3
"""Debug MIPT Contemporary combinatorics scraper."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.mipt import fetch_mipt_html
from bs4 import BeautifulSoup

def debug_contemporary_combinatorics():
    """Debug the Contemporary combinatorics page structure."""
    
    url = "https://priem.mipt.ru/applications_v2/bWFzdGVyL0NvbnRlbXBvcmFyeSBTb21iaW5hdG9yaWNzX0tvbnRyYWt0Lmh0bWw="
    
    print("🔍 DEBUGGING MIPT Contemporary combinatorics")
    print("=" * 50)
    print(f"URL: {url}")
    
    # Fetch HTML
    html_content = fetch_mipt_html(url)
    if not html_content:
        print("❌ Failed to fetch HTML")
        return
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Check all table rows with different classes
    for row_class in ['R18', 'R11', 'R19', 'R0', 'R13']:
        elements = soup.find_all('tr', class_=row_class)
        if elements:
            print(f"\n🎯 Found {len(elements)} rows with class '{row_class}':")
            
            # Show first few and last few elements
            for i, elem in enumerate(elements[:3]):  # First 3
                cells = elem.find_all(['td', 'th'])
                if cells:
                    cell_texts = [cell.get_text().strip() for cell in cells[:6]]  # First 6 columns
                    print(f"  Row {i+1}: {cell_texts}")
            
            if len(elements) > 6:
                print(f"  ... ({len(elements) - 6} more rows) ...")
            
            # Last 3 elements
            for i, elem in enumerate(elements[-3:]):
                cells = elem.find_all(['td', 'th'])
                if cells:
                    cell_texts = [cell.get_text().strip() for cell in cells[:6]]  # First 6 columns
                    actual_index = len(elements) - 3 + i + 1
                    print(f"  Row {actual_index}: {cell_texts}")
    
    # Check if there's a table with data-index or other attributes
    print(f"\n🔍 Looking for data-index attributes:")
    data_index_elements = soup.find_all(attrs={"data-index": True})
    if data_index_elements:
        print(f"Found {len(data_index_elements)} elements with data-index:")
        for elem in data_index_elements[-5:]:  # Last 5
            print(f"  data-index='{elem.get('data-index')}' tag='{elem.name}' text='{elem.get_text().strip()[:50]}'")
    else:
        print("  No data-index attributes found")
    
    # Look at the table structure
    print(f"\n📊 Table structure analysis:")
    tables = soup.find_all('table')
    for i, table in enumerate(tables):
        rows = table.find_all('tr')
        print(f"  Table {i+1}: {len(rows)} rows")
        if rows:
            # Check header row
            header_cells = rows[0].find_all(['th', 'td'])
            if header_cells:
                headers = [cell.get_text().strip() for cell in header_cells]
                print(f"    Headers: {headers[:6]}")  # First 6 headers
            
            # Check last data row
            if len(rows) > 1:
                last_row = rows[-1]
                cells = last_row.find_all(['td', 'th'])
                if cells:
                    cell_texts = [cell.get_text().strip() for cell in cells[:6]]
                    print(f"    Last row data: {cell_texts}")

if __name__ == "__main__":
    debug_contemporary_combinatorics()