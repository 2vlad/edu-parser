#!/usr/bin/env python3
"""Test the fixed MIPT scraper on IT Products Management."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.mipt import scrape_mipt_program

def test_it_products():
    """Test IT Products Management specifically."""
    
    program_name = "Управление IT-продуктами"
    url = "https://priem.mipt.ru/applications_v2/bWFzdGVyL1VwcmF2bGVuaWUgSVQtcHJvZHVrdGFtaV9Lb250cmFrdC5odG1s"
    
    print("🧪 TESTING FIXED MIPT SCRAPER - IT Products Management")
    print("=" * 50)
    print(f"Program: {program_name}")
    print(f"URL: {url}")
    print("Expected count: 239 (based on last row number in screenshot)")
    print()
    
    result = scrape_mipt_program(program_name, url)
    
    print("Result:")
    for key, value in result.items():
        print(f"  {key}: {value}")
    
    if result['status'] == 'success':
        count = result['count']
        if count == 239:
            print(f"\n✅ SUCCESS: Got expected count of {count}")
        else:
            print(f"\n⚠️ UNEXPECTED: Got {count}, expected 239")
    else:
        print(f"\n❌ FAILED: {result.get('error', 'Unknown error')}")

def test_other_programs():
    """Test other MIPT programs to make sure they still work."""
    
    programs = [
        ("Contemporary combinatorics", "https://priem.mipt.ru/applications_v2/bWFzdGVyL0NvbnRlbXBvcmFyeSBTb21iaW5hdG9yaWNzX0tvbnRyYWt0Lmh0bWw="),
        ("Науки о данных", "https://priem.mipt.ru/applications_v2/bWFzdGVyL05hdWtpIG8gZGFubnlraF9Lb250cmFrdC5odG1s")
    ]
    
    print("\n🧪 TESTING OTHER MIPT PROGRAMS (regression test)")
    print("=" * 50)
    
    for program_name, url in programs:
        print(f"\nTesting: {program_name}")
        result = scrape_mipt_program(program_name, url)
        
        if result['status'] == 'success':
            print(f"  ✅ Count: {result['count']}")
        else:
            print(f"  ❌ Error: {result.get('error', 'Unknown')}")

if __name__ == "__main__":
    test_it_products()
    test_other_programs()