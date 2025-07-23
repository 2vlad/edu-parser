#!/usr/bin/env python3
"""Test the new UPSERT logic in storage to prevent duplicates."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.storage import Storage
from datetime import datetime

def test_upsert_prevention():
    """Test that UPSERT logic prevents duplicates."""
    
    print("🧪 TESTING UPSERT DUPLICATE PREVENTION")
    print("=" * 50)
    
    storage = Storage()
    
    # Create a test result
    test_result = {
        'scraper_id': 'test_upsert_scraper',
        'name': 'Test UPSERT Scraper',
        'status': 'success',
        'count': 100,
        'university': 'TEST',
        'program_name': 'Test Program'
    }
    
    print("1️⃣ Saving result first time...")
    success1 = storage.save_result(test_result)
    print(f"   Result: {'✅ Success' if success1 else '❌ Failed'}")
    
    # Check count
    today = datetime.now().strftime('%Y-%m-%d')
    result = storage.client.table('applicant_counts')\
        .select('*')\
        .eq('scraper_id', 'test_upsert_scraper')\
        .eq('date', today)\
        .execute()
    
    print(f"   Records after first save: {len(result.data)}")
    
    print("\n2️⃣ Saving same result again (should replace, not duplicate)...")
    test_result['count'] = 200  # Change count
    success2 = storage.save_result(test_result)
    print(f"   Result: {'✅ Success' if success2 else '❌ Failed'}")
    
    # Check count again
    result = storage.client.table('applicant_counts')\
        .select('*')\
        .eq('scraper_id', 'test_upsert_scraper')\
        .eq('date', today)\
        .execute()
    
    print(f"   Records after second save: {len(result.data)}")
    if len(result.data) == 1:
        print(f"   ✅ No duplicates! Count updated to: {result.data[0]['count']}")
    else:
        print(f"   ❌ Found {len(result.data)} records - duplicates still exist!")
    
    print("\n3️⃣ Testing batch save with duplicates...")
    
    batch_results = [
        {
            'scraper_id': 'test_batch_1',
            'name': 'Test Batch 1',
            'status': 'success',
            'count': 50
        },
        {
            'scraper_id': 'test_batch_2',
            'name': 'Test Batch 2',
            'status': 'success',
            'count': 75
        }
    ]
    
    # Save batch first time
    saved_count1 = storage.batch_save_results(batch_results)
    print(f"   First batch save: {saved_count1} records")
    
    # Check counts
    result = storage.client.table('applicant_counts')\
        .select('*')\
        .in_('scraper_id', ['test_batch_1', 'test_batch_2'])\
        .eq('date', today)\
        .execute()
    print(f"   Records after first batch: {len(result.data)}")
    
    # Save batch again with different counts
    batch_results[0]['count'] = 150
    batch_results[1]['count'] = 175
    saved_count2 = storage.batch_save_results(batch_results)
    print(f"   Second batch save: {saved_count2} records")
    
    # Check final counts
    result = storage.client.table('applicant_counts')\
        .select('*')\
        .in_('scraper_id', ['test_batch_1', 'test_batch_2'])\
        .eq('date', today)\
        .execute()
    print(f"   Records after second batch: {len(result.data)}")
    
    if len(result.data) == 2:
        print(f"   ✅ No duplicates in batch! Counts: {[r['count'] for r in result.data]}")
    else:
        print(f"   ❌ Found {len(result.data)} records - batch duplicates exist!")
    
    print("\n🧹 Cleaning up test data...")
    # Clean up test data
    for scraper_id in ['test_upsert_scraper', 'test_batch_1', 'test_batch_2']:
        storage.client.table('applicant_counts')\
            .delete()\
            .eq('scraper_id', scraper_id)\
            .eq('date', today)\
            .execute()
    
    print("✅ Test cleanup completed")
    print("=" * 50)

if __name__ == "__main__":
    test_upsert_prevention()