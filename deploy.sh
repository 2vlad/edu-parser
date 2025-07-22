#!/bin/bash

# Railway CLI Deployment Script for Edu-Parser
# This script helps deploy the dashboard and scraper to Railway

set -e

echo "🚀 EDU-PARSER RAILWAY DEPLOYMENT SCRIPT"
echo "======================================"
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    echo "Run: brew install railway"
    exit 1
fi

# Check if logged in to Railway
echo "1️⃣ Checking Railway authentication..."
if ! railway whoami &> /dev/null; then
    echo "📝 Not logged in to Railway. Please login:"
    railway login
fi

echo "✅ Logged in as: $(railway whoami)"
echo ""

# Function to deploy a service
deploy_service() {
    local service_name=$1
    local config_file=$2
    local service_type=$3
    
    echo "🚂 Deploying $service_name..."
    echo "======================================"
    
    # Create new project or link existing
    echo "Creating/linking Railway project for $service_name..."
    
    # Deploy with specific config
    echo "Deploying with $config_file..."
    railway up -c $config_file --service "$service_name"
    
    echo "✅ $service_name deployed!"
    echo ""
}

# Main deployment menu
echo "2️⃣ What would you like to deploy?"
echo "======================================"
echo "1) Dashboard only (Web UI)"
echo "2) Scraper only (Cron job)"
echo "3) Both Dashboard and Scraper"
echo "4) Check deployment status"
echo ""

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo ""
        echo "📊 DEPLOYING DASHBOARD"
        echo ""
        # First, we need to create or link a project
        read -p "Is this a new Railway project? (y/n): " is_new
        
        if [[ $is_new == "y" ]]; then
            echo "Creating new Railway project..."
            railway init
        else
            echo "Linking to existing Railway project..."
            railway link
        fi
        
        # Deploy dashboard
        echo "Deploying dashboard with railway.json..."
        railway up -c railway.json
        
        echo ""
        echo "✅ Dashboard deployed!"
        echo ""
        echo "⚙️ Next steps:"
        echo "1. Go to Railway dashboard: https://railway.app/dashboard"
        echo "2. Select your project"
        echo "3. Go to 'Variables' tab"
        echo "4. Add these environment variables:"
        echo "   - SUPABASE_URL"
        echo "   - SUPABASE_KEY"
        echo "   - FLASK_SECRET_KEY (optional)"
        echo "   - DASHBOARD_ALLOWED_IPS (optional)"
        echo ""
        echo "5. Go to 'Settings' tab"
        echo "6. Generate domain under 'Domains'"
        echo ""
        
        # Show deployment URL
        echo "🌐 Getting deployment info..."
        railway status
        ;;
        
    2)
        echo ""
        echo "🤖 DEPLOYING SCRAPER"
        echo ""
        read -p "Is this a new Railway project? (y/n): " is_new
        
        if [[ $is_new == "y" ]]; then
            echo "Creating new Railway project..."
            railway init
        else
            echo "Linking to existing Railway project..."
            railway link
        fi
        
        # Deploy scraper
        echo "Deploying scraper with railway-scraper.json..."
        railway up -c railway-scraper.json
        
        echo ""
        echo "✅ Scraper deployed!"
        echo ""
        echo "⚙️ Next steps:"
        echo "1. Go to Railway dashboard"
        echo "2. Add environment variables:"
        echo "   - SUPABASE_URL"
        echo "   - SUPABASE_KEY"
        echo "   - SCRAPER_MODE (optional, default: enabled)"
        echo ""
        echo "Note: Scraper runs on schedule defined in railway-scraper.json"
        echo "Default schedule: 0 6,18 * * * (6 AM and 6 PM UTC daily)"
        ;;
        
    3)
        echo ""
        echo "🚀 DEPLOYING BOTH SERVICES"
        echo ""
        echo "Railway requires separate projects for each service."
        echo "You'll need to deploy them one at a time."
        echo ""
        echo "Deploy the dashboard first (option 1), then the scraper (option 2)."
        ;;
        
    4)
        echo ""
        echo "📊 CHECKING DEPLOYMENT STATUS"
        echo ""
        
        if railway status &> /dev/null; then
            railway status
            echo ""
            echo "📝 Recent logs:"
            railway logs --tail 20
        else
            echo "❌ No Railway project linked in this directory"
            echo "Run 'railway link' to connect to a project"
        fi
        ;;
        
    *)
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo ""
echo "🎯 DEPLOYMENT CHECKLIST"
echo "======================="
echo "[ ] Environment variables configured in Railway"
echo "[ ] Domain generated for dashboard (if needed)"
echo "[ ] Test health endpoint: https://your-domain.railway.app/health"
echo "[ ] Monitor logs: railway logs"
echo "[ ] Set up external monitoring (UptimeRobot, etc.)"
echo ""
echo "📚 Useful Railway CLI commands:"
echo "- railway logs          # View logs"
echo "- railway status        # Check deployment status"
echo "- railway run echo \$VARIABLE_NAME  # Check env vars"
echo "- railway restart       # Restart service"
echo "- railway down          # Stop deployment"
echo ""

# Save deployment info
echo "💾 Saving deployment info..."
cat > .railway-deployment-info.txt << EOF
Deployment Date: $(date)
Dashboard Config: railway.json
Scraper Config: railway-scraper.json

Environment Variables Needed:
- SUPABASE_URL
- SUPABASE_KEY
- FLASK_SECRET_KEY (generate with: openssl rand -hex 32)
- DASHBOARD_ALLOWED_IPS (optional)
- SCRAPER_MODE (optional: enabled/all)

Commands:
- View logs: railway logs
- Check status: railway status
- Restart: railway restart
EOF

echo "✅ Deployment info saved to .railway-deployment-info.txt"