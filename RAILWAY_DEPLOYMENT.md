# Railway Deployment Guide

This guide covers deploying the edu-parser scraping system to Railway.app with cron scheduling.

## Prerequisites

- Railway account (railway.app)
- GitHub repository with this codebase
- Supabase project with database set up

## Step 1: Create Railway Project

1. Visit [railway.app](https://railway.app) and sign in
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your edu-parser repository
5. Railway will automatically detect the Python project

## Step 2: Configure Environment Variables

### Using Railway Dashboard

1. Go to your Railway project
2. Click on "Variables" tab
3. Add the following environment variables:

**Required Variables:**
```
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-key
```

**Optional Variables:**
```
SCRAPER_MODE=enabled              # Options: "enabled", "all"
SUCCESS_THRESHOLD=0.5             # Minimum success rate (0.0-1.0, default: 0.7)
LOG_LEVEL=INFO                    # Options: DEBUG, INFO, WARNING, ERROR
MAX_WORKERS=5                     # Concurrent scrapers (default: 5)
TIMEOUT_SECONDS=30                # HTTP timeout (default: 30)
```

### Environment Variable Validation

Before deploying, validate your environment variables:

```bash
# Copy template and fill in values
cp .env.template .env
# Edit .env with your values

# Validate configuration
python scripts/validate_env.py
```

The validation script will:
- ✅ Check all required variables are set
- ✅ Validate URL and key formats
- ✅ Test Supabase connection
- ✅ Verify optional variable ranges

## Step 3: Deploy Configuration

The following files configure Railway deployment:

- `railway.json` - Railway-specific configuration
- `nixpacks.toml` - Build configuration and dependencies  
- `Dockerfile` - Alternative container configuration
- `requirements.txt` - Python dependencies

Railway will use nixpacks by default. If needed, switch to Docker in Settings > Deploy.

## Step 4: Set Up Cron Scheduling

Railway doesn't have built-in cron. Options:

### Option A: GitHub Actions (Recommended)

Create `.github/workflows/scraper-cron.yml`:

```yaml
name: Run Scrapers
on:
  schedule:
    - cron: '0 6,18 * * *'  # Run at 6 AM and 6 PM UTC daily
  workflow_dispatch:  # Allow manual runs

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          
      - name: Run scrapers
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
          SCRAPER_MODE: enabled
        run: python main.py
```

Add secrets in GitHub Settings > Secrets:
- `SUPABASE_URL`
- `SUPABASE_KEY`

### Option B: External Cron Service

Use services like:
- **cron-job.org** - Free HTTP cron
- **EasyCron** - Reliable cron service
- **AWS EventBridge** - If using AWS

Create an HTTP trigger endpoint by modifying Railway deployment.

### Option C: Railway Cron Plugin

1. In Railway dashboard, go to your project
2. Click "Add Plugin"
3. Select "Cron"
4. Set schedule: `0 6,18 * * *` (6 AM and 6 PM daily)
5. Set command: `python main.py`

## Step 5: Monitor Deployment

### Logs
- View logs in Railway dashboard under "Deployments"
- Logs show scraping progress and results

### Health Monitoring
- Check deployment status in Railway dashboard
- Set up alerts for failed deployments
- Monitor Supabase database for new records

### Performance Metrics
- Track scraper success rates in logs
- Monitor database storage usage
- Check Railway resource usage

## Step 6: Rollback Procedures

### Automatic Rollback
Railway automatically rolls back failed deployments.

### Manual Rollback
1. Go to Railway dashboard
2. Navigate to "Deployments"
3. Find previous working deployment
4. Click "Redeploy"

### Emergency Stop
1. In Railway dashboard, click "Settings"
2. Click "Pause Deployment" to stop cron runs
3. Fix issues and resume when ready

## Production Considerations

### Resource Limits
- Railway free tier has limited CPU/memory
- Monitor usage and upgrade if needed
- Consider running fewer concurrent scrapers

### Error Handling
- Scrapers are isolated (one failure doesn't stop others)
- Success threshold prevents false positives
- Comprehensive logging for debugging

### Data Retention
- Configure Supabase retention policies
- Archive old scraping results
- Monitor database size

### Security
- Never commit API keys to repository
- Use Railway environment variables
- Regularly rotate Supabase keys

## Troubleshooting

### Build Failures
```bash
# Test locally first
pip install -r requirements.txt
python main.py
```

### Import Errors
- Check `nixpacks.toml` dependencies
- Verify `requirements.txt` is complete
- Test with `python -c "import module"`

### Runtime Errors
- Check environment variables are set
- Verify Supabase connection
- Check logs for specific error messages

### Cron Not Running
- Verify cron schedule syntax
- Check GitHub Actions secrets
- Ensure webhook URLs are correct

## Scaling Considerations

For high-volume scraping:

1. **Horizontal Scaling**: Deploy multiple Railway services
2. **Load Balancing**: Use different scrapers per service
3. **Queue System**: Add Redis/RQ for job queuing
4. **Database Sharding**: Partition data by university

## Cost Optimization

- Use `SCRAPER_MODE=enabled` to run only working scrapers
- Adjust cron frequency based on data change rates
- Monitor Railway resource usage
- Consider spot instances for non-critical runs