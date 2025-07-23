#!/usr/bin/env python3
"""
Cron job runner for Railway.
This script is executed on a schedule defined by RAILWAY_CRON_SCHEDULE.
"""

import os
import sys
import subprocess
from datetime import datetime

def main():
    """Run the scraper job."""
    print(f"🚀 Starting Edu Parser Cron Job at {datetime.now()}")
    
    # Detailed environment debugging for cron.py
    print("🔍 DEBUG: cron.py environment analysis")
    print(f"🔍 DEBUG: __file__ = {__file__}")
    print(f"🔍 DEBUG: sys.argv = {sys.argv}")
    print(f"🔍 DEBUG: Current working directory = {os.getcwd()}")
    
    # Check PORT variable in cron environment
    port_env = os.environ.get('PORT')
    print(f"🔍 DEBUG: PORT environment variable in cron.py = '{port_env}' (type: {type(port_env)})")
    
    if port_env == '$PORT':
        print("🚨 DEBUG: FOUND THE PROBLEM! PORT contains literal '$PORT' in cron.py!")
    elif port_env and '$' in port_env:
        print(f"🚨 DEBUG: PORT contains dollar sign: '{port_env}'")
    
    # Check all environment variables that might be relevant
    relevant_vars = ['PORT', 'FLASK_DEBUG', 'SCRAPER_MODE', 'RAILWAY_CRON_SCHEDULE']
    for var in relevant_vars:
        value = os.environ.get(var)
        print(f"🔍 DEBUG: {var} = '{value}'")
    
    try:
        # Set clean environment to prevent any Flask/PORT conflicts
        env = os.environ.copy()
        env['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))
        # Remove PORT to prevent Flask from trying to start
        env.pop('PORT', None)
        # Ensure we're in scraper mode
        env['SCRAPER_MODE'] = 'enabled'
        
        # Run scraper directly without importing main.py or dashboard
        result = subprocess.run([
            sys.executable, '-c', '''
import sys
import os
sys.path.insert(0, os.getcwd())

from scrapers.hse import scrape_hse
from scrapers.mipt import scrape_mipt
from scrapers.mephi import scrape_mephi
from storage.supabase_client import SupabaseStorage
from config import Config
from datetime import datetime

print("🚀 Starting cron scraper run...")

config = Config()
storage = SupabaseStorage(config)

# Get today's date
today = datetime.now().strftime("%Y-%m-%d")

scrapers = [
    ("HSE", scrape_hse),
    ("MIPT", scrape_mipt), 
    ("MEPhI", scrape_mephi)
]

for scraper_name, scraper_func in scrapers:
    print(f"Running {scraper_name} scraper...")
    try:
        results = scraper_func(config)
        for result in results:
            result["date"] = today
        storage.save_results(results)
        print(f"✅ {scraper_name}: Saved {len(results)} results")
    except Exception as e:
        print(f"❌ {scraper_name} failed: {e}")

print("✅ Cron scraper run completed")
'''
        ], 
        cwd=os.path.dirname(os.path.abspath(__file__)),
        env=env,
        capture_output=True,
        text=True,
        timeout=600  # 10 minute timeout
        )
        
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print(f"✅ Cron job completed successfully at {datetime.now()}")
        else:
            print(f"❌ Cron job failed with return code {result.returncode}")
            sys.exit(1)
        
    except subprocess.TimeoutExpired:
        print(f"❌ Cron job timed out after 10 minutes")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Cron job failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()