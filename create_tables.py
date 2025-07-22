#!/usr/bin/env python3
"""Create Supabase database tables."""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

def create_tables():
    """Create the required database tables."""
    
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_KEY in .env file")
        return False
    
    print(f"🔗 Connecting to Supabase...")
    
    try:
        supabase: Client = create_client(url, key)
        print("✅ Connected to Supabase!")
        
        # Note: The Python client can't execute DDL statements directly
        # We need to use the Supabase SQL Editor for table creation
        
        print("\n⚠️  Cannot create tables using Python client.")
        print("Please follow these steps:")
        print("\n1. Go to your Supabase project dashboard")
        print("2. Navigate to SQL Editor")
        print("3. Create a new query")
        print("4. Paste and run this SQL:\n")
        
        sql = """
-- Create applicant_counts table
CREATE TABLE applicant_counts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    scraper_id TEXT NOT NULL,
    name TEXT NOT NULL,
    count INTEGER,
    status TEXT NOT NULL CHECK (status IN ('success', 'error')),
    error TEXT,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    synced_to_sheets BOOLEAN DEFAULT FALSE
);

-- Create scrapers_config table
CREATE TABLE scrapers_config (
    scraper_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_applicant_counts_date ON applicant_counts(date);
CREATE INDEX idx_applicant_counts_scraper ON applicant_counts(scraper_id);
CREATE INDEX idx_applicant_counts_sync ON applicant_counts(synced_to_sheets);
"""
        
        print(sql)
        print("\n5. Then run this SQL to add initial scraper configurations:\n")
        
        initial_data_sql = """
-- HSE scrapers
INSERT INTO scrapers_config (scraper_id, name) VALUES
('hse_online_big_data_analytics', 'ВШЭ - ОНЛАЙН Аналитика больших данных'),
('hse_online_data_analytics', 'ВШЭ - ОНЛАЙН Аналитика данных и прикладная статистика'),
('hse_online_ai', 'ВШЭ - ОНЛАЙН Искусственный интеллект'),
('hse_online_legaltech', 'ВШЭ - ОНЛАЙН ЛигалТех'),
('hse_online_data_science_master', 'ВШЭ - ОНЛАЙН Магистр по наукам о данным'),
('hse_online_game_engineering', 'ВШЭ - ОНЛАЙН Цифровая инженерия для компьютерных игр'),
('hse_online_urban_analytics', 'ВШЭ - ОНЛАЙН Цифровая урбанистика и аналитика города'),
('hse_online_data_engineering', 'ВШЭ - ОНЛАЙН Инженерия данных'),
('hse_online_cybersecurity', 'ВШЭ - ОНЛАЙН Кибербезопасность'),
('hse_online_innovation_business', 'ВШЭ - ОНЛАЙН Управление инновационным бизнесом'),
('hse_online_social_psychology', 'ВШЭ - ОНЛАЙН Прикладная социальная психология'),
('hse_online_economic_analysis', 'ВШЭ - ОНЛАЙН Экономический анализ'),
('hse_online_marketing_management', 'ВШЭ - ОНЛАЙН Маркетинг - менеджмент'),
('hse_online_creative_industries', 'ВШЭ - ОНЛАЙН Управление в креативных индустриях'),
('hse_online_digital_product', 'ВШЭ - ОНЛАЙН Управление цифровым продуктом'),
('hse_online_business_analytics', 'ВШЭ - ОНЛАЙН Магистр аналитики бизнеса');

-- MIPT scrapers
INSERT INTO scrapers_config (scraper_id, name) VALUES
('mipt_data_science', 'МФТИ - Науки о данных'),
('mipt_modern_combinatorics', 'МФТИ - Современная комбинаторика'),
('mipt_combinatorics_digital_economy', 'МФТИ - Комбинаторика и цифровая экономика'),
('mipt_contemporary_combinatorics', 'МФТИ - Contemporary combinatorics'),
('mipt_modern_ai', 'МФТИ - Modern Artificial Intelligence'),
('mipt_it_product_development', 'МФТИ - Разработка IT-продукта'),
('mipt_it_product_management', 'МФТИ - Управление IT-продуктами');

-- MEPhI scrapers
INSERT INTO scrapers_config (scraper_id, name) VALUES
('mephi_machine_learning', 'МИФИ - Машинное обучение'),
('mephi_data_science', 'МИФИ - Науки о данных'),
('mephi_cybersecurity', 'МИФИ - Кибербезопасность'),
('mephi_info_security', 'МИФИ - Безопасность информационных систем'),
('mephi_software_development', 'МИФИ - Разработка программного обеспечения'),
('mephi_web_development', 'МИФИ - Разработка веб приложений');
"""
        
        print(initial_data_sql)
        print("\n6. After running both SQL statements, run this script again to test!")
        
        return False  # Tables not created yet
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    create_tables()