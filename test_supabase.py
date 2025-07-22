import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("❌ Missing SUPABASE_URL or SUPABASE_KEY in .env file")
    exit(1)

try:
    supabase: Client = create_client(url, key)
    
    # Test query
    result = supabase.table('scrapers_config').select("*").limit(5).execute()
    
    print("✅ Successfully connected to Supabase!")
    print(f"Found {len(result.data)} scrapers in configuration")
    
except Exception as e:
    print(f"❌ Error connecting to Supabase: {e}")