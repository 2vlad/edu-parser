#!/usr/bin/env python3
"""
Standalone cron script for Railway cron service.
This script runs scrapers without any web server components.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers.hse import scrape_hse
from scrapers.mipt import scrape_mipt
from scrapers.mephi import scrape_mephi
from storage.supabase_client import SupabaseStorage
from config import Config
from datetime import datetime

def main():
    """Run all scrapers and save results."""
    print(f"🚀 Starting standalone cron scraper run at {datetime.now()}")
    
    # Detailed environment debugging for cron
    print("🔍 DEBUG: cron-only.py environment analysis")
    print(f"🔍 DEBUG: __file__ = {__file__}")
    print(f"🔍 DEBUG: sys.argv = {sys.argv}")
    print(f"🔍 DEBUG: Current working directory = {os.getcwd()}")
    
    # Check PORT variable in cron environment
    port_env = os.environ.get('PORT')
    print(f"🔍 DEBUG: PORT environment variable in cron = '{port_env}' (type: {type(port_env)})")
    
    # Check all environment variables that might be relevant
    relevant_vars = ['PORT', 'FLASK_DEBUG', 'SCRAPER_MODE', 'RAILWAY_CRON_SCHEDULE']
    for var in relevant_vars:
        value = os.environ.get(var)
        print(f"🔍 DEBUG: {var} = '{value}'")
    
    # Check if this is being run as cron vs standalone
    if 'cron' in ' '.join(sys.argv).lower() or os.environ.get('RAILWAY_CRON_SCHEDULE'):
        print("🔍 DEBUG: Detected cron execution context")
    else:
        print("🔍 DEBUG: Detected standalone execution context")
    
    try:
        config = Config()
        storage = SupabaseStorage(config)
        
        # Get today's date
        today = datetime.now().strftime("%Y-%m-%d")
        
        scrapers = [
            ("HSE", scrape_hse),
            ("MIPT", scrape_mipt), 
            ("MEPhI", scrape_mephi)
        ]
        
        total_results = 0
        for scraper_name, scraper_func in scrapers:
            print(f"Running {scraper_name} scraper...")
            try:
                results = scraper_func(config)
                for result in results:
                    result["date"] = today
                storage.save_results(results)
                total_results += len(results)
                print(f"✅ {scraper_name}: Saved {len(results)} results")
            except Exception as e:
                print(f"❌ {scraper_name} failed: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"✅ Cron scraper run completed successfully. Total results: {total_results}")
        
    except Exception as e:
        print(f"❌ Critical error in cron job: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()