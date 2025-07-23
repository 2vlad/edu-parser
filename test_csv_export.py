#!/usr/bin/env python3
"""Test CSV export functionality."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
from datetime import datetime

def test_csv_export():
    """Test CSV export via API."""
    
    print("🧪 TESTING CSV EXPORT")
    print("=" * 50)
    
    base_url = "http://localhost:8080"
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Test CSV export for today
    print(f"Testing CSV export for date: {today}")
    
    try:
        response = requests.get(f"{base_url}/api/export-csv?date={today}")
        
        if response.status_code == 200:
            print("✅ CSV export successful!")
            print(f"Content-Type: {response.headers.get('Content-Type')}")
            print(f"Content-Disposition: {response.headers.get('Content-Disposition')}")
            print(f"Content length: {len(response.content)} bytes")
            
            # Show first few lines of CSV
            csv_content = response.text
            lines = csv_content.split('\n')[:10]  # First 10 lines
            print("\n📄 CSV Preview (first 10 lines):")
            for i, line in enumerate(lines, 1):
                if line.strip():
                    print(f"  {i}: {line}")
                    
        elif response.status_code == 404:
            print("⚠️ No data found for the specified date")
            print(f"Response: {response.text}")
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - make sure dashboard is running on localhost:8080")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("=" * 50)

if __name__ == "__main__":
    test_csv_export()