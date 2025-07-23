#!/usr/bin/env python3
"""
Check scraper configuration in database vs discovered scrapers.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.registry import ScraperRegistry, get_all_scrapers
from core.storage import Storage

def main():
    print("🔍 SCRAPER ANALYSIS")
    print("=" * 50)
    
    # Initialize components
    storage = Storage()
    registry = ScraperRegistry(storage)
    
    # Discover all scrapers
    print("📡 Discovering scrapers...")
    discovered_count = registry.discover_scrapers()
    print(f"Found {discovered_count} scraper functions")
    
    # Get all discovered scrapers
    all_scrapers = registry.get_all_discovered_scrapers()
    print(f"\n🔍 All discovered scrapers ({len(all_scrapers)}):")
    for func, config in all_scrapers:
        scraper_id = config.get('scraper_id', 'unknown')
        university = config.get('university', 'unknown')
        program = config.get('program_name', 'unknown')
        print(f"  - {scraper_id} ({university}: {program})")
    
    # Get enabled scrapers from database
    print(f"\n✅ Enabled scrapers in database:")
    enabled_scrapers = registry.load_enabled_scrapers()
    print(f"Found {len(enabled_scrapers)} enabled scrapers")
    for func, config in enabled_scrapers:
        scraper_id = config.get('scraper_id', 'unknown')
        university = config.get('university', 'unknown')
        program = config.get('program_name', 'unknown')
        print(f"  - {scraper_id} ({university}: {program})")
    
    # Check database configuration
    print(f"\n🗄️ Database scraper configurations:")
    try:
        # Query scrapers_config table
        configs = storage.client.table('scrapers_config').select('*').execute()
        print(f"Found {len(configs.data)} configurations in database")
        
        enabled_count = 0
        for config in configs.data:
            scraper_id = config['scraper_id']
            enabled = config.get('enabled', False)
            university = config.get('university', 'unknown')
            if enabled:
                enabled_count += 1
                print(f"  ✅ {scraper_id} ({university}) - ENABLED")
            else:
                print(f"  ❌ {scraper_id} ({university}) - DISABLED")
        
        print(f"\nSummary:")
        print(f"  Total configurations: {len(configs.data)}")
        print(f"  Enabled: {enabled_count}")
        print(f"  Disabled: {len(configs.data) - enabled_count}")
        
    except Exception as e:
        print(f"Error querying database: {e}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()