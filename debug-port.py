#!/usr/bin/env python3
"""
Simple debug script to identify PORT variable issues.
This script just prints environment details and exits.
"""

import os
import sys
from datetime import datetime

def main():
    print(f"🔍 DEBUG PORT ANALYSIS - {datetime.now()}")
    print(f"🔍 Script: {__file__}")
    print(f"🔍 Args: {sys.argv}")
    print(f"🔍 CWD: {os.getcwd()}")
    
    # Check PORT variable
    port_env = os.environ.get('PORT')
    print(f"🔍 PORT = '{port_env}' (type: {type(port_env)})")
    
    if port_env == '$PORT':
        print("🚨 FOUND LITERAL $PORT!")
    elif port_env and '$' in str(port_env):
        print(f"🚨 PORT contains $ symbol: '{port_env}'")
    elif port_env is None:
        print("🔍 PORT is None (normal for scripts)")
    else:
        print(f"🔍 PORT appears normal: '{port_env}'")
    
    # Check other variables
    vars_to_check = [
        'RAILWAY_CRON_SCHEDULE', 'FLASK_DEBUG', 'SCRAPER_MODE', 
        'PYTHONPATH', 'PATH', 'HOME', 'USER'
    ]
    
    for var in vars_to_check:
        value = os.environ.get(var)
        if value and '$' in value:
            print(f"🚨 {var} contains $: '{value}'")
        else:
            print(f"🔍 {var} = '{value}'")
    
    # Check if we're in Railway
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        print("🔍 Running in Railway environment")
    else:
        print("🔍 Not in Railway environment")
    
    print("🔍 Debug analysis complete - exiting normally")

if __name__ == "__main__":
    main()