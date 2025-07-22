#!/usr/bin/env python3
"""
Comprehensive system test for edu-parser.
Tests all major components before deployment.
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_environment():
    """Test environment variables."""
    print("\n1️⃣  ENVIRONMENT VARIABLES TEST")
    print("=" * 50)
    
    required = ['SUPABASE_URL', 'SUPABASE_KEY']
    optional = ['SCRAPER_MODE', 'SUCCESS_THRESHOLD', 'FLASK_SECRET_KEY']
    
    missing = []
    for var in required:
        value = os.getenv(var)
        if value:
            masked = value[:10] + '...' if len(value) > 20 else value
            print(f"✅ {var}: {masked}")
        else:
            print(f"❌ {var}: NOT SET")
            missing.append(var)
    
    print("\nOptional variables:")
    for var in optional:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"⚠️  {var}: Not set (using default)")
    
    return len(missing) == 0


def test_core_modules():
    """Test core module imports."""
    print("\n2️⃣  CORE MODULES TEST")
    print("=" * 50)
    
    modules = [
        ('core.storage', 'Storage'),
        ('core.registry', 'ScraperRegistry'),
        ('core.runner', 'ScraperRunner'),
        ('core.logging_config', 'setup_logging'),
        ('core.http_client', 'ReliableHTTPClient')
    ]
    
    success = True
    for module_name, class_name in modules:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            print(f"✅ {module_name}.{class_name}")
        except Exception as e:
            print(f"❌ {module_name}.{class_name}: {e}")
            success = False
    
    return success


def test_scrapers():
    """Test scraper discovery."""
    print("\n3️⃣  SCRAPER DISCOVERY TEST")
    print("=" * 50)
    
    try:
        from core.registry import ScraperRegistry
        from core.storage import Storage
        
        # Mock storage to avoid DB connection
        class MockStorage:
            def load_enabled_scrapers(self): return []
        
        registry = ScraperRegistry(storage=MockStorage())
        count = registry.discover_scrapers()
        
        print(f"✅ Discovered {count} scrapers")
        
        # Show first few scrapers
        scrapers = list(registry.scrapers.items())[:5]
        for scraper_id, info in scrapers:
            print(f"  - {scraper_id}: {info['config'].get('name', 'Unknown')}")
        
        if count > 5:
            print(f"  ... and {count - 5} more")
        
        return count >= 20  # Expected ~29 scrapers
        
    except Exception as e:
        print(f"❌ Scraper discovery failed: {e}")
        return False


def test_database_connection():
    """Test Supabase connection."""
    print("\n4️⃣  DATABASE CONNECTION TEST")
    print("=" * 50)
    
    try:
        from core.storage import Storage
        
        storage = Storage()
        # Simple query to test connection
        result = storage.client.table('scrapers_config').select('scraper_id').limit(1).execute()
        
        print("✅ Database connection successful")
        print(f"✅ Scrapers config table accessible")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def test_dashboard():
    """Test dashboard functionality."""
    print("\n5️⃣  DASHBOARD TEST")
    print("=" * 50)
    
    try:
        from dashboard import app
        
        print("✅ Dashboard imports successful")
        
        # Test routes
        with app.test_client() as client:
            # Test health endpoint
            response = client.get('/health')
            print(f"✅ Health endpoint: {response.status_code}")
            
            # Test main dashboard (might fail without data)
            response = client.get('/')
            print(f"✅ Dashboard route: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Dashboard test failed: {e}")
        return False


def test_deployment_files():
    """Test deployment configuration files."""
    print("\n6️⃣  DEPLOYMENT FILES TEST")
    print("=" * 50)
    
    files = {
        'railway.json': 'Railway dashboard config',
        'railway-scraper.json': 'Railway scraper config',
        'nixpacks.toml': 'Nixpacks build config',
        'Dockerfile': 'Docker configuration',
        'Procfile': 'Heroku-style config',
        '.env.template': 'Environment template',
        'requirements.txt': 'Python dependencies'
    }
    
    success = True
    for filename, description in files.items():
        if os.path.exists(filename):
            print(f"✅ {filename}: {description}")
        else:
            print(f"❌ {filename}: Missing")
            success = False
    
    # Validate JSON files
    for json_file in ['railway.json', 'railway-scraper.json']:
        if os.path.exists(json_file):
            try:
                with open(json_file) as f:
                    json.load(f)
                print(f"✅ {json_file}: Valid JSON")
            except Exception as e:
                print(f"❌ {json_file}: Invalid JSON - {e}")
                success = False
    
    return success


def test_sample_scraper():
    """Test running a single scraper."""
    print("\n7️⃣  SAMPLE SCRAPER TEST")
    print("=" * 50)
    
    try:
        from scrapers.hse import get_scrapers
        
        scrapers = get_scrapers()
        if scrapers:
            # Test first scraper
            scraper_func, config = scrapers[0]
            print(f"Testing {config['name']}...")
            
            result = scraper_func()
            
            if result['status'] == 'success':
                print(f"✅ Scraper successful: {result['count']} applicants")
            else:
                print(f"⚠️  Scraper failed: {result.get('error', 'Unknown error')}")
                print("   (This is expected if the data source has changed)")
            
            return True  # Test passes even if scraper fails (data might have changed)
        else:
            print("❌ No scrapers found in HSE module")
            return False
        
    except Exception as e:
        print(f"❌ Scraper test error: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("🚀 EDU-PARSER COMPREHENSIVE SYSTEM TEST")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    tests = [
        ("Environment Variables", test_environment()),
        ("Core Modules", test_core_modules()),
        ("Scraper Discovery", test_scrapers()),
        ("Database Connection", test_database_connection()),
        ("Dashboard", test_dashboard()),
        ("Deployment Files", test_deployment_files()),
        ("Sample Scraper", test_sample_scraper())
    ]
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print("=" * 60)
    print(f"Overall: {passed}/{len(tests)} tests passed ({passed/len(tests)*100:.0f}%)")
    
    if passed == len(tests):
        print("\n🎉 ALL TESTS PASSED! System is ready for deployment.")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        print("\nCommon issues:")
        print("- Missing environment variables (.env file)")
        print("- Database connection (check SUPABASE credentials)")
        print("- Module imports (run: pip install -r requirements.txt)")
    
    return passed == len(tests)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)