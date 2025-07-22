#!/usr/bin/env python3
"""Test script for the dashboard functionality."""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all dashboard imports work."""
    print("Testing dashboard imports...")
    
    try:
        from dashboard import app, check_access
        print("✓ Dashboard imports successful")
        
        # Test Flask configuration
        print(f"✓ Flask app created: {app.name}")
        print(f"✓ Secret key configured: {'***' if app.config['SECRET_KEY'] else 'NOT SET'}")
        
        # Test routes
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append(f"{rule.endpoint}: {rule.rule}")
        
        print(f"✓ Routes registered: {len(routes)}")
        for route in sorted(routes):
            print(f"  - {route}")
            
        return True
        
    except Exception as e:
        print(f"✗ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_templates():
    """Test that templates exist."""
    print("\nTesting templates...")
    
    templates = [
        'templates/dashboard.html',
        'templates/error.html',
        'templates/404.html'
    ]
    
    all_exist = True
    for template in templates:
        if os.path.exists(template):
            print(f"✓ {template} exists")
        else:
            print(f"✗ {template} missing")
            all_exist = False
    
    return all_exist


def test_health_endpoint():
    """Test the health check endpoint."""
    print("\nTesting health endpoint...")
    
    try:
        from dashboard import app
        
        # Create test client
        with app.test_client() as client:
            response = client.get('/health')
            print(f"✓ Health endpoint status: {response.status_code}")
            
            if response.json:
                print(f"✓ Health response: {response.json}")
            
            return response.status_code in [200, 503]
            
    except Exception as e:
        print(f"✗ Health endpoint error: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("DASHBOARD TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_imports(),
        test_templates(),
        test_health_endpoint()
    ]
    
    passed = sum(tests)
    total = len(tests)
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("✅ All tests passed! Dashboard is ready.")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)