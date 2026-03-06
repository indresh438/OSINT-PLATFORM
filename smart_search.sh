#!/bin/bash

# Search with deduplication to show only unique valuable records
# This helps find maximum valuable info in less time

EMAIL="$1"

if [ -z "$EMAIL" ]; then
    echo "Usage: $0 <email>"
    echo "Example: $0 satush005@gmail.com"
    exit 1
fi

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║       🎯 Smart Search with Deduplication 🎯                  ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "🔎 Searching for: $EMAIL"
echo ""

# Search WITHOUT deduplication (all records)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 WITHOUT Deduplication (all records):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

result_all=$(curl -s -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"$EMAIL\", \"limit\": 1000}")

total_all=$(echo "$result_all" | jq -r '.total')
echo "Total results: $total_all records"
echo ""

# Show breakdown by table
echo "📋 Results by table:"
echo "$result_all" | jq -r '.results | group_by(.source_table) | map({table: .[0].source_table, count: length}) | sort_by(-.count) | .[] | "   • \(.table): \(.count) records"'
echo ""

# Search WITH deduplication (unique records only)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ WITH Deduplication (unique records only):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

result_unique=$(curl -s -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"$EMAIL\", \"deduplicate\": true, \"limit\": 1000}")

total_unique=$(echo "$result_unique" | jq -r '.total')
echo "Total results: $total_unique unique records"
echo ""

# Show breakdown by table
echo "📋 Unique records by table:"
echo "$result_unique" | jq -r '.results | group_by(.source_table) | map({table: .[0].source_table, count: length}) | sort_by(-.count) | .[] | "   • \(.table): \(.count) unique records"'
echo ""

# Calculate reduction
if [ "$total_all" -gt 0 ]; then
    reduction=$((total_all - total_unique))
    percentage=$(awk "BEGIN {printf \"%.1f\", ($reduction / $total_all) * 100}")
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📉 Deduplication Stats:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "   Removed: $reduction duplicate records ($percentage%)"
    echo "   Kept: $total_unique unique records"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
fi
echo ""

# Show sample unique results with duplicate counts
echo "✨ Unique records (showing duplicate counts):"
echo "$result_unique" | jq -r '.results[0:5] | .[] | "
🔖 \(.entity_type | ascii_upcase): \(.value)
   Source: \(.source)
   Table: \(.source_table)
   Timestamp: \(.timestamp)
   " + (if .metadata.duplicate_count then "   📊 Duplicates: \(.metadata.duplicate_count) identical records found" else "" end)'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 RECOMMENDED: Combine filters for best results"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

result_best=$(curl -s -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"$EMAIL\", \"deduplicate\": true, \"exclude_tables\": [\"notifications\"], \"limit\": 1000}")

total_best=$(echo "$result_best" | jq -r '.total')
echo ""
echo "✅ With BOTH deduplication + excluding 'notifications':"
echo "   Results: $total_best clean, unique records"
echo ""
echo "📋 Clean results by table:"
echo "$result_best" | jq -r '.results | group_by(.source_table) | map({table: .[0].source_table, count: length}) | sort_by(-.count) | .[] | "   • \(.table): \(.count) unique records"'
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 API Usage Examples:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1️⃣  Deduplicate only:"
echo '   curl -X POST "http://localhost:8000/api/v1/search" \'
echo '     -H "Content-Type: application/json" \'
echo '     -d '"'"'{"query": "email@example.com", "deduplicate": true}'"'"
echo ""
echo "2️⃣  Deduplicate + exclude tables (BEST):"
echo '   curl -X POST "http://localhost:8000/api/v1/search" \'
echo '     -H "Content-Type: application/json" \'
echo '     -d '"'"'{"query": "email@example.com", "deduplicate": true, "exclude_tables": ["notifications", "logs"]}'"'"
echo ""
echo "3️⃣  Show only from specific tables:"
echo '   curl -X POST "http://localhost:8000/api/v1/search" \'
echo '     -H "Content-Type: application/json" \'
echo '     -d '"'"'{"query": "email@example.com", "deduplicate": true, "sources": ["u590166733_login"]}'"'"
echo ""
echo "🎯 BENEFIT: Focus on valuable data, ignore noise!"
echo ""
