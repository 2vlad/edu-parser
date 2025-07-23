#!/usr/bin/env python3
"""
Monitoring dashboard for the edu-parser scraping system.

Provides a web interface to view scraping results and system health status.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any

from flask import Flask, render_template, jsonify, request, abort
from functools import wraps
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.storage import Storage
from core.logging_config import setup_logging, get_logger

# Load environment variables
load_dotenv()

# Set up logging
setup_logging(log_level="INFO")
logger = get_logger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['JSON_SORT_KEYS'] = False


def check_access():
    """Check if access is allowed based on IP restrictions."""
    # If no restrictions are set, allow all
    allowed_ips = os.environ.get('DASHBOARD_ALLOWED_IPS', '')
    if not allowed_ips:
        return True
    
    # Get client IP
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ',' in client_ip:
        # Take the first IP if there are multiple (proxy chain)
        client_ip = client_ip.split(',')[0].strip()
    
    # Check if client IP is in allowed list
    allowed_list = [ip.strip() for ip in allowed_ips.split(',')]
    
    # Special case for localhost/development
    if client_ip in ['127.0.0.1', '::1', 'localhost']:
        return True
    
    return client_ip in allowed_list


def require_access(f):
    """Decorator to require access check for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not check_access():
            logger.warning(f"Access denied for IP: {request.remote_addr}")
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
@require_access
def dashboard():
    """Main dashboard view showing today's scraping results."""
    try:
        storage = Storage()
        
        # Get date from query parameter or use today
        date_str = request.args.get('date')
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                target_date = datetime.now().date()
        else:
            target_date = datetime.now().date()
        
        # Get results for the target date
        results = storage.client.table('applicant_counts')\
            .select('*')\
            .eq('date', target_date.isoformat())\
            .order('name')\
            .execute()
        
        # Calculate statistics
        total = len(results.data)
        success = sum(1 for r in results.data if r['status'] == 'success')
        errors = sum(1 for r in results.data if r['status'] == 'error')
        success_rate = (success / total * 100) if total > 0 else 0
        
        # Group results by university
        by_university = {}
        for result in results.data:
            # Extract university and program from name
            parts = result['name'].split(' - ')
            if len(parts) >= 2:
                university = parts[0]
                program = ' - '.join(parts[1:])
            else:
                university = 'Unknown'
                program = result['name']
            
            if university not in by_university:
                by_university[university] = []
            
            result['university'] = university
            result['program'] = program
            by_university[university].append(result)
        
        # Get recent dates for navigation
        recent_dates = storage.client.table('applicant_counts')\
            .select('date')\
            .order('date', desc=True)\
            .limit(30)\
            .execute()
        
        unique_dates = sorted(list(set(r['date'] for r in recent_dates.data)), reverse=True)[:7]
        
        return render_template('dashboard.html',
            date=target_date,
            total=total,
            success=success,
            errors=errors,
            success_rate=success_rate,
            results_by_university=by_university,
            recent_dates=unique_dates
        )
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return render_template('error.html', error=str(e)), 500


@app.route('/health')
def health():
    """Health check endpoint for monitoring."""
    try:
        storage = Storage()
        
        # Check if we have recent data (within last 48 hours)
        cutoff_date = (datetime.now() - timedelta(days=2)).date()
        
        result = storage.client.table('applicant_counts')\
            .select('date, status')\
            .gte('date', cutoff_date.isoformat())\
            .order('date', desc=True)\
            .limit(1)\
            .execute()
        
        if result.data:
            last_run = result.data[0]['date']
            
            # Check database connectivity
            db_healthy = True
            try:
                # Simple query to test connection
                storage.client.table('scrapers_config').select('scraper_id').limit(1).execute()
            except:
                db_healthy = False
            
            # Read version info
            try:
                with open('VERSION', 'r') as f:
                    version = f.read().strip()
            except:
                version = 'unknown'
            
            return jsonify({
                'status': 'healthy' if db_healthy else 'degraded',
                'version': version,
                'last_run': last_run,
                'database': 'connected' if db_healthy else 'error',
                'timestamp': datetime.now().isoformat(),
                'cache_buster': os.environ.get('CACHE_BUSTER', 'none'),
                'git_commit': os.environ.get('RAILWAY_GIT_COMMIT_SHA', 'unknown')[:8] if os.environ.get('RAILWAY_GIT_COMMIT_SHA') else 'unknown'
            })
        else:
            return jsonify({
                'status': 'unhealthy',
                'error': 'No recent data found',
                'timestamp': datetime.now().isoformat()
            }), 503
            
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503


@app.route('/api/stats')
@require_access
def api_stats():
    """API endpoint for getting statistics."""
    try:
        storage = Storage()
        
        # Get statistics for the last 7 days
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=6)
        
        results = storage.client.table('applicant_counts')\
            .select('date, status, count')\
            .gte('date', start_date.isoformat())\
            .lte('date', end_date.isoformat())\
            .execute()
        
        # Aggregate by date
        stats_by_date = {}
        for result in results.data:
            date = result['date']
            if date not in stats_by_date:
                stats_by_date[date] = {
                    'total': 0,
                    'success': 0,
                    'error': 0,
                    'total_applicants': 0
                }
            
            stats_by_date[date]['total'] += 1
            if result['status'] == 'success':
                stats_by_date[date]['success'] += 1
                if result['count']:
                    stats_by_date[date]['total_applicants'] += result['count']
            else:
                stats_by_date[date]['error'] += 1
        
        # Convert to list and sort by date
        stats_list = []
        for date, stats in stats_by_date.items():
            stats['date'] = date
            stats['success_rate'] = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
            stats_list.append(stats)
        
        stats_list.sort(key=lambda x: x['date'])
        
        return jsonify({
            'stats': stats_list,
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Stats API error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/scrapers')
@require_access
def api_scrapers():
    """API endpoint for getting scraper configuration."""
    try:
        storage = Storage()
        
        scrapers = storage.client.table('scrapers_config')\
            .select('*')\
            .order('name')\
            .execute()
        
        return jsonify({
            'scrapers': scrapers.data,
            'total': len(scrapers.data),
            'enabled': sum(1 for s in scrapers.data if s.get('enabled', False))
        })
        
    except Exception as e:
        logger.error(f"Scrapers API error: {e}")
        return jsonify({'error': str(e)}), 500




@app.route('/api/run-all-scrapers', methods=['POST'])
@require_access
def run_all_scrapers():
    """Run all scrapers manually and overwrite today's data."""
    try:
        import threading
        from datetime import date
        # Import main lazily to avoid startup issues
# from main import main as run_scrapers
        
        def run_scrapers_background():
            try:
                # First, delete today's data
                today = date.today().isoformat()
                storage = Storage()
                
                # Delete existing records for today
                existing = storage.client.table('applicant_counts')\
                    .select('id')\
                    .eq('date', today)\
                    .execute()
                
                if existing.data:
                    ids_to_delete = [record['id'] for record in existing.data]
                    storage.client.table('applicant_counts')\
                        .delete()\
                        .in_('id', ids_to_delete)\
                        .execute()
                    logger.info(f"Deleted {len(ids_to_delete)} existing records for {today}")
                
                # Run scrapers with lazy import
                logger.info("Starting manual scraper run")
                from main import main as run_scrapers_func
                run_scrapers_func()
                logger.info("Manual scraper run completed")
                
            except Exception as e:
                logger.error(f"Error in manual scraper run: {e}")
        
        # Run in background
        thread = threading.Thread(target=run_scrapers_background)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'status': 'started',
            'message': 'Scrapers started. Data will be updated in a few minutes.'
        })
        
    except Exception as e:
        logger.error(f"Run all scrapers error: {e}")
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return render_template('error.html', error="Internal server error"), 500


if __name__ == '__main__':
    # Detailed PORT debugging
    logger.info("🔍 DEBUG: Starting dashboard.py main execution")
    logger.info(f"🔍 DEBUG: __file__ = {__file__}")
    logger.info(f"🔍 DEBUG: sys.argv = {sys.argv}")
    
    # Read version info
    try:
        with open('VERSION', 'r') as f:
            version = f.read().strip()
        logger.info(f"🚀 DASHBOARD VERSION: {version}")
    except:
        logger.info("🚀 DASHBOARD VERSION: unknown")
    
    # Log all environment variables related to PORT
    port_env = os.environ.get('PORT')
    logger.info(f"🔍 DEBUG: Raw PORT environment variable = '{port_env}' (type: {type(port_env)})")
    
    # Log other relevant env vars
    flask_debug = os.environ.get('FLASK_DEBUG')
    scraper_mode = os.environ.get('SCRAPER_MODE')
    cache_buster = os.environ.get('CACHE_BUSTER')
    logger.info(f"🔍 DEBUG: FLASK_DEBUG = '{flask_debug}'")
    logger.info(f"🔍 DEBUG: SCRAPER_MODE = '{scraper_mode}'")
    logger.info(f"🔍 DEBUG: CACHE_BUSTER = '{cache_buster}'")
    
    # Check if we're being imported vs run directly
    logger.info(f"🔍 DEBUG: __name__ = '{__name__}'")
    
    # **CRITICAL FIX:** Handle PORT parsing very carefully
    try:
        # If PORT is the literal string '$PORT', Railway has a bug
        if port_env == '$PORT' or port_env == "'$PORT'" or port_env == '"$PORT"':
            logger.error(f"🚨 CRITICAL: PORT env var contains literal '$PORT' string: '{port_env}'")
            logger.error(f"🚨 CRITICAL: This is a Railway environment variable substitution bug!")
            port = 8080
            logger.info(f"🔧 FIXED: Using hardcoded port 8080 to bypass Railway bug")
        elif port_env is None or port_env == '':
            port = 8080
            logger.info(f"🔍 DEBUG: PORT env var is None/empty, using default: {port}")
        else:
            # Try to parse as integer
            port = int(port_env)
            logger.info(f"🔍 DEBUG: Successfully parsed PORT = {port}")
    except (ValueError, TypeError) as e:
        port = 8080
        logger.error(f"🚨 DEBUG: Failed to parse PORT '{port_env}': {e}")
        logger.info(f"🔧 FIXED: Using default port: {port}")
    
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"🚀 Starting dashboard on port {port} (debug={debug})")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=debug)
    except Exception as e:
        logger.error(f"🚨 CRITICAL: Failed to start Flask app: {e}")
        logger.error(f"🚨 CRITICAL: Attempted to use port: {port}")
        logger.error(f"🚨 CRITICAL: Original PORT env: '{port_env}'")
        # Don't re-raise - try to continue
        import time
        time.sleep(10)  # Wait before exit to see logs