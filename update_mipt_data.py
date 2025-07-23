#!/usr/bin/env python3
"""Update MIPT data with fixed scraper logic."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from scrapers.mipt import MIPT_PROGRAMS, scrape_mipt_program
from core.storage import Storage

def update_mipt_data():
    """Update MIPT application data for today."""
    
    print("🔄 UPDATING MIPT DATA WITH FIXED SCRAPER")
    print("=" * 50)
    
    storage = Storage()
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Delete existing MIPT records for today
    print(f"🗑️ Deleting existing MIPT records for {today}...")
    
    try:
        # Get all MIPT scraper IDs
        mipt_scraper_ids = []
        for program_name, _ in MIPT_PROGRAMS:
            clean_name = (program_name
                         .replace('Науки о данных', 'data_science')
                         .replace('Современная комбинаторика', 'modern_combinatorics') 
                         .replace('Комбинаторика и цифровая экономика', 'combinatorics_digital_economy')
                         .replace('Contemporary combinatorics', 'contemporary_combinatorics')
                         .replace('Modern Artificial Intelligence', 'modern_ai')
                         .replace('Разработка IT-продукта', 'it_product_development')
                         .replace('Управление IT-продуктами', 'it_product_management')
                         .replace(' ', '_')
                         .replace('-', '_')
                         .lower())
            mipt_scraper_ids.append(f"mipt_{clean_name}")
        
        # Delete records for these scraper IDs for today
        for scraper_id in mipt_scraper_ids:
            result = storage.client.table('applicant_counts')\
                .delete()\
                .eq('scraper_id', scraper_id)\
                .eq('date', today)\
                .execute()
            print(f"  Deleted records for {scraper_id}")
        
        print(f"✅ Deleted old MIPT records for {today}")
        
    except Exception as e:
        print(f"⚠️ Error deleting old records: {e}")
    
    # Scrape and save new data
    print(f"\n📊 Scraping MIPT programs...")
    success_count = 0
    
    for i, (program_name, url) in enumerate(MIPT_PROGRAMS, 1):
        print(f"\n{i}/{len(MIPT_PROGRAMS)} - {program_name}")
        
        try:
            result = scrape_mipt_program(program_name, url)
            
            if result['status'] == 'success':
                count = result['count']
                scraper_id = result['scraper_id']
                name = result['name']
                
                # Save to database
                storage.save_result(result)
                
                print(f"  ✅ {count} заявлений - сохранено в БД")
                success_count += 1
                
            else:
                error = result.get('error', 'Unknown error')
                print(f"  ❌ Ошибка: {error}")
                
        except Exception as e:
            print(f"  ❌ Исключение: {e}")
    
    print(f"\n🎉 ОБНОВЛЕНИЕ ЗАВЕРШЕНО")
    print(f"Успешно: {success_count}/{len(MIPT_PROGRAMS)} программ")

if __name__ == "__main__":
    update_mipt_data()