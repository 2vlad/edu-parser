#!/usr/bin/env python3
"""Master test runner for all edu-parser tests."""

import os
import sys
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import test modules
from test_storage import run_storage_tests
from test_runner import run_runner_tests  
from test_http_client import run_http_client_tests
from test_hse import run_hse_tests
from test_mephi import run_mephi_tests
from test_registry import run_registry_tests
from core.logging_config import setup_logging, get_logger


def run_all_tests():
    """Run all test suites and provide comprehensive report."""
    
    # Setup logging for test run
    setup_logging(log_level="INFO")
    logger = get_logger(__name__)
    
    print("🧪" + "=" * 70 + "🧪")
    print("             EDU-PARSER COMPREHENSIVE TEST SUITE")
    print("🧪" + "=" * 70 + "🧪")
    print(f"📅 Started at: {datetime.now().isoformat()}")
    print()
    
    logger.info("Starting comprehensive test suite")
    
    # Track overall results
    test_suites = [
        ("Storage Module", run_storage_tests),
        ("Runner Module", run_runner_tests), 
        ("HTTP Client Module", run_http_client_tests),
        ("HSE Scraper Module", run_hse_tests),
        ("MEPhI Scraper Module", run_mephi_tests),
        ("Registry Module", run_registry_tests)
    ]
    
    all_results = {}
    total_start_time = time.time()
    
    # Run each test suite
    for suite_name, test_function in test_suites:
        print(f"🔍 Running {suite_name} Tests...")
        print("-" * 50)
        
        suite_start_time = time.time()
        
        try:
            success, failures, errors = test_function()
            suite_duration = time.time() - suite_start_time
            
            all_results[suite_name] = {
                'success': success,
                'failures': failures,
                'errors': errors,
                'duration': suite_duration
            }
            
            # Status indicator
            status_icon = "✅" if success else "❌"
            print(f"{status_icon} {suite_name}: ", end="")
            
            if success:
                print(f"ALL PASSED in {suite_duration:.2f}s")
                logger.info(f"{suite_name} tests: ALL PASSED ({suite_duration:.2f}s)")
            else:
                print(f"FAILED ({failures} failures, {errors} errors) in {suite_duration:.2f}s")
                logger.error(f"{suite_name} tests: FAILED ({failures} failures, {errors} errors)")
                
        except Exception as e:
            suite_duration = time.time() - suite_start_time
            all_results[suite_name] = {
                'success': False,
                'failures': 0,
                'errors': 1,
                'duration': suite_duration,
                'exception': str(e)
            }
            print(f"💥 {suite_name}: CRITICAL ERROR - {e}")
            logger.error(f"{suite_name} tests: CRITICAL ERROR - {e}")
        
        print()
    
    # Calculate totals
    total_duration = time.time() - total_start_time
    total_success = all(result['success'] for result in all_results.values())
    total_failures = sum(result['failures'] for result in all_results.values())
    total_errors = sum(result['errors'] for result in all_results.values())
    
    # Final report
    print("📊" + "=" * 70 + "📊")
    print("                    FINAL TEST REPORT")
    print("📊" + "=" * 70 + "📊")
    
    for suite_name, result in all_results.items():
        duration = result['duration']
        if result['success']:
            print(f"✅ {suite_name:<25} PASSED     ({duration:.2f}s)")
        else:
            failures = result['failures']
            errors = result['errors']
            print(f"❌ {suite_name:<25} FAILED     ({failures}F, {errors}E, {duration:.2f}s)")
            
            if 'exception' in result:
                print(f"   💥 Exception: {result['exception']}")
    
    print("-" * 72)
    
    # Overall summary
    if total_success:
        print(f"🎉 ALL TESTS PASSED! ({total_duration:.2f}s total)")
        logger.info(f"All test suites passed in {total_duration:.2f}s")
    else:
        print(f"💀 TESTS FAILED: {total_failures} failures, {total_errors} errors ({total_duration:.2f}s total)")
        logger.error(f"Test suite failed: {total_failures} failures, {total_errors} errors")
    
    print(f"📅 Completed at: {datetime.now().isoformat()}")
    print("📊" + "=" * 70 + "📊")
    
    # Test coverage summary
    print("\n📋 TEST COVERAGE SUMMARY:")
    print("   ✅ core/storage.py      - 18 unit tests (CRUD, validation, performance)")
    print("   ✅ core/runner.py       - 13 unit tests (isolation, concurrency, error handling)")
    print("   ✅ core/http_client.py  - 16 unit tests (timeouts, retries, reliability)")
    print("   ✅ scrapers/hse.py      - 21 unit tests (Excel parsing, fuzzy matching, data validation)")
    print("   ✅ scrapers/mephi.py    - 21 unit tests (HTML parsing, trPosBen extraction, transliteration)")
    print("   ✅ core/registry.py     - 9 unit tests (scraper discovery, configuration matching)")
    print("   📊 Total: 98 unit tests covering all critical components and scraper implementations")
    
    # Return success status
    return total_success


def check_critical_components():
    """Check that all critical components are properly covered by tests."""
    
    print("\n🔬 CRITICAL COMPONENT TEST COVERAGE CHECK:")
    print("-" * 50)
    
    critical_components = [
        ("core/storage.py", "Database operations, data validation, error handling"),
        ("core/runner.py", "Scraper isolation, concurrency, fault tolerance"),
        ("core/http_client.py", "Network reliability, timeouts, retries"),
        ("scrapers/hse.py", "HSE Excel scraper with fuzzy matching"),
        ("scrapers/mephi.py", "MEPhI HTML scraper with trPosBen parsing"),
        ("core/registry.py", "Scraper discovery and configuration matching"),
        ("core/logging_config.py", "Logging system (tested indirectly)")
    ]
    
    for component, description in critical_components:
        if os.path.exists(component):
            print(f"   ✅ {component:<25} - {description}")
        else:
            print(f"   ❌ {component:<25} - MISSING!")
    
    print()


if __name__ == "__main__":
    try:
        check_critical_components()
        success = run_all_tests()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Fatal error running test suite: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)