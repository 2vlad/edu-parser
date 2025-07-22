#!/usr/bin/env python3
"""Setup and test Supabase database connection."""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

def setup_database():
    """Setup and test Supabase database connection."""
    
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_KEY in .env file")
        print("Please check your .env file and ensure it contains:")
        print("SUPABASE_URL=https://your-project-id.supabase.co")
        print("SUPABASE_KEY=your-anon-public-key-here")
        return False
    
    print(f"🔗 Connecting to Supabase at: {url[:30]}...")
    
    try:
        supabase: Client = create_client(url, key)
        print("✅ Successfully connected to Supabase!")
        
        # Test basic connection
        print("\n📋 Testing database tables...")
        
        # Test scrapers_config table
        try:
            result = supabase.table('scrapers_config').select("scraper_id, name, enabled").limit(3).execute()
            print(f"✅ scrapers_config table found with {len(result.data)} entries")
            if result.data:
                print("   Sample entries:")
                for entry in result.data:
                    print(f"   - {entry['scraper_id']}: {entry['name']} (enabled: {entry['enabled']})")
        except Exception as e:
            print(f"❌ scrapers_config table error: {e}")
            return False
            
        # Test applicant_counts table
        try:
            result = supabase.table('applicant_counts').select("id, scraper_id, name, status").limit(3).execute()
            print(f"✅ applicant_counts table found with {len(result.data)} entries")
            if result.data:
                print("   Recent entries:")
                for entry in result.data:
                    print(f"   - {entry['scraper_id']}: {entry.get('count', 'N/A')} ({entry['status']})")
        except Exception as e:
            print(f"❌ applicant_counts table error: {e}")
            return False
            
        # Test insert capability
        print("\n🧪 Testing insert operations...")
        try:
            test_data = {
                'scraper_id': 'test_scraper',
                'name': 'Test University - Test Program',
                'count': 42,
                'status': 'success',
                'synced_to_sheets': False
            }
            
            # Insert test data
            result = supabase.table('applicant_counts').insert(test_data).execute()
            print("✅ Successfully inserted test data")
            
            # Clean up test data
            supabase.table('applicant_counts').delete().eq('scraper_id', 'test_scraper').execute()
            print("✅ Successfully cleaned up test data")
            
        except Exception as e:
            print(f"❌ Insert test failed: {e}")
            return False
            
        print("\n🎉 All database tests passed!")
        print("Your Supabase setup is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {e}")
        print("\nTroubleshooting:")
        print("1. Check your SUPABASE_URL and SUPABASE_KEY in .env")
        print("2. Ensure you're using the 'anon public' key, not 'service_role'")
        print("3. Verify the Supabase project is active")
        print("4. Make sure you created the database tables with the provided SQL")
        return False

if __name__ == "__main__":
    success = setup_database()
    if not success:
        exit(1)