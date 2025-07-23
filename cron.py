#!/usr/bin/env python3
"""
Cron job runner for Railway.
This script is executed on a schedule defined by RAILWAY_CRON_SCHEDULE.
"""

import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Run the scraper job."""
    print(f"🚀 Starting Edu Parser Cron Job at {datetime.now()}")
    
    # Import and run the main scraper
    try:
        from main import main as run_scrapers
        
        # Run scrapers
        run_scrapers()
        
        print(f"✅ Cron job completed successfully at {datetime.now()}")
        
    except Exception as e:
        print(f"❌ Cron job failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()