#!/usr/bin/env python3
"""
Check database schema for scrapers_config table.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.storage import Storage

def main():
    print("🔍 DATABASE SCHEMA CHECK")
    print("=" * 50)
    
    storage = Storage()
    
    # Get existing configuration to see the schema
    try:
        configs = storage.client.table('scrapers_config').select('*').limit(1).execute()
        if configs.data:
            sample_config = configs.data[0]
            print("📋 Existing configuration columns:")
            for key, value in sample_config.items():
                print(f"  - {key}: {type(value).__name__} = {value}")
        else:
            print("❌ No configurations found in database")
    except Exception as e:
        print(f"❌ Error querying database: {e}")
    
    print("=" * 50)

if __name__ == "__main__":
    main()