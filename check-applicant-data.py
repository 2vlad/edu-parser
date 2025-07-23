#!/usr/bin/env python3
"""
Check applicant_counts table for duplicates.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.storage import Storage
from datetime import datetime
from collections import defaultdict

def main():
    print("🔍 CHECKING APPLICANT DATA")
    print("=" * 50)
    
    storage = Storage()
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Get today's data
    result = storage.client.table('applicant_counts')\
        .select('*')\
        .eq('date', today)\
        .execute()
    
    print(f"Found {len(result.data)} records for {today}")
    
    if not result.data:
        print("No data for today")
        return
    
    # Group by scraper_id and name
    scraper_groups = defaultdict(list)
    name_groups = defaultdict(list)
    
    for record in result.data:
        scraper_id = record.get('scraper_id', 'unknown')
        name = record.get('name', 'unknown')
        scraper_groups[scraper_id].append(record)
        name_groups[name].append(record)
    
    print(f"\n📊 Analysis:")
    print(f"  Unique scraper_ids: {len(scraper_groups)}")
    print(f"  Unique names: {len(name_groups)}")
    
    # Find duplicates by scraper_id
    duplicate_scrapers = {k: v for k, v in scraper_groups.items() if len(v) > 1}
    if duplicate_scrapers:
        print(f"\n🚨 Duplicate scraper_ids:")
        for scraper_id, records in list(duplicate_scrapers.items())[:10]:  # Show first 10
            print(f"  - {scraper_id}: {len(records)} records")
    
    # Find duplicates by name
    duplicate_names = {k: v for k, v in name_groups.items() if len(v) > 1}
    if duplicate_names:
        print(f"\n🚨 Duplicate names:")
        for name, records in list(duplicate_names.items())[:10]:  # Show first 10
            counts = [r.get('count', 0) for r in records]
            print(f"  - {name}: {len(records)} records, counts: {counts[:5]}...")
    
    # Show sample data
    print(f"\n📋 Sample records:")
    for i, record in enumerate(result.data[:5]):
        scraper_id = record.get('scraper_id', 'unknown')
        name = record.get('name', 'unknown')
        count = record.get('count', 0)
        print(f"  {i+1}. {scraper_id} | {name} | count: {count}")
    
    print("=" * 50)

if __name__ == "__main__":
    main()