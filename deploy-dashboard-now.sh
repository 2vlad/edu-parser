#!/bin/bash

# Quick deployment script for dashboard
set -e

echo "🚀 DEPLOYING EDU-PARSER DASHBOARD TO RAILWAY"
echo "==========================================="
echo ""

# Check if we're in a git repo and have commits
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Not in a git repository. Railway needs git."
    echo "Run: git init && git add . && git commit -m 'Initial commit'"
    exit 1
fi

# Check for uncommitted changes
if [[ -n $(git status -s) ]]; then
    echo "⚠️  You have uncommitted changes. Railway deploys from git."
    echo "Do you want to commit them now? (y/n)"
    read -p "> " commit_now
    
    if [[ $commit_now == "y" ]]; then
        git add .
        git commit -m "Pre-deployment commit $(date +%Y-%m-%d_%H:%M:%S)"
        echo "✅ Changes committed"
    fi
fi

echo "📊 Deploying Dashboard..."
echo ""

# Check if already linked to a project
if railway status &> /dev/null; then
    echo "✅ Already linked to a Railway project"
    railway status
else
    echo "🆕 Creating new Railway project..."
    railway init --name "edu-parser-dashboard"
fi

echo ""
echo "🚂 Deploying with railway.json configuration..."
railway up -c railway.json

echo ""
echo "✅ DEPLOYMENT INITIATED!"
echo ""
echo "⏳ Railway is building and deploying your app..."
echo ""

# Get deployment URL
echo "🔍 Getting deployment information..."
sleep 3
railway status

echo ""
echo "📋 NEXT STEPS:"
echo "=============="
echo ""
echo "1. Go to your Railway dashboard:"
echo "   https://railway.app/dashboard"
echo ""
echo "2. Click on your 'edu-parser-dashboard' project"
echo ""
echo "3. Go to 'Variables' tab and add:"
echo "   SUPABASE_URL = $(grep SUPABASE_URL .env | cut -d'=' -f2)"
echo "   SUPABASE_KEY = [your key from .env]"
echo "   FLASK_SECRET_KEY = $(openssl rand -hex 32)"
echo ""
echo "4. Go to 'Settings' > 'Environment' > 'Domains'"
echo "   Click 'Generate Domain' to get a public URL"
echo ""
echo "5. Your dashboard will be available at:"
echo "   https://[your-app].railway.app"
echo ""
echo "6. Test the health endpoint:"
echo "   https://[your-app].railway.app/health"
echo ""

# Open Railway dashboard
echo "🌐 Opening Railway dashboard in browser..."
railway open