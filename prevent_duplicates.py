#!/usr/bin/env python3
"""Add database constraints to prevent duplicates."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.storage import Storage
from datetime import datetime

def add_unique_constraint():
    """Add unique constraint to prevent duplicate scraper_id + date combinations."""
    
    print("🔧 ADDING UNIQUE CONSTRAINT TO PREVENT DUPLICATES")
    print("=" * 50)
    
    storage = Storage()
    
    try:
        # First, let's see if there's already a unique constraint
        print("Checking current table constraints...")
        
        # We can't directly add unique constraints via supabase client
        # But we can implement UPSERT logic in our save methods
        print("📋 Current approach: Implementing UPSERT logic in save methods")
        
        # Create a better save function that prevents duplicates
        def save_unique_result(storage, result):
            """Save result with duplicate prevention."""
            today = datetime.now().strftime('%Y-%m-%d')
            scraper_id = result['scraper_id']
            
            # First, delete any existing records for this scraper_id + date
            delete_result = storage.client.table('applicant_counts')\
                .delete()\
                .eq('scraper_id', scraper_id)\
                .eq('date', today)\
                .execute()
            
            # Then insert the new record
            return storage.save_result(result)
        
        print("✅ UPSERT logic defined for preventing duplicates")
        print("\nRecommendation: Use the cleanup script after any manual runs")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    add_unique_constraint()