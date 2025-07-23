# Railway Cron Setup Instructions

## Setting up the Daily Scraper Run at 23:59

Railway supports cron jobs through environment variables. To enable the daily scraper run at 23:59:

### 1. Add Environment Variable in Railway Dashboard

In your Railway project settings, add:

```
RAILWAY_CRON_SCHEDULE=59 23 * * *
```

This runs the scraper every day at 23:59 (11:59 PM) UTC.

For Moscow time (UTC+3), use:
```
RAILWAY_CRON_SCHEDULE=59 20 * * *
```

This runs at 20:59 UTC = 23:59 MSK.

### 2. Deploy Configuration

The project already includes:
- `cron.py` - The cron job runner script (uses subprocess to avoid PORT conflicts)
- `start-scraper.sh` - Shell script to run the scraper (for manual use)
- `railway.json` - Updated with cronCommand configuration

### 3. Manual Run Button

The dashboard now includes a "Run All Scrapers Now" button that allows you to:
- Manually trigger all scrapers at any time
- Overwrite existing data for today
- Test the system without waiting for cron

### 4. Verify Setup

After setting the environment variable and deploying:

1. Check Railway logs for "Starting Edu Parser Cron Job"
2. Monitor the dashboard at https://web-production-cdc5.up.railway.app/
3. Data should appear after 23:59 each day
4. Use the manual run button for immediate testing

### Cron Schedule Format

```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 7)
│ │ │ │ │
│ │ │ │ │
59 23 * * *
```

### Alternative Schedules

- `59 11,23 * * *` - Run at 11:59 AM and 11:59 PM
- `0 */6 * * *` - Run every 6 hours
- `59 23 * * 1-5` - Run at 11:59 PM on weekdays only

### Testing

To manually trigger the scraper:
```bash
python main.py
```

Or using the cron script:
```bash
python cron.py
```