#!/usr/bin/env python3
"""Demo script to test Storage class with real Supabase connection."""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.storage import Storage, StorageError


def demo_storage():
    """Demonstrate Storage class functionality."""
    
    print("🔗 Storage Class Demo")
    print("=" * 50)
    
    try:
        # Initialize storage
        print("1. Initializing storage...")
        storage = Storage()
        print("   ✅ Storage initialized successfully!")
        
        # Get enabled scrapers
        print("\n2. Getting enabled scrapers...")
        scrapers = storage.get_enabled_scrapers()
        print(f"   ✅ Found {len(scrapers)} enabled scrapers")
        
        # Show sample scrapers
        if scrapers:
            print("   Sample scrapers:")
            for scraper in scrapers[:3]:
                print(f"   - {scraper['scraper_id']}: {scraper['name']}")
        
        # Test saving a result
        print("\n3. Testing save_result...")
        test_result = {
            'scraper_id': 'demo_test',
            'name': 'Demo Test - Storage Module',
            'count': 999,
            'status': 'success'
        }
        
        success = storage.save_result(test_result)
        if success:
            print("   ✅ Test result saved successfully!")
        else:
            print("   ❌ Failed to save test result")
        
        # Get today's results
        print("\n4. Getting today's results...")
        today_results = storage.get_today_results()
        print(f"   ✅ Found {len(today_results)} results for today")
        
        # Show recent results
        if today_results:
            print("   Recent results:")
            for result in today_results[:3]:
                status_icon = "✅" if result['status'] == 'success' else "❌"
                count = result.get('count', 'N/A')
                print(f"   {status_icon} {result['scraper_id']}: {count}")
        
        # Test batch save
        print("\n5. Testing batch_save_results...")
        batch_results = [
            {
                'scraper_id': 'demo_batch_1',
                'name': 'Demo Batch Test 1',
                'count': 100,
                'status': 'success'
            },
            {
                'scraper_id': 'demo_batch_2', 
                'name': 'Demo Batch Test 2',
                'count': 200,
                'status': 'success'
            }
        ]
        
        saved_count = storage.batch_save_results(batch_results)
        print(f"   ✅ Saved {saved_count} results in batch")
        
        # Test get scraper by ID
        print("\n6. Testing get_scraper_by_id...")
        if scrapers:
            first_scraper = scrapers[0]
            scraper = storage.get_scraper_by_id(first_scraper['scraper_id'])
            if scraper:
                print(f"   ✅ Retrieved scraper: {scraper['name']}")
            else:
                print("   ❌ Failed to retrieve scraper")
        
        # Clean up test data
        print("\n7. Cleaning up test data...")
        # Note: We don't have a delete method, so test data will remain
        print("   ℹ️  Test data left in database for verification")
        
        print("\n🎉 Storage demo completed successfully!")
        return True
        
    except StorageError as e:
        print(f"   ❌ Storage error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = demo_storage()
    if not success:
        print("\n💡 Make sure your .env file contains valid Supabase credentials")
        sys.exit(1)