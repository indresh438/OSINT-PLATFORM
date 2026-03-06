#!/bin/bash

# Reimport ALL databases with fixed logic (each gets its own MySQL database)
# This will import ALL data including emails like satush005@gmail.com

BASE_URL="http://localhost:8000/api/v1"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║      🔄 FRESH IMPORT - All Databases Separately 🔄           ║"
echo "║                                                              ║"
echo "║  Now imports each SQL dump into its OWN MySQL database!      ║"
echo "║  This will capture ALL data from all dumps.                  ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Stop any running imports
echo "🛑 Stopping current imports..."
sudo docker-compose stop celery_worker celery_beat
sleep 3

# Clear MongoDB
echo "🗑️  Clearing MongoDB..."
sudo docker-compose exec mongodb mongosh -u osint_admin -p osint_mongo_pass --authenticationDatabase admin osint_data --quiet --eval '
var result = db.entities.deleteMany({});
print("✅ Deleted " + result.deletedCount + " entities");
db.raw_records.deleteMany({});
db.import_logs.deleteMany({});
print("MongoDB cleared");
' 2>/dev/null

# Clear Elasticsearch
echo "🗑️  Clearing Elasticsearch..."
sudo docker-compose exec elasticsearch curl -s -X DELETE "http://localhost:9200/osint_entities" >/dev/null 2>&1 || true

# Clear old MySQL databases
echo "🗑️  Clearing old MySQL databases..."
sudo docker-compose exec mysql mysql -u root -posint_root_pass -e "
DROP DATABASE IF EXISTS osint_raw;
DROP DATABASE IF EXISTS osint_user;
DROP DATABASE IF EXISTS osint_u590166733_dashboard;
DROP DATABASE IF EXISTS osint_u590166733_fyadmission;
DROP DATABASE IF EXISTS osint_u590166733_jai_hind_college;
DROP DATABASE IF EXISTS osint_u590166733_login;
DROP DATABASE IF EXISTS osint_u590166733_thakur_college_of_science_and_commerce;
" 2>/dev/null || true

# Restart services
echo "🔄 Restarting services..."
sudo docker-compose start celery_worker celery_beat
sudo docker-compose restart backend
sleep 10

# Initialize Elasticsearch
echo "🔧 Initializing Elasticsearch..."
curl -s -X POST "$BASE_URL/import/initialize" >/dev/null 2>&1
sleep 5

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Starting FRESH imports (each dump gets its own database)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Array of dump files
declare -a dumps=(
    "user.sql"
    "u590166733_dashboard.sql"
    "u590166733_fyadmission.sql"
    "u590166733_jai_hind_college.sql"
    "u590166733_login.sql"
    "u590166733_thakur_college_of_science_and_commerce.sql"
)

counter=1
total=${#dumps[@]}

for dump_file in "${dumps[@]}"; do
    source_name="${dump_file%.sql}"
    
    echo "[$counter/$total] Importing: $dump_file"
    echo "   Database: osint_$source_name"
    
    response=$(curl -s -X POST "$BASE_URL/import/mysql" \
        -H "Content-Type: application/json" \
        -d "{\"source_name\": \"$source_name\", \"dump_file\": \"$dump_file\"}")
    
    if echo "$response" | grep -q "job_id"; then
        job_id=$(echo "$response" | jq -r '.job_id')
        echo "   ✅ Started: $job_id"
    else
        echo "   ❌ Failed: $response"
    fi
    
    # Delay between imports to avoid overloading
    sleep 5
    counter=$((counter + 1))
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ All import jobs triggered!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Each SQL dump is now in its OWN MySQL database:"
echo "   • osint_user"
echo "   • osint_u590166733_dashboard"
echo "   • osint_u590166733_fyadmission"  
echo "   • osint_u590166733_jai_hind_college"
echo "   • osint_u590166733_login (has satush005@gmail.com)"
echo "   • osint_u590166733_thakur_college_of_science_and_commerce (has satush005@gmail.com)"
echo ""
echo "⏳ Imports running in background (this will take 3-4 hours)..."
echo ""
echo "📊 Monitor progress:"
echo "   ./monitor_import.sh"
echo ""
echo "🔍 Watch logs:"
echo "   sudo docker-compose logs -f celery_worker"
echo ""
echo "✨ After completion, satush005@gmail.com will be searchable! ✨"
echo ""
