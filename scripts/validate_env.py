#!/usr/bin/env python3
"""
Environment variable validation script.

This script validates all required and optional environment variables
for the edu-parser system. Useful for deployment verification.
"""

import os
import sys
from typing import Dict, List, Tuple, Any
from urllib.parse import urlparse


def validate_required_vars() -> List[Tuple[str, bool, str]]:
    """Validate required environment variables."""
    validations = []
    
    # SUPABASE_URL
    supabase_url = os.getenv('SUPABASE_URL', '').strip()
    if not supabase_url:
        validations.append(('SUPABASE_URL', False, 'Missing required environment variable'))
    elif not supabase_url.startswith('https://'):
        validations.append(('SUPABASE_URL', False, 'Must start with https://'))
    elif '.supabase.co' not in supabase_url:
        validations.append(('SUPABASE_URL', False, 'Must be a valid Supabase URL'))
    else:
        try:
            parsed = urlparse(supabase_url)
            if not parsed.netloc:
                validations.append(('SUPABASE_URL', False, 'Invalid URL format'))
            else:
                validations.append(('SUPABASE_URL', True, f'Valid URL: {parsed.netloc}'))
        except Exception as e:
            validations.append(('SUPABASE_URL', False, f'URL parsing error: {e}'))
    
    # SUPABASE_KEY
    supabase_key = os.getenv('SUPABASE_KEY', '').strip()
    if not supabase_key:
        validations.append(('SUPABASE_KEY', False, 'Missing required environment variable'))
    elif len(supabase_key) < 100:
        validations.append(('SUPABASE_KEY', False, 'Key appears too short (should be ~100+ characters)'))
    elif not supabase_key.startswith('eyJ'):
        validations.append(('SUPABASE_KEY', False, 'Key should start with "eyJ" (JWT format)'))
    else:
        # Mask key for security
        masked_key = supabase_key[:10] + '*' * (len(supabase_key) - 20) + supabase_key[-10:]
        validations.append(('SUPABASE_KEY', True, f'Valid key format: {masked_key}'))
    
    return validations


def validate_optional_vars() -> List[Tuple[str, bool, str]]:
    """Validate optional environment variables."""
    validations = []
    
    # SCRAPER_MODE
    scraper_mode = os.getenv('SCRAPER_MODE', 'enabled').lower().strip()
    if scraper_mode not in ['enabled', 'all']:
        validations.append(('SCRAPER_MODE', False, f'Invalid value "{scraper_mode}", must be "enabled" or "all"'))
    else:
        validations.append(('SCRAPER_MODE', True, f'Valid mode: {scraper_mode}'))
    
    # SUCCESS_THRESHOLD
    try:
        threshold = float(os.getenv('SUCCESS_THRESHOLD', '0.7'))
        if threshold < 0 or threshold > 1:
            validations.append(('SUCCESS_THRESHOLD', False, f'Value {threshold} out of range (must be 0.0-1.0)'))
        else:
            validations.append(('SUCCESS_THRESHOLD', True, f'Valid threshold: {threshold} ({threshold*100:.0f}%)'))
    except (ValueError, TypeError):
        threshold_str = os.getenv('SUCCESS_THRESHOLD', 'default')
        validations.append(('SUCCESS_THRESHOLD', False, f'Invalid number: "{threshold_str}"'))
    
    # LOG_LEVEL
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper().strip()
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if log_level not in valid_levels:
        validations.append(('LOG_LEVEL', False, f'Invalid level "{log_level}", must be one of: {valid_levels}'))
    else:
        validations.append(('LOG_LEVEL', True, f'Valid level: {log_level}'))
    
    # MAX_WORKERS
    try:
        workers = int(os.getenv('MAX_WORKERS', '5'))
        if workers < 1 or workers > 20:
            validations.append(('MAX_WORKERS', False, f'Value {workers} out of range (recommended: 1-20)'))
        else:
            validations.append(('MAX_WORKERS', True, f'Valid worker count: {workers}'))
    except (ValueError, TypeError):
        workers_str = os.getenv('MAX_WORKERS', 'default')
        validations.append(('MAX_WORKERS', False, f'Invalid number: "{workers_str}"'))
    
    # TIMEOUT_SECONDS
    try:
        timeout = int(os.getenv('TIMEOUT_SECONDS', '30'))
        if timeout < 5 or timeout > 300:
            validations.append(('TIMEOUT_SECONDS', False, f'Value {timeout} out of range (recommended: 5-300)'))
        else:
            validations.append(('TIMEOUT_SECONDS', True, f'Valid timeout: {timeout}s'))
    except (ValueError, TypeError):
        timeout_str = os.getenv('TIMEOUT_SECONDS', 'default')
        validations.append(('TIMEOUT_SECONDS', False, f'Invalid number: "{timeout_str}"'))
    
    return validations


def test_supabase_connection() -> Tuple[bool, str]:
    """Test Supabase connection with current environment variables."""
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from core.storage import Storage
        
        storage = Storage()
        # Try a simple query to test connection
        result = storage.client.table('scraper_results').select('id').limit(1).execute()
        return True, f"Connection successful (found {len(result.data)} test records)"
    except ImportError as e:
        return False, f"Import error: {e}"
    except Exception as e:
        return False, f"Connection failed: {e}"


def print_validation_results(validations: List[Tuple[str, bool, str]], title: str):
    """Print formatted validation results."""
    print(f"\n{title}")
    print("=" * len(title))
    
    for var_name, is_valid, message in validations:
        status = "✅" if is_valid else "❌"
        print(f"{status} {var_name:<20} | {message}")


def main():
    """Main validation function."""
    print("🔧 Environment Variable Validation")
    print("=" * 40)
    
    # Validate required variables
    required_validations = validate_required_vars()
    print_validation_results(required_validations, "Required Variables")
    
    # Validate optional variables
    optional_validations = validate_optional_vars()
    print_validation_results(optional_validations, "Optional Variables")
    
    # Test connection if required vars are valid
    required_valid = all(valid for _, valid, _ in required_validations)
    
    if required_valid:
        print("\n🔌 Connection Test")
        print("=" * 17)
        
        connection_valid, connection_message = test_supabase_connection()
        status = "✅" if connection_valid else "❌"
        print(f"{status} Supabase Connection | {connection_message}")
    else:
        print("\n🔌 Connection Test")
        print("=" * 17)
        print("❌ Connection Test Skipped | Required variables not valid")
    
    # Summary
    print("\n📊 Summary")
    print("=" * 10)
    
    all_validations = required_validations + optional_validations
    total_vars = len(all_validations)
    valid_vars = sum(1 for _, valid, _ in all_validations if valid)
    
    print(f"Total variables checked: {total_vars}")
    print(f"Valid variables: {valid_vars}")
    print(f"Invalid variables: {total_vars - valid_vars}")
    
    if required_valid and connection_valid:
        print("✅ System ready for deployment")
        sys.exit(0)
    elif required_valid:
        print("⚠️  Required variables valid but connection failed")
        sys.exit(2)
    else:
        print("❌ Required variables invalid - deployment will fail")
        sys.exit(1)


if __name__ == "__main__":
    main()