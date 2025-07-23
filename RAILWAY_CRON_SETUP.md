# Railway Cron Setup Instructions

## Setting up the 6 AM Daily Scraper Run

Railway supports cron jobs through environment variables. To enable the 6 AM daily scraper run:

### 1. Add Environment Variable in Railway Dashboard

In your Railway project settings, add:

```
RAILWAY_CRON_SCHEDULE=0 6 * * *
```

This runs the scraper every day at 6:00 AM UTC+3 (Moscow time).

### 2. Deploy Configuration

The project already includes:
- `cron.py` - The cron job runner script
- `start-scraper.sh` - Shell script to run the scraper

### 3. Verify Setup

After setting the environment variable and deploying:

1. Check Railway logs for "Starting Edu Parser Cron Job"
2. Monitor the dashboard at https://web-production-cdc5.up.railway.app/
3. Data should appear after 6 AM each day

### Cron Schedule Format

```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 7)
│ │ │ │ │
│ │ │ │ │
0 6 * * *
```

### Alternative Schedules

- `0 6,18 * * *` - Run at 6 AM and 6 PM
- `0 */6 * * *` - Run every 6 hours
- `0 6 * * 1-5` - Run at 6 AM on weekdays only

### Testing

To manually trigger the scraper:
```bash
python main.py
```

Or using the cron script:
```bash
python cron.py
```