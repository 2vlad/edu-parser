# edu-parser

Automated system for collecting applicant data from university websites.

## Overview

This project automates the daily manual process of collecting applicant statistics from ~30 university websites. It scrapes data once per day, saves it to a cloud database (Supabase), and can sync with Google Sheets for analytics.

## Features

- ✅ Automated scraping of HTML tables and Excel files
- ✅ Support for 30+ university programs across HSE, MIPT, and MEPhI
- ✅ Daily scheduled runs via Railway cron jobs
- ✅ Cloud storage with Supabase
- ✅ Error isolation - one scraper failure doesn't affect others
- ✅ Google Sheets synchronization (optional)

## Project Structure

```
edu-parser/
├── scrapers/          # University-specific scrapers
│   ├── hse.py        # HSE scrapers
│   ├── mipt.py       # MIPT scrapers
│   └── mephi.py      # MEPhI scrapers
├── core/             # Core functionality
│   ├── storage.py    # Supabase operations
│   ├── runner.py     # Scraper execution engine
│   └── registry.py   # Scraper registration
├── sync/             # External integrations
│   └── sheets_sync.py # Google Sheets sync
├── main.py           # Main entry point for cron
└── sheets_sync_job.py # Separate cron for Sheets sync
```

## Setup

### 1. Prerequisites

- Python 3.8+
- Supabase account (free tier works)
- Railway account for deployment (optional)
- Google Cloud account for Sheets API (optional)

### 2. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd edu-parser

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Setup

Follow the [Supabase Setup Guide](docs/supabase-setup.md) to:
1. Create a Supabase project
2. Set up database tables
3. Configure environment variables

### 4. Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-public-key-here
```

### 5. Test Setup

```bash
# Test Supabase connection
python test_supabase.py

# Test package imports
python test_imports.py
```

## Development

### Running Locally

```bash
# Run all scrapers once
python main.py

# Run specific scraper (after implementing)
python -c "from scrapers.hse import scrape_hse_online_ai; print(scrape_hse_online_ai())"
```

### Adding New Scrapers

1. Add scraper function to appropriate file in `scrapers/`
2. Register in `core/registry.py`
3. Add configuration to Supabase `scrapers_config` table

### Testing

```bash
# Run individual scraper
python -m scrapers.hse

# Check scraper output
python main.py --dry-run
```

## Deployment

### Railway Setup

1. Connect GitHub repository to Railway
2. Add environment variables in Railway dashboard
3. Configure cron schedule in Railway

### Cron Schedule

- Main scraper: Daily at 10:00 AM Moscow time
- Sheets sync: Daily at 10:30 AM Moscow time

## Monitoring

- Check Railway logs for execution status
- Query Supabase for recent data
- Monitor error rates in `applicant_counts` table

## Contributing

1. Create feature branch
2. Add tests for new scrapers
3. Ensure error handling is robust
4. Submit pull request

## License

[Your License]