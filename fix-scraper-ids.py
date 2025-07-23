#!/usr/bin/env python3
"""
Fix scraper ID mismatch between code and database.
Update database configurations to match actual scraper function IDs.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.registry import ScraperRegistry
from core.storage import Storage

def main():
    print("🔧 FIXING SCRAPER ID MISMATCH")
    print("=" * 50)
    
    storage = Storage()
    registry = ScraperRegistry(storage)
    
    # Get all discovered scrapers
    discovered_count = registry.discover_scrapers()
    all_scrapers = registry.get_all_discovered_scrapers()
    
    print(f"Found {len(all_scrapers)} scrapers in code")
    
    # Get current database configurations
    configs = storage.client.table('scrapers_config').select('*').execute()
    print(f"Found {len(configs.data)} configurations in database")
    
    # Create mapping of actual scraper IDs
    code_scraper_ids = set()
    for func, config in all_scrapers:
        scraper_id = config.get('scraper_id')
        if scraper_id:
            code_scraper_ids.add(scraper_id)
    
    print(f"\n🔍 Scraper IDs in code: {len(code_scraper_ids)}")
    for sid in sorted(code_scraper_ids):
        print(f"  - {sid}")
    
    # Find mismatched HSE configurations
    db_hse_configs = [c for c in configs.data if c['scraper_id'].startswith('hse_online_')]
    code_hse_ids = [sid for sid in code_scraper_ids if sid.startswith('hse_')]
    
    print(f"\n🔄 HSE ID Mapping needed:")
    print(f"Database has {len(db_hse_configs)} hse_online_* configs")
    print(f"Code has {len(code_hse_ids)} hse_* scrapers")
    
    # Create new configurations for all code scrapers
    print(f"\n🔧 Creating/updating configurations...")
    
    for func, config in all_scrapers:
        scraper_id = config.get('scraper_id')
        university = config.get('university', 'Unknown')
        program_name = config.get('program_name', 'Unknown')
        
        # Check if config exists
        existing = next((c for c in configs.data if c['scraper_id'] == scraper_id), None)
        
        if existing:
            print(f"  ✅ {scraper_id} - already exists")
        else:
            # Create new configuration
            new_config = {
                'scraper_id': scraper_id,
                'name': f"{university} - {program_name}",
                'enabled': True
            }
            
            try:
                result = storage.client.table('scrapers_config').insert(new_config).execute()
                print(f"  ➕ {scraper_id} - created new config")
            except Exception as e:
                print(f"  ❌ {scraper_id} - error: {e}")
    
    # Disable old HSE configurations that don't match
    print(f"\n🔄 Disabling old HSE configurations...")
    for config in db_hse_configs:
        old_id = config['scraper_id']
        if old_id not in code_scraper_ids:
            try:
                storage.client.table('scrapers_config').update({'enabled': False}).eq('scraper_id', old_id).execute()
                print(f"  🔴 {old_id} - disabled (no matching scraper)")
            except Exception as e:
                print(f"  ❌ {old_id} - error disabling: {e}")
    
    print(f"\n✅ Configuration update complete!")
    print("=" * 50)

if __name__ == "__main__":
    main()