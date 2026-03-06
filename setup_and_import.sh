#!/bin/bash

# Complete Setup and Import Script for Your Databases
# This script will start the platform and import all your databases in one go

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=================================================="
echo "🚀 OSINT Platform - Complete Setup & Import"
echo "=================================================="
echo ""
echo "This script will:"
echo "  1. Start the OSINT platform"
echo "  2. Initialize all databases"
echo "  3. Import your 6 database dumps (1.06 GB)"
echo ""
echo -e "${YELLOW}⚠️  This will take approximately 45-60 minutes${NC}"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

echo ""
echo "=================================================="
echo "📦 Step 1: Starting OSINT Platform..."
echo "=================================================="
./start.sh

echo ""
echo "⏳ Waiting for backend to be fully ready..."
sleep 10

# Wait for backend
MAX_WAIT=60
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend is ready!${NC}"
        break
    fi
    echo "Waiting... ($WAITED/$MAX_WAIT seconds)"
    sleep 5
    WAITED=$((WAITED + 5))
done

if [ $WAITED -eq $MAX_WAIT ]; then
    echo -e "${RED}❌ Backend failed to start${NC}"
    echo "Check logs: docker-compose logs backend"
    exit 1
fi

echo ""
echo "=================================================="
echo "📊 Step 2: Starting Database Imports..."
echo "=================================================="

API_BASE="http://localhost:8000/api/v1"

# Array to store job IDs
declare -a JOB_IDS
declare -a JOB_NAMES

# Import user.sql first (smallest, for quick testing)
echo ""
echo "1/6: Importing user.sql (10 KB)..."
RESULT=$(curl -s -X POST "${API_BASE}/import/mysql" \
    -H "Content-Type: application/json" \
    -d '{
        "source_name": "user_data",
        "dump_file": "/dumps/user.sql"
    }')
JOB_ID=$(echo "$RESULT" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
if [ -n "$JOB_ID" ]; then
    echo -e "${GREEN}✅ Started: ${JOB_ID}${NC}"
    JOB_IDS+=("$JOB_ID")
    JOB_NAMES+=("user_data")
else
    echo -e "${RED}❌ Failed${NC}"
fi
sleep 3

# Import jai_hind_college (48 MB)
echo ""
echo "2/6: Importing Jai Hind College (48 MB)..."
RESULT=$(curl -s -X POST "${API_BASE}/import/mysql" \
    -H "Content-Type: application/json" \
    -d '{
        "source_name": "jai_hind_college",
        "dump_file": "/dumps/u590166733_jai_hind_college.sql"
    }')
JOB_ID=$(echo "$RESULT" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
if [ -n "$JOB_ID" ]; then
    echo -e "${GREEN}✅ Started: ${JOB_ID}${NC}"
    JOB_IDS+=("$JOB_ID")
    JOB_NAMES+=("jai_hind_college")
else
    echo -e "${RED}❌ Failed${NC}"
fi
sleep 3

# Import fyadmission (72 MB)
echo ""
echo "3/6: Importing FY Admission (72 MB)..."
RESULT=$(curl -s -X POST "${API_BASE}/import/mysql" \
    -H "Content-Type: application/json" \
    -d '{
        "source_name": "fy_admission",
        "dump_file": "/dumps/u590166733_fyadmission.sql"
    }')
JOB_ID=$(echo "$RESULT" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
if [ -n "$JOB_ID" ]; then
    echo -e "${GREEN}✅ Started: ${JOB_ID}${NC}"
    JOB_IDS+=("$JOB_ID")
    JOB_NAMES+=("fy_admission")
else
    echo -e "${RED}❌ Failed${NC}"
fi
sleep 3

# Import dashboard (123 MB)
echo ""
echo "4/6: Importing Dashboard (123 MB)..."
RESULT=$(curl -s -X POST "${API_BASE}/import/mysql" \
    -H "Content-Type: application/json" \
    -d '{
        "source_name": "dashboard_db",
        "dump_file": "/dumps/u590166733_dashboard.sql"
    }')
JOB_ID=$(echo "$RESULT" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
if [ -n "$JOB_ID" ]; then
    echo -e "${GREEN}✅ Started: ${JOB_ID}${NC}"
    JOB_IDS+=("$JOB_ID")
    JOB_NAMES+=("dashboard_db")
else
    echo -e "${RED}❌ Failed${NC}"
fi
sleep 3

# Import thakur_college (354 MB)
echo ""
echo "5/6: Importing Thakur College (354 MB)..."
RESULT=$(curl -s -X POST "${API_BASE}/import/mysql" \
    -H "Content-Type: application/json" \
    -d '{
        "source_name": "thakur_college",
        "dump_file": "/dumps/u590166733_thakur_college_of_science_and_commerce.sql"
    }')
JOB_ID=$(echo "$RESULT" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
if [ -n "$JOB_ID" ]; then
    echo -e "${GREEN}✅ Started: ${JOB_ID}${NC}"
    JOB_IDS+=("$JOB_ID")
    JOB_NAMES+=("thakur_college")
else
    echo -e "${RED}❌ Failed${NC}"
fi
sleep 3

# Import login (467 MB - largest)
echo ""
echo "6/6: Importing Login System (467 MB, 72 tables)..."
echo -e "${YELLOW}This is the largest database and will take the longest...${NC}"
RESULT=$(curl -s -X POST "${API_BASE}/import/mysql" \
    -H "Content-Type: application/json" \
    -d '{
        "source_name": "login_system",
        "dump_file": "/dumps/u590166733_login.sql"
    }')
JOB_ID=$(echo "$RESULT" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
if [ -n "$JOB_ID" ]; then
    echo -e "${GREEN}✅ Started: ${JOB_ID}${NC}"
    JOB_IDS+=("$JOB_ID")
    JOB_NAMES+=("login_system")
else
    echo -e "${RED}❌ Failed${NC}"
fi

echo ""
echo "=================================================="
echo -e "${GREEN}🎉 All Import Jobs Started!${NC}"
echo "=================================================="
echo ""
echo "Job IDs:"
for i in "${!JOB_IDS[@]}"; do
    echo "  ${JOB_NAMES[$i]}: ${JOB_IDS[$i]}"
done

echo ""
echo "=================================================="
echo "⏳ Import Progress"
echo "=================================================="
echo ""
echo "Estimated completion times:"
echo "  • user_data:      ~1 minute"
echo "  • jai_hind:       ~5 minutes"
echo "  • fy_admission:   ~8 minutes"
echo "  • dashboard:      ~12 minutes"
echo "  • thakur_college: ~25 minutes"
echo "  • login_system:   ~30 minutes"
echo ""
echo "Total time: 45-60 minutes (running in parallel)"
echo ""

# Monitor progress
echo "Monitoring first few jobs (10 minutes)..."
echo ""

for ((i=0; i<20; i++)); do
    sleep 30
    echo "⏱️  Time elapsed: $((i * 30 / 60)) min $((i * 30 % 60)) sec"
    
    # Check first job status
    if [ ${#JOB_IDS[@]} -gt 0 ]; then
        STATUS=$(curl -s "${API_BASE}/import/status/${JOB_IDS[0]}" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        echo "  ${JOB_NAMES[0]}: $STATUS"
    fi
    
    # Check if user wants to continue monitoring
    if [ $i -eq 19 ]; then
        echo ""
        echo "Continue monitoring? (y/n) [Default: n]"
        read -t 5 -r continue_monitor || continue_monitor="n"
        if [ "$continue_monitor" != "y" ]; then
            break
        fi
    fi
done

echo ""
echo "=================================================="
echo "📊 How to Monitor Full Progress:"
echo "=================================================="
echo ""
echo "Option 1: Dashboard (Recommended)"
echo "  http://localhost:8501"
echo "  → Go to 'Import Data' → 'Monitor Jobs'"
echo ""
echo "Option 2: API"
echo "  curl http://localhost:8000/api/v1/import/jobs"
echo ""
echo "Option 3: Logs"
echo "  docker-compose logs -f celery_worker"
echo ""

echo "=================================================="
echo "🔍 Quick Search Test"
echo "=================================================="
echo ""
echo "While imports are running, you can already search:"
echo ""
echo "Dashboard:"
echo "  http://localhost:8501 → Search"
echo ""
echo "API:"
echo "  curl -X POST http://localhost:8000/api/v1/search \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"query\": \"college\", \"limit\": 10}'"
echo ""

echo "=================================================="
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "=================================================="
echo ""
echo "🎯 What's Next:"
echo ""
echo "1. Wait for imports to complete (monitor via dashboard)"
echo "2. Explore your data at http://localhost:8501"
echo "3. Search for emails, IPs, usernames, phone numbers"
echo "4. Visualize relationships between entities"
echo "5. Export findings and generate reports"
echo ""
echo "📖 Documentation:"
echo "  • YOUR_DATABASES.md - Your specific databases"
echo "  • README.md - Full platform documentation"
echo "  • QUICKSTART.md - Quick reference"
echo ""
echo "🔧 Useful Commands:"
echo "  ./status.sh     - Check system status"
echo "  make stats      - View statistics"
echo "  make logs       - View all logs"
echo ""
echo "=================================================="
