#!/bin/bash

# Complete Database Import Script
# This will import ALL SQL dumps and process every single table

set -e

BASE_URL="http://localhost:8000/api/v1"
DUMP_DIR="./data/mysql_dumps"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║         🚀 COMPLETE DATABASE IMPORT - ALL DATA 🚀            ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Get list of all SQL files sorted by size (smallest first for faster initial results)
echo "📁 Found SQL dump files:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ls -lh "$DUMP_DIR"/*.sql | awk '{printf "   %-50s %8s\n", $9, $5}'
echo ""

# Count total files
TOTAL_FILES=$(ls -1 "$DUMP_DIR"/*.sql | wc -l)
echo "📊 Total databases to import: $TOTAL_FILES"
echo ""

# Function to trigger import
import_database() {
    local filepath=$1
    local filename=$(basename "$filepath")
    local db_name="${filename%.sql}"
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📥 Importing: $filename"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Trigger import via API
    response=$(curl -s -X POST "$BASE_URL/import/mysql" \
        -H "Content-Type: application/json" \
        -d "{\"source_name\": \"$db_name\", \"dump_file\": \"$filename\"}")
    
    # Check if import was triggered
    if echo "$response" | grep -q "job_id"; then
        job_id=$(echo "$response" | jq -r '.job_id')
        echo "✅ Import task started: $job_id"
        echo "   Source: $db_name"
        echo "   Status: Processing..."
        return 0
    else
        echo "❌ Failed to start import"
        echo "   Response: $response"
        return 1
    fi
}

# Function to get current stats
get_stats() {
    curl -s "$BASE_URL/stats" | jq '{
        elasticsearch: .elasticsearch.total_entities,
        mongodb: .mongodb.total_entities,
        neo4j: .neo4j.total_nodes,
        sources: .mongodb.by_source
    }'
}

# Get initial stats
echo "📊 Initial Statistics:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
get_stats
echo ""

read -p "🚀 Start importing all databases? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Import cancelled"
    exit 1
fi

echo ""
echo "🚀 Starting imports..."
echo ""

# Import each database
counter=1
for dump_file in "$DUMP_DIR"/*.sql; do
    echo "[$counter/$TOTAL_FILES] Processing $(basename "$dump_file")..."
    
    if import_database "$dump_file"; then
        echo "   ⏳ Waiting 5 seconds before next import..."
        sleep 5
    else
        echo "   ⚠️  Continuing to next database..."
    fi
    
    counter=$((counter + 1))
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ All import tasks triggered!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⏳ Imports are running in the background..."
echo ""
echo "📊 Monitor progress with:"
echo "   ./monitor_import.sh"
echo ""
echo "🔍 Check real-time logs:"
echo "   sudo docker-compose logs -f celery_worker"
echo ""
echo "📈 Current statistics in 30 seconds..."
sleep 30

echo ""
echo "📊 Current Statistics:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
get_stats
echo ""
echo "✨ Keep monitoring! Imports continue in background..."
echo ""
