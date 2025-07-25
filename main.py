#!/usr/bin/env python3
"""
Main entry point for the edu-parser scraper system.

This script serves as the primary cron job entry point that orchestrates
the entire scraping process using the registry and runner components.
"""

import os
import sys
import time
import signal
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.logging_config import setup_logging, get_logger, log_performance
from core.storage import Storage
from core.registry import ScraperRegistry, get_all_scrapers
from core.runner import ScraperRunner


def setup_signal_handlers():
    """Set up signal handlers for graceful shutdown."""
    def signal_handler(signum, frame):
        logger = get_logger(__name__)
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def validate_environment():
    """Validate that all required environment variables are set."""
    logger = get_logger(__name__)
    
    required_vars = ['SUPABASE_URL', 'SUPABASE_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        logger.error("Please set these variables in your .env file or environment")
        return False
    
    logger.info("Environment validation passed")
    return True


def initialize_components():
    """Initialize storage, registry, and runner components."""
    logger = get_logger(__name__)
    
    try:
        # Initialize storage
        logger.info("Initializing storage component...")
        storage = Storage()
        
        # Initialize registry and discover scrapers
        logger.info("Initializing scraper registry...")
        registry = ScraperRegistry(storage=storage)
        discovered = registry.discover_scrapers()
        logger.info(f"Registry discovered {discovered} scrapers")
        
        # Initialize runner
        logger.info("Initializing scraper runner...")
        runner = ScraperRunner(storage=storage, max_workers=5)
        
        return storage, registry, runner
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        raise


def run_scrapers(registry: ScraperRegistry, runner: ScraperRunner, mode: str = "enabled") -> List[Dict[str, Any]]:
    """
    Run scrapers based on the specified mode.
    
    Args:
        registry: ScraperRegistry instance
        runner: ScraperRunner instance  
        mode: "enabled" to run only enabled scrapers, "all" to run all discovered scrapers
        
    Returns:
        List of scraper results
    """
    logger = get_logger(__name__)
    
    if mode == "enabled":
        logger.info("Loading enabled scrapers from database...")
        scrapers = registry.load_enabled_scrapers()
    else:
        logger.info("Loading all discovered scrapers...")
        scrapers = registry.get_all_discovered_scrapers()
    
    if not scrapers:
        logger.warning(f"No scrapers found in {mode} mode")
        return []
    
    logger.info(f"Found {len(scrapers)} scrapers to run in {mode} mode")
    
    # Log scraper details
    for i, (func, config) in enumerate(scrapers[:5], 1):  # Show first 5
        scraper_id = config.get('scraper_id', 'unknown')
        name = config.get('name', 'Unknown')
        logger.info(f"  {i}. {scraper_id}: {name}")
    
    if len(scrapers) > 5:
        logger.info(f"  ... and {len(scrapers) - 5} more scrapers")
    
    # Run all scrapers
    start_time = time.time()
    results = runner.run_all_scrapers(scrapers)
    duration = time.time() - start_time
    
    log_performance("main_scraping_session", duration, f"scrapers={len(scrapers)}, mode={mode}")
    
    return results


def analyze_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze scraper results and generate summary statistics.
    
    Args:
        results: List of scraper results
        
    Returns:
        Summary statistics dictionary
    """
    if not results:
        return {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'success_rate': 0.0,
            'total_applicants': 0,
            'errors': []
        }
    
    successful = [r for r in results if r.get('status') == 'success']
    failed = [r for r in results if r.get('status') == 'error']
    
    total_applicants = 0
    for result in successful:
        count = result.get('count')
        if count is not None and isinstance(count, (int, float)):
            total_applicants += count
    
    error_details = []
    for result in failed:
        error_details.append({
            'scraper_id': result.get('scraper_id', 'unknown'),
            'name': result.get('name', 'Unknown'),
            'error': result.get('error', 'Unknown error')
        })
    
    return {
        'total': len(results),
        'successful': len(successful),
        'failed': len(failed),
        'success_rate': len(successful) / len(results) * 100,
        'total_applicants': total_applicants,
        'errors': error_details
    }


def main():
    """Main entry point for the scraper system."""
    # Set up logging first
    setup_logging(log_level="INFO")
    logger = get_logger(__name__)
    
    # Detailed environment debugging for main.py
    logger.info("🔍 DEBUG: main.py execution started")
    logger.info(f"🔍 DEBUG: __file__ = {__file__}")
    logger.info(f"🔍 DEBUG: sys.argv = {sys.argv}")
    logger.info(f"🔍 DEBUG: Current working directory = {os.getcwd()}")
    logger.info(f"🔍 DEBUG: Python path = {sys.path[:3]}...")  # Show first 3 paths
    
    # Check PORT variable in main.py environment
    port_env = os.environ.get('PORT')
    logger.info(f"🔍 DEBUG: PORT environment variable in main.py = '{port_env}' (type: {type(port_env)})")
    
    # Check all environment variables that might be relevant
    relevant_vars = ['PORT', 'FLASK_DEBUG', 'SCRAPER_MODE', 'RAILWAY_CRON_SCHEDULE', 'PYTHONPATH']
    for var in relevant_vars:
        value = os.environ.get(var)
        logger.info(f"🔍 DEBUG: {var} = '{value}'")
    
    # Check if any Flask-related modules are imported
    flask_modules = [module for module in sys.modules.keys() if 'flask' in module.lower()]
    if flask_modules:
        logger.warning(f"🚨 DEBUG: Flask modules detected in main.py: {flask_modules}")
    else:
        logger.info("🔍 DEBUG: No Flask modules detected in main.py (good)")
    
    # Set up signal handlers
    setup_signal_handlers()
    
    # Read version for logging
    try:
        with open('VERSION', 'r') as f:
            version = f.read().strip()
    except:
        version = 'unknown'
    
    logger.info("=" * 80)
    logger.info("🚀 STARTING EDU-PARSER SCRAPING SESSION 🚀")
    logger.info(f"🚀 VERSION: {version}")
    logger.info(f"🚀 TIMESTAMP: {datetime.now().isoformat()}")
    logger.info(f"🚀 CACHE_BUSTER: {os.environ.get('CACHE_BUSTER', 'none')}")
    logger.info(f"🚀 EXPECTED SCRAPERS: 36 (23 HSE + 7 MIPT + 6 MEPhI)")
    logger.info("=" * 80)
    
    session_start_time = time.time()
    
    try:
        # Validate environment
        if not validate_environment():
            sys.exit(1)
        
        # Initialize components
        storage, registry, runner = initialize_components()
        
        # Determine run mode (can be set via environment variable)
        run_mode = os.getenv('SCRAPER_MODE', 'enabled').lower()
        if run_mode not in ['enabled', 'all']:
            logger.warning(f"Invalid SCRAPER_MODE '{run_mode}', defaulting to 'enabled'")
            run_mode = 'enabled'
        
        logger.info(f"Running in '{run_mode}' mode")
        
        # Run scrapers
        results = run_scrapers(registry, runner, run_mode)
        
        if not results:
            logger.warning("No results obtained from scrapers")
            sys.exit(1)
        
        # Analyze results
        summary = analyze_results(results)
        
        # Log comprehensive summary
        logger.info("-" * 60)
        logger.info("SCRAPING SESSION SUMMARY")
        logger.info("-" * 60)
        logger.info(f"Total scrapers: {summary['total']}")
        logger.info(f"Successful: {summary['successful']}")
        logger.info(f"Failed: {summary['failed']}")
        logger.info(f"Success rate: {summary['success_rate']:.1f}%")
        logger.info(f"Total applicants found: {summary['total_applicants']:,}")
        
        session_duration = time.time() - session_start_time
        logger.info(f"Session duration: {session_duration:.2f}s")
        
        # Log errors if any
        if summary['errors']:
            logger.error(f"Errors encountered in {len(summary['errors'])} scrapers:")
            for error in summary['errors'][:10]:  # Show first 10 errors
                logger.error(f"  - {error['scraper_id']}: {error['error']}")
            if len(summary['errors']) > 10:
                logger.error(f"  ... and {len(summary['errors']) - 10} more errors")
        
        # Determine exit code based on success rate
        success_threshold = float(os.getenv('SUCCESS_THRESHOLD', '0.7'))  # 70% by default
        if summary['success_rate'] < success_threshold * 100:
            logger.error(f"Success rate {summary['success_rate']:.1f}% below threshold {success_threshold * 100}%")
            logger.error("Marking this run as failed")
            sys.exit(1)
        
        # Sync to Google Sheets if configured
        sheets_sync_success = False
        try:
            from core.dynamic_sheets import update_dynamic_sheets
            logger.info("Attempting to update dynamic Google Sheets...")
            
            if update_dynamic_sheets():
                logger.info("✅ Successfully updated dynamic Google Sheets")
                sheets_sync_success = True
            else:
                logger.warning("⚠️ Dynamic Google Sheets update skipped (not configured or failed)")
        except Exception as e:
            logger.error(f"Dynamic Google Sheets update error: {e}")
            # Don't fail the entire run if sheets sync fails
        
        # Verify sync if it was successful
        if sheets_sync_success:
            try:
                logger.info("🔍 Verifying Google Sheets sync...")
                import subprocess
                import sys
                
                # Run verification script
                result = subprocess.run([
                    sys.executable, 'verify_sheets_sync.py', date.today().isoformat()
                ], cwd=os.getcwd(), capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    logger.info("✅ Google Sheets sync verification: PASSED")
                else:
                    logger.warning("⚠️ Google Sheets sync verification: ISSUES DETECTED")
                    logger.warning(f"Verification output: {result.stdout}")
                    
            except subprocess.TimeoutExpired:
                logger.warning("⚠️ Google Sheets sync verification timed out")
            except Exception as e:
                logger.warning(f"⚠️ Google Sheets sync verification error: {e}")
                # Don't fail if verification fails
        
        logger.info("=" * 60)
        logger.info("SCRAPING SESSION COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        
    except KeyboardInterrupt:
        logger.info("Scraping session interrupted by user")
        sys.exit(130)
    except Exception as e:
        session_duration = time.time() - session_start_time
        logger.error(f"FATAL ERROR in scraping session: {e}")
        logger.error(f"Session failed after {session_duration:.2f}s")
        
        # Log full traceback for debugging
        import traceback
        logger.error("Full traceback:")
        logger.error(traceback.format_exc())
        
        sys.exit(1)


if __name__ == "__main__":
    main()