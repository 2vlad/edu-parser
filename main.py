#!/usr/bin/env python3
"""Main entry point for edu-parser scraping system."""

import sys
import os
from datetime import datetime
import traceback

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from core.logging_config import setup_logging, get_logger
from core.storage import Storage, StorageError


def main():
    """Main entry point for the edu-parser system."""
    
    # Initialize logging first
    setup_logging(log_level=os.environ.get("LOG_LEVEL", "INFO"))
    logger = get_logger(__name__)
    
    logger.info("=" * 60)
    logger.info("Starting edu-parser system")
    logger.info(f"Run started at: {datetime.now().isoformat()}")
    logger.info("=" * 60)
    
    try:
        # Initialize storage
        logger.info("Initializing storage system...")
        storage = Storage()
        logger.info("Storage system initialized successfully")
        
        # Get enabled scrapers
        logger.info("Retrieving enabled scrapers...")
        enabled_scrapers = storage.get_enabled_scrapers()
        
        if not enabled_scrapers:
            logger.error("No enabled scrapers found in database")
            return False
        
        logger.info(f"Found {len(enabled_scrapers)} enabled scrapers")
        
        # Log scraper summary by university
        universities = {}
        for scraper in enabled_scrapers:
            scraper_id = scraper['scraper_id']
            if scraper_id.startswith('hse_'):
                universities.setdefault('HSE', []).append(scraper)
            elif scraper_id.startswith('mipt_'):
                universities.setdefault('MIPT', []).append(scraper)
            elif scraper_id.startswith('mephi_'):
                universities.setdefault('MEPhI', []).append(scraper)
            else:
                universities.setdefault('Other', []).append(scraper)
        
        for uni, scrapers in universities.items():
            logger.info(f"   - {uni}: {len(scrapers)} scrapers")
        
        # TODO: Run scrapers (will be implemented in subsequent tasks)
        logger.warning("Scraper execution not yet implemented - coming in next tasks")
        logger.info("For now, just validating system readiness...")
        
        # Test basic functionality
        today_results = storage.get_today_results()
        logger.info(f"Found {len(today_results)} existing results for today")
        
        logger.info("=" * 60)
        logger.info("edu-parser system validation completed successfully")
        logger.info(f"Run completed at: {datetime.now().isoformat()}")
        logger.info("=" * 60)
        
        return True
        
    except StorageError as e:
        logger.error(f"Storage system error: {e}")
        logger.error("Cannot proceed without database connectivity")
        return False
        
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        logger.error("Full traceback:")
        
        # Log full traceback to file but not console
        file_logger = get_logger('error_details')
        file_logger.error("Full error traceback:", exc_info=True)
        
        return False


if __name__ == "__main__":
    try:
        success = main()
        exit_code = 0 if success else 1
        
        # Final log message
        logger = get_logger(__name__)
        if success:
            logger.info("System exited successfully")
        else:
            logger.error("System exited with errors")
            
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        logger = get_logger(__name__)
        logger.warning("System interrupted by user (Ctrl+C)")
        sys.exit(130)
    except Exception as e:
        # This should catch any logging setup errors
        print(f"FATAL: Failed to initialize logging or main system: {e}")
        traceback.print_exc()
        sys.exit(1)