#!/usr/bin/env python3
"""Test the fixed MIPT scraper."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.mipt import scrape_mipt_program

def test_contemporary_combinatorics():
    """Test Contemporary combinatorics specifically."""
    
    program_name = "Contemporary combinatorics"
    url = "https://priem.mipt.ru/applications_v2/bWFzdGVyL0NvbnRlbXBvcmFyeSBTb21iaW5hdG9yaWNzX0tvbnRyYWt0Lmh0bWw="
    
    print("🧪 TESTING FIXED MIPT SCRAPER")
    print("=" * 50)
    print(f"Program: {program_name}")
    print(f"URL: {url}")
    print("Expected count: 14 (based on last row number in screenshot)")
    print()
    
    result = scrape_mipt_program(program_name, url)
    
    print("Result:")
    for key, value in result.items():
        print(f"  {key}: {value}")
    
    if result['status'] == 'success':
        count = result['count']
        if count == 14:
            print(f"\n✅ SUCCESS: Got expected count of {count}")
        else:
            print(f"\n⚠️ UNEXPECTED: Got {count}, expected 14")
    else:
        print(f"\n❌ FAILED: {result.get('error', 'Unknown error')}")

def test_few_more_programs():
    """Test a couple more MIPT programs."""
    
    programs = [
        ("Науки о данных", "https://priem.mipt.ru/applications_v2/bWFzdGVyL05hdWtpIG8gZGFubnlraF9Lb250cmFrdC5odG1s"),
        ("Современная комбинаторика", "https://priem.mipt.ru/applications_v2/bWFzdGVyL1NvdnJlbWVubmF5YSBrb21iaW5hdG9yaWthX0tvbnRyYWt0Lmh0bWw=")
    ]
    
    print("\n🧪 TESTING OTHER MIPT PROGRAMS")
    print("=" * 50)
    
    for program_name, url in programs:
        print(f"\nTesting: {program_name}")
        result = scrape_mipt_program(program_name, url)
        
        if result['status'] == 'success':
            print(f"  ✅ Count: {result['count']}")
        else:
            print(f"  ❌ Error: {result.get('error', 'Unknown')}")

if __name__ == "__main__":
    test_contemporary_combinatorics()
    test_few_more_programs()