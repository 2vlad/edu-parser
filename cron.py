#!/usr/bin/env python3
"""
Cron job runner for Railway.
This script is executed on a schedule defined by RAILWAY_CRON_SCHEDULE.
"""

import os
import sys
import subprocess
from datetime import datetime

def main():
    """Run the scraper job."""
    print(f"🚀 Starting Edu Parser Cron Job at {datetime.now()}")
    
    try:
        # Set environment variables to prevent dashboard startup
        env = os.environ.copy()
        env['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))
        
        # Run main.py as subprocess to avoid import conflicts
        result = subprocess.run([
            sys.executable, 'main.py'
        ], 
        cwd=os.path.dirname(os.path.abspath(__file__)),
        env=env,
        capture_output=True,
        text=True,
        timeout=600  # 10 minute timeout
        )
        
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print(f"✅ Cron job completed successfully at {datetime.now()}")
        else:
            print(f"❌ Cron job failed with return code {result.returncode}")
            sys.exit(1)
        
    except subprocess.TimeoutExpired:
        print(f"❌ Cron job timed out after 10 minutes")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Cron job failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()