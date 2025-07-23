#!/usr/bin/env python3
"""
Clean up duplicate scrapers in database.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.storage import Storage
from collections import defaultdict

def main():
    print("🧹 CLEANING UP DUPLICATE SCRAPERS")
    print("=" * 50)
    
    storage = Storage()
    
    # Get all configurations
    configs = storage.client.table('scrapers_config').select('*').execute()
    print(f"Found {len(configs.data)} total configurations")
    
    # Group by scraper_id to find duplicates
    scraper_groups = defaultdict(list)
    for config in configs.data:
        scraper_id = config['scraper_id']
        scraper_groups[scraper_id].append(config)
    
    # Find duplicates
    duplicates = {k: v for k, v in scraper_groups.items() if len(v) > 1}
    unique_scrapers = {k: v for k, v in scraper_groups.items() if len(v) == 1}
    
    print(f"\n📊 Analysis:")
    print(f"  Unique scrapers: {len(unique_scrapers)}")
    print(f"  Duplicated scrapers: {len(duplicates)}")
    
    total_duplicate_records = sum(len(v) - 1 for v in duplicates.values())
    print(f"  Extra records to delete: {total_duplicate_records}")
    
    if duplicates:
        print(f"\n🔍 Duplicated scrapers:")
        for scraper_id, records in duplicates.items():
            print(f"  - {scraper_id}: {len(records)} copies")
    
    # Delete duplicates (keep the first one, delete the rest)
    deleted_count = 0
    for scraper_id, records in duplicates.items():
        # Sort by created_at to keep the earliest
        records_sorted = sorted(records, key=lambda x: x.get('created_at', ''))
        records_to_delete = records_sorted[1:]  # Keep first, delete rest
        
        for record in records_to_delete:
            try:
                storage.client.table('scrapers_config').delete().eq('scraper_id', record['scraper_id']).eq('created_at', record['created_at']).execute()
                print(f"  🗑️ Deleted duplicate: {scraper_id}")
                deleted_count += 1
            except Exception as e:
                print(f"  ❌ Failed to delete {scraper_id}: {e}")
    
    print(f"\n✅ Cleanup complete!")
    print(f"  Deleted {deleted_count} duplicate records")
    
    # Final count
    final_configs = storage.client.table('scrapers_config').select('*').execute()
    print(f"  Final count: {len(final_configs.data)} configurations")
    
    print("=" * 50)

if __name__ == "__main__":
    main()