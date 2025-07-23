#!/usr/bin/env python3
"""Debug the Google Sheets sync button functionality."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_api_endpoint():
    """Test the API endpoint directly."""
    
    print("🔧 DEBUGGING GOOGLE SHEETS SYNC BUTTON")
    print("=" * 50)
    
    try:
        import requests
        from datetime import date
        
        # Test the API endpoint directly
        print("1️⃣ Testing API endpoint directly...")
        
        url = "http://localhost:8080/api/sync-to-sheets"
        data = {"date": date.today().isoformat()}
        
        print(f"   URL: {url}")
        print(f"   Data: {data}")
        
        response = requests.post(url, json=data)
        
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ API endpoint is working")
        else:
            print("❌ API endpoint failed")
            
    except requests.exceptions.ConnectionError:
        print("❌ Dashboard not running on localhost:8080")
        print("   Start dashboard first: python dashboard.py")
        
    except ImportError:
        print("❌ requests module not available")
        print("   Testing without HTTP request...")
        
        # Test the function directly
        print("\n2️⃣ Testing sync function directly...")
        
        try:
            from core.dynamic_sheets import update_dynamic_sheets
            
            result = update_dynamic_sheets()
            
            if result:
                print("✅ Direct sync function works")
            else:
                print("⚠️ Direct sync function returned False")
                
        except Exception as e:
            print(f"❌ Direct sync function failed: {e}")
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def check_browser_console():
    """Provide instructions for checking browser console."""
    
    print("\n🌐 BROWSER DEBUGGING STEPS:")
    print("=" * 30)
    print("1. Open dashboard in browser")
    print("2. Open Developer Tools (F12)")
    print("3. Go to Console tab")
    print("4. Click 'Sync to Sheets' button")
    print("5. Look for error messages in console")
    print()
    print("Common errors:")
    print("- Network error: Dashboard not running")
    print("- 500 error: Server-side issue")
    print("- CORS error: Cross-origin issue")
    print("- JavaScript error: Function not defined")

if __name__ == "__main__":
    test_api_endpoint()
    check_browser_console()