#!/usr/bin/env python3
"""Test UPSERT logic with real scraper data."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.mipt import scrape_mipt_program
from core.storage import Storage
from datetime import datetime

def test_real_scraper_upsert():
    """Test UPSERT with real MIPT scraper."""
    
    print("🧪 TESTING REAL SCRAPER UPSERT")
    print("=" * 50)
    
    storage = Storage()
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Test with Contemporary combinatorics
    program_name = "Contemporary combinatorics"
    url = "https://priem.mipt.ru/applications_v2/bWFzdGVyL0NvbnRlbXBvcmFyeSBTb21iaW5hdG9yaWNzX0tvbnRyYWt0Lmh0bWw="
    scraper_id = "mipt_contemporary_combinatorics"
    
    print(f"Testing with: {program_name}")
    print(f"Scraper ID: {scraper_id}")
    
    # Check initial count
    initial_result = storage.client.table('applicant_counts')\
        .select('*')\
        .eq('scraper_id', scraper_id)\
        .eq('date', today)\
        .execute()
    
    print(f"\nInitial records: {len(initial_result.data)}")
    
    # Run scraper first time
    print("\n1️⃣ Running scraper first time...")
    result1 = scrape_mipt_program(program_name, url)
    
    if result1['status'] == 'success':
        storage.save_result(result1)
        print(f"   ✅ Saved: {result1['count']} applications")
    else:
        print(f"   ❌ Error: {result1.get('error')}")
        return
    
    # Check count after first run
    after_first = storage.client.table('applicant_counts')\
        .select('*')\
        .eq('scraper_id', scraper_id)\
        .eq('date', today)\
        .execute()
    
    print(f"   Records after first run: {len(after_first.data)}")
    
    # Run scraper second time
    print("\n2️⃣ Running same scraper again...")
    result2 = scrape_mipt_program(program_name, url)
    
    if result2['status'] == 'success':
        storage.save_result(result2)
        print(f"   ✅ Saved: {result2['count']} applications")
    else:
        print(f"   ❌ Error: {result2.get('error')}")
        return
    
    # Check final count
    final_result = storage.client.table('applicant_counts')\
        .select('*')\
        .eq('scraper_id', scraper_id)\
        .eq('date', today)\
        .execute()
    
    print(f"   Records after second run: {len(final_result.data)}")
    
    if len(final_result.data) == 1:
        print(f"   ✅ SUCCESS: No duplicates created!")
        print(f"   Final count: {final_result.data[0]['count']}")
    else:
        print(f"   ❌ FAILURE: {len(final_result.data)} records found - duplicates exist!")
        for record in final_result.data:
            print(f"      ID: {record['id']}, Count: {record['count']}, Created: {record['created_at']}")
    
    print("=" * 50)

if __name__ == "__main__":
    test_real_scraper_upsert()