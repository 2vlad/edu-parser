# Dashboard Deployment Guide

The Edu Parser Dashboard provides a web interface to monitor scraping results and system health.

## Features

- **Real-time monitoring** of scraping results
- **Historical data viewing** with date navigation
- **Statistics dashboard** showing success rates
- **Health check endpoint** for monitoring
- **IP-based access control** for security
- **Responsive design** for mobile and desktop

## Local Development

### Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export FLASK_DEBUG=true
export SUPABASE_URL=your-url
export SUPABASE_KEY=your-key
```

3. Run the dashboard:
```bash
python dashboard.py
# Or use the startup script
./start-dashboard.sh
```

4. Access at http://localhost:5000

### Development Features

- Auto-reload on code changes
- Detailed error messages
- Debug toolbar (when FLASK_DEBUG=true)

## Production Deployment

### Railway Deployment

#### Option 1: Separate Services (Recommended)

Deploy dashboard and scraper as separate Railway services:

1. **Dashboard Service**
   - Use `railway.json` (configured for dashboard)
   - Set PORT environment variable
   - Configure domain in Railway

2. **Scraper Service**
   - Use `railway-scraper.json` 
   - Configure cron schedule
   - No public domain needed

#### Option 2: Combined Service

Use Procfile to run both in one service:
- Web process runs dashboard
- Worker process runs scrapers

### Environment Variables

#### Required
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
```

#### Optional - Security
```
FLASK_SECRET_KEY=generate-a-secure-key     # For session security
DASHBOARD_ALLOWED_IPS=1.2.3.4,5.6.7.8     # Restrict access by IP
```

#### Optional - Configuration
```
PORT=5000                    # Dashboard port
FLASK_DEBUG=false           # Never true in production!
DASHBOARD_WORKERS=2         # Gunicorn workers (default: CPU*2+1)
```

### Security Considerations

1. **IP Restrictions**
   - Set `DASHBOARD_ALLOWED_IPS` to limit access
   - Separate multiple IPs with commas
   - Leave empty to allow all (not recommended)

2. **Secret Key**
   - Generate secure key: `python -c "import secrets; print(secrets.token_hex(32))"`
   - Never use default key in production

3. **HTTPS**
   - Always use HTTPS in production
   - Railway provides automatic SSL

### Deployment Steps

1. **Configure Railway**
```bash
# Dashboard service
railway link
railway up -c railway.json

# Scraper service (if separate)
railway link
railway up -c railway-scraper.json
```

2. **Set Environment Variables**
   - Go to Railway dashboard
   - Add all required variables
   - Configure security settings

3. **Custom Domain (Optional)**
   - Add custom domain in Railway
   - Configure DNS records
   - SSL automatically provisioned

## Monitoring

### Health Check

The `/health` endpoint provides system status:

```bash
curl https://your-dashboard.railway.app/health
```

Response:
```json
{
  "status": "healthy",
  "last_run": "2024-01-22",
  "database": "connected",
  "timestamp": "2024-01-22T10:30:00"
}
```

### Status Codes
- `200` - System healthy
- `503` - System unhealthy (no recent data or database issues)

### Monitoring Services

Integrate with monitoring services using the health endpoint:
- **UptimeRobot**: HTTP(s) monitor on `/health`
- **Pingdom**: HTTP check expecting 200 status
- **Datadog**: Custom check on health endpoint

## API Endpoints

### Dashboard Pages

- `GET /` - Main dashboard (current date)
- `GET /?date=2024-01-22` - View specific date

### API Endpoints

- `GET /health` - System health check
- `GET /api/stats` - 7-day statistics
- `GET /api/scrapers` - Scraper configuration

All API endpoints return JSON and require same access permissions as dashboard.

## Troubleshooting

### Common Issues

1. **403 Forbidden**
   - Check IP restrictions
   - Verify DASHBOARD_ALLOWED_IPS setting
   - Check X-Forwarded-For header handling

2. **Database Connection**
   - Verify SUPABASE_URL and SUPABASE_KEY
   - Check network connectivity
   - Review Supabase quotas

3. **No Data Showing**
   - Ensure scrapers have run recently
   - Check date parameter in URL
   - Verify database has data for selected date

### Logs

Check Railway logs:
```bash
railway logs
```

Or local logs:
```bash
./start-dashboard.sh 2>&1 | tee dashboard.log
```

## Performance Tuning

### Gunicorn Workers

Optimal workers = (2 × CPU cores) + 1

```bash
# Override default
export DASHBOARD_WORKERS=4
```

### Database Queries

Dashboard caches queries for 30 seconds to reduce load.

### Static Files

In production, consider:
- CDN for static assets
- nginx for static file serving
- Asset compression

## Development Tips

### Testing Locally with Production Data

```bash
# Use production database locally
export SUPABASE_URL=prod-url
export SUPABASE_KEY=prod-key
export FLASK_DEBUG=true
python dashboard.py
```

### Mock Data for Development

Create `test_dashboard.py`:
```python
from dashboard import app
app.config['TESTING'] = True
# Add mock data logic
```

## Dashboard Features

### Date Navigation
- Click date links to view historical data
- Auto-refresh every 30 seconds for current date
- Shows last 7 days of available data

### Statistics Display
- Total scrapers run
- Success count and rate
- Failed scraper count
- Grouped by university

### Error Details
- Hover over errors to see full message
- Check logs for detailed stack traces
- Failed scrapers show error reason

## Customization

### Adding New Views

1. Add route in `dashboard.py`
2. Create template in `templates/`
3. Update navigation if needed

### Modifying Styles

Edit CSS in `templates/dashboard.html` or create separate CSS file.

### Adding Authentication

For more robust auth, consider:
- Flask-Login for user authentication
- OAuth2 for SSO integration
- Basic Auth for simple protection

## Scaling Considerations

### High Traffic
- Increase Gunicorn workers
- Add caching layer (Redis)
- Use CDN for static assets

### Multiple Regions
- Deploy dashboard in multiple regions
- Use geo-routing
- Replicate database for read performance

### Large Datasets
- Implement pagination
- Add date range limits
- Optimize database queries