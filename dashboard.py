#!/usr/bin/env python3
"""
Monitoring dashboard for the edu-parser scraping system.

Provides a web interface to view scraping results and system health status.
"""

import os
import sys
import csv
import io
from datetime import datetime, timedelta
from typing import Dict, List, Any

from flask import Flask, render_template, jsonify, request, abort, make_response
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
    """Main dashboard view showing data like Google Sheets with 7-day columns."""
    try:
        storage = Storage()
        
        # Get all available dates (not just last 7)
        recent_dates_result = storage.client.table('applicant_counts')\
            .select('date')\
            .eq('status', 'success')\
            .order('date', desc=True)\
            .execute()
        
        # Get unique dates and limit to last 7 for display
        all_unique_dates = sorted(list(set(r['date'] for r in recent_dates_result.data)), reverse=True)
        unique_dates = all_unique_dates[:7]  # Limit to 7 most recent dates for display
        
        if not unique_dates:
            # No data available
            return render_template('dashboard.html',
                date=datetime.now().date(),
                total=0,
                success=0,
                errors=0,
                success_rate=0,
                programs_data={},
                date_columns=[],
                recent_dates=[]
            )
        
        # Get data for all recent dates
        start_date = unique_dates[-1] if unique_dates else datetime.now().date().isoformat()
        end_date = unique_dates[0] if unique_dates else datetime.now().date().isoformat()
        
        all_results = storage.client.table('applicant_counts')\
            .select('*')\
            .gte('date', start_date)\
            .lte('date', end_date)\
            .eq('status', 'success')\
            .order('name')\
            .execute()
        
        # Calculate statistics for today (most recent date)
        today_date = unique_dates[0] if unique_dates else datetime.now().date().isoformat()
        today_results = [r for r in all_results.data if r['date'] == today_date]
        
        total = len(today_results)
        success = len(today_results)  # We only get successful results
        errors = 0  # We'll calculate this separately if needed
        success_rate = 100 if total > 0 else 0
        
        # Organize data by program (like Google Sheets)
        programs_data = {}
        
        for result in all_results.data:
            # Determine university from scraper_id
            scraper_id = result['scraper_id']
            if scraper_id.startswith('hse_'):
                university = 'НИУ ВШЭ'
            elif scraper_id.startswith('mipt_'):
                university = 'МФТИ'
            elif scraper_id.startswith('mephi_'):
                university = 'МИФИ'
            else:
                university = 'Unknown'
            
            program_name = result.get('name', result['scraper_id'])
            
            # Clean program name
            if program_name.startswith('HSE - '):
                program_name = program_name[6:]
            elif program_name.startswith('МФТИ - '):
                program_name = program_name[7:]
            elif program_name.startswith('НИЯУ МИФИ - '):
                program_name = program_name[12:]
            
            program_key = f"{university} - {program_name}"
            
            if program_key not in programs_data:
                programs_data[program_key] = {
                    'university': university,
                    'program': program_name,
                    'counts_by_date': {}
                }
            
            programs_data[program_key]['counts_by_date'][result['date']] = result.get('count', 0)
        
        # Format date columns for display
        date_columns = []
        for date_str in unique_dates:
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                months = ['янв', 'фев', 'мар', 'апр', 'май', 'июн',
                         'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']
                formatted_date = f"{date_obj.day} {months[date_obj.month - 1]}"
                date_columns.append({
                    'date': date_str,
                    'formatted': formatted_date
                })
            except ValueError:
                date_columns.append({
                    'date': date_str,
                    'formatted': date_str
                })
        
        # Calculate growth percentages for each program (earliest to latest)
        for program_key, program_data in programs_data.items():
            counts = program_data['counts_by_date']
            
            # Get all dates with data for this program, sorted chronologically
            program_dates = [d for d in unique_dates if d in counts and counts[d] is not None]
            program_dates.sort()  # Sort chronologically (earliest first)
            
            if len(program_dates) >= 2:
                # Compare earliest vs latest available dates
                earliest_count = counts[program_dates[0]]   # First (earliest) date
                latest_count = counts[program_dates[-1]]    # Last (latest) date
                
                if earliest_count and earliest_count > 0:
                    growth = ((latest_count - earliest_count) / earliest_count) * 100
                    program_data['growth_percentage'] = round(growth, 1)
                    
                    # Store info about date range for debugging
                    program_data['growth_period'] = {
                        'from_date': program_dates[0],
                        'to_date': program_dates[-1],
                        'from_count': earliest_count,
                        'to_count': latest_count
                    }
                else:
                    program_data['growth_percentage'] = None
            else:
                program_data['growth_percentage'] = None
        
        return render_template('dashboard.html',
            date=datetime.strptime(today_date, '%Y-%m-%d').date() if unique_dates else datetime.now().date(),
            total=total,
            success=success,
            errors=errors,
            success_rate=success_rate,
            programs_data=programs_data,
            date_columns=date_columns,
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
                
                # Run scrapers using subprocess to avoid signal issues
                logger.info("Starting manual scraper run via subprocess")
                import subprocess
                import os
                
                # Use subprocess to run scrapers in separate process
                # Use sys.executable to get the correct Python path
                import sys
                result = subprocess.run([
                    sys.executable, 'main.py'
                ], cwd=os.getcwd(), capture_output=True, text=True, timeout=600)  # 10 minute timeout
                
                if result.returncode == 0:
                    logger.info("Manual scraper run completed successfully")
                else:
                    logger.error(f"Scraper run failed with code {result.returncode}")
                    logger.error(f"STDOUT: {result.stdout}")
                    logger.error(f"STDERR: {result.stderr}")
                
                # Auto-cleanup any duplicates that might have been created
                logger.info("Cleaning up any duplicate records")
                try:
                    from cleanup_applicant_duplicates import cleanup_duplicates
                    cleanup_duplicates()
                    logger.info("Duplicate cleanup completed")
                except Exception as cleanup_error:
                    logger.error(f"Cleanup error: {cleanup_error}")
                
                # Update dynamic Google Sheets if configured
                try:
                    from core.dynamic_sheets import update_dynamic_sheets
                    logger.info("Updating dynamic Google Sheets...")
                    
                    if update_dynamic_sheets():
                        logger.info("✅ Successfully updated dynamic Google Sheets")
                    else:
                        logger.warning("⚠️ Dynamic Google Sheets update skipped (not configured)")
                except Exception as e:
                    logger.error(f"Dynamic Google Sheets update error: {e}")
                    # Don't fail the manual run if sheets sync fails
                
            except subprocess.TimeoutExpired:
                logger.error("Scraper run timed out after 10 minutes")
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


@app.route('/api/export-csv')
@require_access
def export_csv():
    """Export applicant data as CSV file."""
    try:
        storage = Storage()
        
        # Get date range (last 7 days by default, or specific date from query)
        date_param = request.args.get('date')
        if date_param:
            # Export specific date
            target_date = date_param
            date_filter = target_date
        else:
            # Export last 7 days
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=6)
            date_filter = None
        
        # Get data from database
        if date_filter:
            # Single date
            result = storage.client.table('applicant_counts')\
                .select('*')\
                .eq('date', date_filter)\
                .order('name')\
                .execute()
        else:
            # Date range
            result = storage.client.table('applicant_counts')\
                .select('*')\
                .gte('date', start_date.isoformat())\
                .lte('date', end_date.isoformat())\
                .order('name')\
                .execute()
        
        if not result.data:
            return jsonify({'error': 'No data found for the specified date(s)'}), 404
        
        # Group data by university and program
        programs_data = {}
        dates = set()
        
        for record in result.data:
            if record['status'] != 'success' or not record['count']:
                continue
                
            # Determine university from scraper_id or name
            scraper_id = record['scraper_id']
            name = record.get('name', scraper_id)
            
            if scraper_id.startswith('hse_'):
                university = 'НИУ ВШЭ'
            elif scraper_id.startswith('mipt_'):
                university = 'МФТИ'
            elif scraper_id.startswith('mephi_'):
                university = 'МИФИ'
            else:
                university = record.get('university', 'Unknown')
            
            program_key = f"{university} - {name}"
            date_str = record['date']
            dates.add(date_str)
            
            if program_key not in programs_data:
                programs_data[program_key] = {
                    'university': university,
                    'program': name,
                    'url': '',  # We don't store URLs in applicant_counts table
                    'counts_by_date': {}
                }
            
            programs_data[program_key]['counts_by_date'][date_str] = record['count']
        
        # Sort dates
        sorted_dates = sorted(list(dates))
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        header = ['вуз', 'программа']
        for date_str in sorted_dates:
            # Format date as "DD месяц"
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            months = ['янв', 'фев', 'мар', 'апр', 'май', 'июн',
                     'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']
            formatted_date = f"{date_obj.day} {months[date_obj.month - 1]}"
            header.append(formatted_date)
        
        if len(header) > 2:  # Only write if we have date columns
            header.append('URL')  # Add URL column at the end
        
        writer.writerow(header)
        
        # Write data rows
        for program_key in sorted(programs_data.keys()):
            program_data = programs_data[program_key]
            row = [
                program_data['university'],
                program_data['program']
            ]
            
            # Add counts for each date
            for date_str in sorted_dates:
                count = program_data['counts_by_date'].get(date_str, '')
                row.append(count)
            
            # Add URL (empty for now, could be enhanced later)
            if len(header) > 2:
                row.append('')
            
            writer.writerow(row)
        
        # Prepare response
        output.seek(0)
        csv_data = output.getvalue()
        output.close()
        
        # Create response with proper headers
        response = make_response(csv_data)
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        
        # Generate filename
        if date_filter:
            filename = f"applicant_data_{date_filter}.csv"
        else:
            filename = f"applicant_data_{start_date}_to_{end_date}.csv"
        
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        logger.info(f"CSV export completed: {len(programs_data)} programs, {len(sorted_dates)} dates")
        return response
        
    except Exception as e:
        logger.error(f"CSV export error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/sync-to-sheets', methods=['POST'])
@require_access
def sync_to_sheets():
    """Manually sync data to Google Sheets."""
    try:
        import threading
        from datetime import date
        
        # Get date parameter in main thread (before background execution)
        date_param = request.json.get('date') if request.json else None
        
        def sync_background():
            try:
                # Get date parameter or use today (passed from main thread)
                target_date = date_param or date.today().isoformat()
                
                logger.info(f"Starting manual dynamic Google Sheets update for {target_date}")
                
                from core.dynamic_sheets import update_dynamic_sheets
                
                if update_dynamic_sheets(target_date):
                    logger.info(f"✅ Successfully updated dynamic Google Sheets for {target_date}")
                else:
                    logger.warning(f"⚠️ Dynamic Google Sheets update skipped for {target_date} (not configured or no data)")
                
            except Exception as e:
                logger.error(f"Error in manual Google Sheets sync: {e}")
        
        # Run sync in background
        thread = threading.Thread(target=sync_background)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'status': 'started',
            'message': 'Google Sheets sync started. Check logs for results.'
        })
        
    except Exception as e:
        logger.error(f"Sync to sheets error: {e}")
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
    
    # Log all environment variables related to WEB_PORT (renamed from PORT to avoid Railway conflicts)
    web_port_env = os.environ.get('WEB_PORT')
    port_env = os.environ.get('PORT')  # Keep for debugging Railway issue
    logger.info(f"🔍 DEBUG: WEB_PORT environment variable = '{web_port_env}' (type: {type(web_port_env)})")
    logger.info(f"🔍 DEBUG: PORT environment variable = '{port_env}' (type: {type(port_env)})")
    
    # Log other relevant env vars
    flask_debug = os.environ.get('FLASK_DEBUG')
    scraper_mode = os.environ.get('SCRAPER_MODE')
    cache_buster = os.environ.get('CACHE_BUSTER')
    logger.info(f"🔍 DEBUG: FLASK_DEBUG = '{flask_debug}'")
    logger.info(f"🔍 DEBUG: SCRAPER_MODE = '{scraper_mode}'")
    logger.info(f"🔍 DEBUG: CACHE_BUSTER = '{cache_buster}'")
    
    # Check if we're being imported vs run directly
    logger.info(f"🔍 DEBUG: __name__ = '{__name__}'")
    
    # **CRITICAL FIX:** Use WEB_PORT instead of PORT to avoid Railway conflicts
    try:
        # First try WEB_PORT (our custom variable)
        if web_port_env and web_port_env.isdigit():
            port = int(web_port_env)
            logger.info(f"🔧 SUCCESS: Using WEB_PORT = {port}")
        # Then try PORT but with careful handling
        elif port_env and port_env != '$PORT' and port_env != "'$PORT'" and port_env != '"$PORT"':
            try:
                port = int(port_env)
                logger.info(f"🔍 DEBUG: Successfully parsed PORT = {port}")
            except (ValueError, TypeError):
                port = 8080
                logger.info(f"🔧 FALLBACK: PORT parse failed, using default: {port}")
        else:
            port = 8080
            if port_env == '$PORT' or port_env == "'$PORT'" or port_env == '"$PORT"':
                logger.error(f"🚨 CRITICAL: PORT env var contains literal '$PORT' string: '{port_env}'")
                logger.error(f"🚨 CRITICAL: This confirms Railway environment variable substitution bug!")
            logger.info(f"🔧 FALLBACK: Using default port: {port}")
    except Exception as e:
        port = 8080
        logger.error(f"🚨 ERROR: Port determination failed: {e}")
        logger.info(f"🔧 EMERGENCY: Using hardcoded port: {port}")
    
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