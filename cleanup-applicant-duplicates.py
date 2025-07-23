#!/usr/bin/env python3
"""
Clean up duplicate applicant_counts records.
Keep only the latest record for each scraper_id per date.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.storage import Storage
from datetime import datetime
from collections import defaultdict

def cleanup_duplicates():
    print("🧹 CLEANING UP DUPLICATE APPLICANT RECORDS")
    print("=" * 50)
    
    storage = Storage()
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Get today's data
    result = storage.client.table('applicant_counts')\
        .select('*')\
        .eq('date', today)\
        .order('created_at', desc=True)\
        .execute()
    
    print(f"Found {len(result.data)} records for {today}")
    
    if not result.data:
        print("No data to clean")
        return
    
    # Group by scraper_id, keep the first (latest) record
    seen_scrapers = set()
    records_to_keep = []
    records_to_delete = []
    
    for record in result.data:
        scraper_id = record.get('scraper_id')
        if scraper_id not in seen_scrapers:
            seen_scrapers.add(scraper_id)
            records_to_keep.append(record)
        else:
            records_to_delete.append(record)
    
    print(f"\n📊 Analysis:")
    print(f"  Records to keep: {len(records_to_keep)}")
    print(f"  Records to delete: {len(records_to_delete)}")
    
    if records_to_delete:
        print(f"\n🗑️ Deleting duplicates...")
        
        deleted_count = 0
        for record in records_to_delete:
            try:
                storage.client.table('applicant_counts')\
                    .delete()\
                    .eq('id', record['id'])\
                    .execute()
                deleted_count += 1
                if deleted_count % 50 == 0:
                    print(f"  Deleted {deleted_count}/{len(records_to_delete)} records...")
            except Exception as e:
                print(f"  ❌ Failed to delete record {record['id']}: {e}")
        
        print(f"  ✅ Deleted {deleted_count} duplicate records")
    
    # Final count
    final_result = storage.client.table('applicant_counts')\
        .select('*')\
        .eq('date', today)\
        .execute()
    
    print(f"\n✅ Cleanup complete!")
    print(f"  Final count for {today}: {len(final_result.data)} records")
    
    # Show final stats
    scraper_counts = defaultdict(int)
    for record in final_result.data:
        scraper_id = record.get('scraper_id', 'unknown')
        scraper_counts[scraper_id] += 1
    
    duplicates_remaining = sum(1 for count in scraper_counts.values() if count > 1)
    if duplicates_remaining == 0:
        print(f"  🎉 No duplicates remaining!")
    else:
        print(f"  ⚠️ Still {duplicates_remaining} scrapers with duplicates")
    
    print("=" * 50)

def main():
    """Main function for command line usage."""
    cleanup_duplicates()

if __name__ == "__main__":
    main()