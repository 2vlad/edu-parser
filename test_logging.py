#!/usr/bin/env python3
"""Test logging configuration."""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.logging_config import setup_logging, get_logger, log_scraper_result, log_performance
from core.storage import Storage, StorageError


def test_logging():
    """Test logging configuration and functionality."""
    
    print("🔍 Testing Logging Configuration")
    print("=" * 50)
    
    # Initialize logging
    setup_logging(log_level="DEBUG")
    
    # Get loggers for different modules
    main_logger = get_logger(__name__)
    storage_logger = get_logger('core.storage')
    scraper_logger = get_logger('scrapers.test')
    
    main_logger.info("Testing logging initialization - this should appear in console and file")
    main_logger.debug("This is a debug message - should only appear in file")
    main_logger.warning("This is a warning message")
    main_logger.error("This is a test error message - should appear in error log too")
    
    # Test scraper result logging
    log_scraper_result('test_scraper', 'success', count=42)
    log_scraper_result('failed_scraper', 'error', error='Connection timeout')
    
    # Test performance logging
    log_performance('test_operation', 1.23, 'processed 100 items')
    
    # Test storage logging
    try:
        main_logger.info("Testing Storage class logging...")
        storage = Storage()
        
        # This should log connection success
        scrapers = storage.get_enabled_scrapers()
        main_logger.info(f"Retrieved {len(scrapers)} scrapers (with logging)")
        
        # Test saving with logging
        test_result = {
            'scraper_id': 'logging_test',
            'name': 'Logging Test - Demo',
            'count': 123,
            'status': 'success'
        }
        
        success = storage.save_result(test_result)
        main_logger.info(f"Save result test: {'✅ Success' if success else '❌ Failed'}")
        
    except StorageError as e:
        main_logger.error(f"Storage error during logging test: {e}")
    except Exception as e:
        main_logger.error(f"Unexpected error during logging test: {e}")
    
    # Check if log files were created
    log_dir = Path("logs")
    if log_dir.exists():
        log_files = list(log_dir.glob("*.log"))
        main_logger.info(f"Created {len(log_files)} log files:")
        for log_file in log_files:
            size = log_file.stat().st_size
            main_logger.info(f"  - {log_file.name}: {size} bytes")
    else:
        main_logger.warning("No log directory created")
    
    print("\n✅ Logging test completed! Check the logs/ directory for output files.")
    return True


if __name__ == "__main__":
    try:
        test_logging()
    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        sys.exit(1)