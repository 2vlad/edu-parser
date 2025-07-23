#!/usr/bin/env python3
"""Test Google Sheets API endpoint directly."""

import sys
import os
import subprocess
import json
from datetime import date

def test_sheets_api():
    """Test the sheets API using curl."""
    
    print("🧪 TESTING GOOGLE SHEETS API ENDPOINT")
    print("=" * 45)
    
    url = "http://localhost:8080/api/sync-to-sheets"
    data = {"date": date.today().isoformat()}
    
    print(f"Testing: {url}")
    print(f"Data: {data}")
    
    try:
        # Use curl to test the endpoint
        curl_command = [
            'curl',
            '-X', 'POST',
            '-H', 'Content-Type: application/json',
            '-d', json.dumps(data),
            url
        ]
        
        print(f"\nRunning: {' '.join(curl_command)}")
        
        result = subprocess.run(
            curl_command,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        print(f"\nStatus Code: {result.returncode}")
        print(f"Response: {result.stdout}")
        
        if result.stderr:
            print(f"Error: {result.stderr}")
        
        if result.returncode == 0:
            print("✅ API endpoint responded")
        else:
            print("❌ API endpoint failed")
            
    except subprocess.TimeoutExpired:
        print("❌ Request timed out")
    except FileNotFoundError:
        print("❌ curl not found")
        print("Alternative: Test manually in browser developer tools")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_dashboard_health():
    """Test if dashboard is responding."""
    
    print("\n🏥 TESTING DASHBOARD HEALTH")
    print("=" * 30)
    
    try:
        result = subprocess.run(
            ['curl', 'http://localhost:8080/health'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print("✅ Dashboard health check passed")
            print(f"Response: {result.stdout}")
        else:
            print("❌ Dashboard health check failed")
            print(f"Error: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Health check error: {e}")

if __name__ == "__main__":
    test_dashboard_health()
    test_sheets_api()