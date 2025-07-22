#!/usr/bin/env python3
"""Test script to verify all dependencies are properly installed."""

import sys

def test_imports():
    """Test importing all required packages."""
    
    packages = [
        ('httpx', 'HTTP client'),
        ('bs4', 'BeautifulSoup'),
        ('pandas', 'Data analysis'),
        ('openpyxl', 'Excel support'),
        ('lxml', 'XML parsing'),
        ('dotenv', 'Environment variables'),
        ('supabase', 'Supabase client'),
        ('googleapiclient.discovery', 'Google API'),
        ('google.auth', 'Google Auth'),
    ]
    
    failed = []
    
    for package, description in packages:
        try:
            __import__(package)
            print(f"✅ {package:<25} - {description}")
        except ImportError as e:
            print(f"❌ {package:<25} - {description} - Error: {e}")
            failed.append(package)
    
    print("\n" + "="*50)
    if failed:
        print(f"❌ {len(failed)} packages failed to import: {', '.join(failed)}")
        sys.exit(1)
    else:
        print("✅ All packages imported successfully!")
        
        # Test creating a simple BeautifulSoup object
        from bs4 import BeautifulSoup
        soup = BeautifulSoup('<html><body>Test</body></html>', 'html.parser')
        print(f"✅ BeautifulSoup parse test: {soup.body.text}")
        
        # Test pandas
        import pandas as pd
        df = pd.DataFrame({'test': [1, 2, 3]})
        print(f"✅ Pandas DataFrame test: {len(df)} rows")
        
        # Test httpx
        import httpx
        print(f"✅ httpx version: {httpx.__version__}")

if __name__ == "__main__":
    test_imports()