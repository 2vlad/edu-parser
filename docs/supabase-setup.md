# Supabase Setup Guide

This guide will help you set up Supabase for the edu-parser project.

## Prerequisites

- Supabase account (free tier is sufficient)
- Access to Supabase dashboard

## Steps

### 1. Create a New Supabase Project

1. Go to [https://app.supabase.com](https://app.supabase.com)
2. Click "New project"
3. Enter project details:
   - Name: `edu-parser` (or your preferred name)
   - Database Password: Generate a strong password
   - Region: Choose the closest to your location
4. Click "Create new project" and wait for initialization

### 2. Get Your API Credentials

1. Once the project is created, go to Settings → API
2. Copy the following values:
   - `Project URL` → This is your `SUPABASE_URL`
   - `anon public` key → This is your `SUPABASE_KEY`

### 3. Create Database Tables

1. Go to SQL Editor in Supabase dashboard
2. Create a new query and paste the following SQL:

```sql
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
```

3. Click "Run" to execute the SQL

### 4. Insert Initial Scraper Configuration

Run this SQL to add the initial scraper configurations:

```sql
-- HSE scrapers
INSERT INTO scrapers_config (scraper_id, name) VALUES
('hse_online_big_data_analytics', 'ВШЭ - ОНЛАЙН Аналитика больших данных'),
('hse_online_data_analytics', 'ВШЭ - ОНЛАЙН Аналитика данных и прикладная статистика'),
('hse_online_ai', 'ВШЭ - ОНЛАЙН Искусственный интеллект'),
('hse_online_legaltech', 'ВШЭ - ОНЛАЙН ЛигалТех'),
('hse_online_data_science_master', 'ВШЭ - ОНЛАЙН Магистр по наукам о данных'),
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
```

### 5. Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your Supabase credentials:
   ```
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_KEY=your-anon-public-key-here
   ```

### 6. Test Connection

Create a test script `test_supabase.py`:

```python
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
```

Run the test:
```bash
python test_supabase.py
```

## Common Issues

### Authentication Error
- Ensure you're using the `anon public` key, not the `service_role` key
- Check that the URL includes `https://` and ends with `.supabase.co`

### Table Not Found
- Make sure you ran the CREATE TABLE SQL statements
- Check you're in the correct Supabase project

### Connection Timeout
- Check your internet connection
- Verify the Supabase project is in an active state

## Next Steps

Once setup is complete:
1. Mark task 2 as complete in Task Master
2. Proceed with implementing the core storage module (task 3)