#!/bin/bash

# Search with table/source exclusion filters
# This demonstrates how to filter out unwanted tables like "notifications"

EMAIL="$1"

if [ -z "$EMAIL" ]; then
    echo "Usage: $0 <email>"
    echo "Example: $0 satush005@gmail.com"
    exit 1
fi

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║       🔍 OSINT Search with Table Exclusion 🔍                ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "🔎 Searching for: $EMAIL"
echo ""

# Method 1: Exclude "notifications" table
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Search WITH notifications table (all results):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
result_with=$(curl -s -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"$EMAIL\", \"limit\": 1000}")

total_with=$(echo "$result_with" | jq -r '.total')
echo "Total results: $total_with"
echo ""

# Show breakdown by table
echo "📋 Results by table:"
echo "$result_with" | jq -r '.results | group_by(.source_table) | map({table: .[0].source_table, count: length}) | .[] | "   • \(.table): \(.count) results"'
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Search WITHOUT notifications table (filtered):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
result_without=$(curl -s -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"$EMAIL\", \"exclude_tables\": [\"notifications\"], \"limit\": 1000}")

total_without=$(echo "$result_without" | jq -r '.total')
echo "Total results: $total_without"
echo ""

# Show breakdown by table
echo "📋 Results by table:"
echo "$result_without" | jq -r '.results | group_by(.source_table) | map({table: .[0].source_table, count: length}) | .[] | "   • \(.table): \(.count) results"'
echo ""

# Calculate difference
diff=$((total_with - total_without))
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📉 Filtered out: $diff results from 'notifications' table"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Show sample of clean results
echo "✨ Sample clean results (excluding notifications):"
echo "$result_without" | jq -r '.results[0:3] | .[] | "
🔖 \(.entity_type | ascii_upcase): \(.value)
   Source: \(.source)
   Table: \(.source_table)
   Timestamp: \(.timestamp)
"'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 Usage Examples:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1️⃣  Exclude notifications table:"
echo '   curl -X POST "http://localhost:8000/api/v1/search" \'
echo '     -H "Content-Type: application/json" \'
echo '     -d '"'"'{"query": "email@example.com", "exclude_tables": ["notifications"]}'"'"
echo ""
echo "2️⃣  Exclude multiple tables:"
echo '   curl -X POST "http://localhost:8000/api/v1/search" \'
echo '     -H "Content-Type: application/json" \'
echo '     -d '"'"'{"query": "email@example.com", "exclude_tables": ["notifications", "logs", "audit"]}'"'"
echo ""
echo "3️⃣  Exclude entire source database:"
echo '   curl -X POST "http://localhost:8000/api/v1/search" \'
echo '     -H "Content-Type: application/json" \'
echo '     -d '"'"'{"query": "email@example.com", "exclude_sources": ["u590166733_thakur_college_of_science_and_commerce"]}'"'"
echo ""
