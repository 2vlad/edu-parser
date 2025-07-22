#!/usr/bin/env python3
"""
Deployment status checker for Railway deployment.

This script checks the health of the deployed scraper system
and can be used for monitoring and alerting.
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.logging_config import setup_logging, get_logger
from core.storage import Storage


def check_environment() -> Dict[str, Any]:
    """Check environment variables and configuration."""
    checks = {
        'supabase_url': bool(os.getenv('SUPABASE_URL')),
        'supabase_key': bool(os.getenv('SUPABASE_KEY')),
        'scraper_mode': os.getenv('SCRAPER_MODE', 'enabled'),
        'success_threshold': float(os.getenv('SUCCESS_THRESHOLD', '0.7')),
    }
    
    return {
        'status': 'healthy' if all([checks['supabase_url'], checks['supabase_key']]) else 'unhealthy',
        'details': checks,
        'timestamp': datetime.now().isoformat()
    }


def check_database_connection() -> Dict[str, Any]:
    """Check Supabase database connectivity."""
    try:
        storage = Storage()
        
        # Try to connect and perform a simple operation
        # This will validate the connection without making changes
        result = storage.client.table('scraper_results').select('id').limit(1).execute()
        
        return {
            'status': 'healthy',
            'details': {
                'connected': True,
                'response_time_ms': None  # Could add timing if needed
            },
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'details': {
                'connected': False,
                'error': str(e)
            },
            'timestamp': datetime.now().isoformat()
        }


def check_recent_runs() -> Dict[str, Any]:
    """Check for recent successful scraper runs."""
    try:
        storage = Storage()
        
        # Look for runs in the last 24 hours
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        result = storage.client.table('scraper_results')\
            .select('created_at, status, scraper_id')\
            .gte('created_at', cutoff_time.isoformat())\
            .order('created_at', desc=True)\
            .limit(100)\
            .execute()
        
        recent_results = result.data
        
        if not recent_results:
            return {
                'status': 'warning',
                'details': {
                    'recent_runs': 0,
                    'last_run': None,
                    'message': 'No runs in last 24 hours'
                },
                'timestamp': datetime.now().isoformat()
            }
        
        successful_runs = [r for r in recent_results if r.get('status') == 'success']
        success_rate = len(successful_runs) / len(recent_results) * 100
        
        last_run_time = max(recent_results, key=lambda x: x['created_at'])['created_at']
        
        status = 'healthy' if success_rate >= 50 else 'warning' if success_rate >= 25 else 'unhealthy'
        
        return {
            'status': status,
            'details': {
                'recent_runs': len(recent_results),
                'successful_runs': len(successful_runs),
                'success_rate': round(success_rate, 1),
                'last_run': last_run_time,
                'unique_scrapers': len(set(r['scraper_id'] for r in recent_results))
            },
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'details': {
                'error': str(e)
            },
            'timestamp': datetime.now().isoformat()
        }


def check_scraper_registry() -> Dict[str, Any]:
    """Check scraper registry can discover scrapers."""
    try:
        from core.registry import ScraperRegistry
        from core.storage import Storage
        
        storage = Storage()
        registry = ScraperRegistry(storage=storage)
        discovered_count = registry.discover_scrapers()
        
        status = 'healthy' if discovered_count >= 20 else 'warning' if discovered_count >= 10 else 'unhealthy'
        
        return {
            'status': status,
            'details': {
                'discovered_scrapers': discovered_count,
                'expected_minimum': 20
            },
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'details': {
                'error': str(e)
            },
            'timestamp': datetime.now().isoformat()
        }


def generate_status_report() -> Dict[str, Any]:
    """Generate comprehensive status report."""
    logger = get_logger(__name__)
    
    logger.info("Starting deployment status check...")
    
    checks = {
        'environment': check_environment(),
        'database': check_database_connection(),
        'recent_runs': check_recent_runs(),
        'scraper_registry': check_scraper_registry()
    }
    
    # Determine overall status
    statuses = [check['status'] for check in checks.values()]
    
    if 'unhealthy' in statuses:
        overall_status = 'unhealthy'
    elif 'warning' in statuses:
        overall_status = 'warning'
    else:
        overall_status = 'healthy'
    
    report = {
        'overall_status': overall_status,
        'timestamp': datetime.now().isoformat(),
        'checks': checks
    }
    
    logger.info(f"Status check completed: {overall_status}")
    
    return report


def main():
    """Main entry point for status checker."""
    setup_logging(log_level="INFO")
    logger = get_logger(__name__)
    
    try:
        report = generate_status_report()
        
        # Print JSON report
        print(json.dumps(report, indent=2))
        
        # Exit with appropriate code
        if report['overall_status'] == 'unhealthy':
            sys.exit(1)
        elif report['overall_status'] == 'warning':
            sys.exit(2)
        else:
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        print(json.dumps({
            'overall_status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()