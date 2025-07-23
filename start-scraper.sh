#!/bin/bash
set -e

echo "🚀 Starting Edu Parser Scraper Job..."
echo "Time: $(date)"

# Run the main scraper script
python main.py

echo "✅ Scraper job completed at $(date)"