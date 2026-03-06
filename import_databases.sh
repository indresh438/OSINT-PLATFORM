#!/bin/bash

# Import Configuration for Your Database Dumps
# This script helps you import your existing databases into the OSINT platform

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

BACKEND_URL="http://localhost:8000"
API_BASE="${BACKEND_URL}/api/v1"

echo "=================================================="
echo "🗄️  Database Import Wizard"
echo "=================================================="
echo ""
echo "Found 6 database dumps ready to import:"
echo "  1. u590166733_dashboard.sql (123 MB)"
echo "  2. u590166733_fyadmission.sql (72 MB)"
echo "  3. u590166733_jai_hind_college.sql (48 MB)"
echo "  4. u590166733_login.sql (467 MB - 72 tables)"
echo "  5. u590166733_thakur_college_of_science_and_commerce.sql (354 MB)"
echo "  6. user.sql (10 KB)"
echo ""
echo "Total size: ~1.06 GB"
echo ""

# Check if backend is running
echo "🔍 Checking if OSINT platform is running..."
if ! curl -s "${API_BASE}/health" > /dev/null 2>&1; then
    echo -e "${RED}❌ Backend is not running!${NC}"
    echo ""
    echo "Please start the platform first:"
    echo "  cd /home/sansat/Desktop/local_osint"
    echo "  ./start.sh"
    echo ""
    exit 1
fi

echo -e "${GREEN}✅ Backend is running${NC}"
echo ""

# Import options
echo "Select import option:"
echo "  1) Import all databases (recommended)"
echo "  2) Import specific database"
echo "  3) Import login database only (largest, 467 MB)"
echo "  4) Import college databases only"
echo "  5) Show import configuration examples"
echo ""
read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        echo ""
        echo "🚀 Starting import of ALL databases..."
        echo ""
        
        # Import dashboard
        echo "📊 Importing dashboard database..."
        JOB1=$(curl -s -X POST "${API_BASE}/import/mysql" \
            -H "Content-Type: application/json" \
            -d '{
                "source_name": "dashboard_db",
                "dump_file": "/dumps/u590166733_dashboard.sql"
            }')
        JOB1_ID=$(echo "$JOB1" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
        echo -e "${GREEN}✅ Job started: ${JOB1_ID}${NC}"
        
        sleep 2
        
        # Import fyadmission
        echo ""
        echo "🎓 Importing FY admission database..."
        JOB2=$(curl -s -X POST "${API_BASE}/import/mysql" \
            -H "Content-Type: application/json" \
            -d '{
                "source_name": "fy_admission",
                "dump_file": "/dumps/u590166733_fyadmission.sql"
            }')
        JOB2_ID=$(echo "$JOB2" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
        echo -e "${GREEN}✅ Job started: ${JOB2_ID}${NC}"
        
        sleep 2
        
        # Import Jai Hind College
        echo ""
        echo "🏫 Importing Jai Hind College database..."
        JOB3=$(curl -s -X POST "${API_BASE}/import/mysql" \
            -H "Content-Type: application/json" \
            -d '{
                "source_name": "jai_hind_college",
                "dump_file": "/dumps/u590166733_jai_hind_college.sql"
            }')
        JOB3_ID=$(echo "$JOB3" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
        echo -e "${GREEN}✅ Job started: ${JOB3_ID}${NC}"
        
        sleep 2
        
        # Import login (largest)
        echo ""
        echo "🔐 Importing login database (this will take longer - 467 MB)..."
        JOB4=$(curl -s -X POST "${API_BASE}/import/mysql" \
            -H "Content-Type: application/json" \
            -d '{
                "source_name": "login_system",
                "dump_file": "/dumps/u590166733_login.sql"
            }')
        JOB4_ID=$(echo "$JOB4" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
        echo -e "${GREEN}✅ Job started: ${JOB4_ID}${NC}"
        
        sleep 2
        
        # Import Thakur College
        echo ""
        echo "🏫 Importing Thakur College database..."
        JOB5=$(curl -s -X POST "${API_BASE}/import/mysql" \
            -H "Content-Type: application/json" \
            -d '{
                "source_name": "thakur_college",
                "dump_file": "/dumps/u590166733_thakur_college_of_science_and_commerce.sql"
            }')
        JOB5_ID=$(echo "$JOB5" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
        echo -e "${GREEN}✅ Job started: ${JOB5_ID}${NC}"
        
        sleep 2
        
        # Import user
        echo ""
        echo "👤 Importing user database..."
        JOB6=$(curl -s -X POST "${API_BASE}/import/mysql" \
            -H "Content-Type: application/json" \
            -d '{
                "source_name": "user_data",
                "dump_file": "/dumps/user.sql"
            }')
        JOB6_ID=$(echo "$JOB6" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
        echo -e "${GREEN}✅ Job started: ${JOB6_ID}${NC}"
        
        echo ""
        echo "=================================================="
        echo -e "${GREEN}🎉 All import jobs started!${NC}"
        echo "=================================================="
        echo ""
        echo "Job IDs:"
        echo "  Dashboard:      ${JOB1_ID}"
        echo "  FY Admission:   ${JOB2_ID}"
        echo "  Jai Hind:       ${JOB3_ID}"
        echo "  Login System:   ${JOB4_ID}"
        echo "  Thakur College: ${JOB5_ID}"
        echo "  User Data:      ${JOB6_ID}"
        echo ""
        echo "⏳ Import will take approximately 30-60 minutes for all databases."
        echo ""
        echo "📊 Monitor progress:"
        echo "  - Dashboard: http://localhost:8501 → Import Data → Monitor Jobs"
        echo "  - Logs: docker-compose logs -f celery_worker"
        echo ""
        ;;
        
    2)
        echo ""
        echo "Select database to import:"
        echo "  1) Dashboard (123 MB)"
        echo "  2) FY Admission (72 MB)"
        echo "  3) Jai Hind College (48 MB)"
        echo "  4) Login System (467 MB)"
        echo "  5) Thakur College (354 MB)"
        echo "  6) User Data (10 KB)"
        echo ""
        read -p "Enter choice (1-6): " db_choice
        
        case $db_choice in
            1) 
                DUMP_FILE="/dumps/u590166733_dashboard.sql"
                SOURCE_NAME="dashboard_db"
                ;;
            2)
                DUMP_FILE="/dumps/u590166733_fyadmission.sql"
                SOURCE_NAME="fy_admission"
                ;;
            3)
                DUMP_FILE="/dumps/u590166733_jai_hind_college.sql"
                SOURCE_NAME="jai_hind_college"
                ;;
            4)
                DUMP_FILE="/dumps/u590166733_login.sql"
                SOURCE_NAME="login_system"
                ;;
            5)
                DUMP_FILE="/dumps/u590166733_thakur_college_of_science_and_commerce.sql"
                SOURCE_NAME="thakur_college"
                ;;
            6)
                DUMP_FILE="/dumps/user.sql"
                SOURCE_NAME="user_data"
                ;;
            *)
                echo "Invalid choice"
                exit 1
                ;;
        esac
        
        echo ""
        echo "🚀 Starting import of ${SOURCE_NAME}..."
        
        RESULT=$(curl -s -X POST "${API_BASE}/import/mysql" \
            -H "Content-Type: application/json" \
            -d "{
                \"source_name\": \"${SOURCE_NAME}\",
                \"dump_file\": \"${DUMP_FILE}\"
            }")
        
        JOB_ID=$(echo "$RESULT" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
        
        if [ -n "$JOB_ID" ]; then
            echo -e "${GREEN}✅ Import job started: ${JOB_ID}${NC}"
        else
            echo -e "${RED}❌ Failed to start import${NC}"
            echo "$RESULT"
            exit 1
        fi
        ;;
        
    3)
        echo ""
        echo "🔐 Importing login database (467 MB, 72 tables)..."
        echo "⏳ This will take approximately 15-30 minutes..."
        
        RESULT=$(curl -s -X POST "${API_BASE}/import/mysql" \
            -H "Content-Type: application/json" \
            -d '{
                "source_name": "login_system",
                "dump_file": "/dumps/u590166733_login.sql"
            }')
        
        JOB_ID=$(echo "$RESULT" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
        
        if [ -n "$JOB_ID" ]; then
            echo -e "${GREEN}✅ Import job started: ${JOB_ID}${NC}"
        else
            echo -e "${RED}❌ Failed to start import${NC}"
            exit 1
        fi
        ;;
        
    4)
        echo ""
        echo "🏫 Importing college databases..."
        
        # Jai Hind
        echo "Importing Jai Hind College..."
        JOB1=$(curl -s -X POST "${API_BASE}/import/mysql" \
            -H "Content-Type: application/json" \
            -d '{
                "source_name": "jai_hind_college",
                "dump_file": "/dumps/u590166733_jai_hind_college.sql"
            }')
        JOB1_ID=$(echo "$JOB1" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
        echo -e "${GREEN}✅ Jai Hind job: ${JOB1_ID}${NC}"
        
        sleep 2
        
        # Thakur
        echo "Importing Thakur College..."
        JOB2=$(curl -s -X POST "${API_BASE}/import/mysql" \
            -H "Content-Type: application/json" \
            -d '{
                "source_name": "thakur_college",
                "dump_file": "/dumps/u590166733_thakur_college_of_science_and_commerce.sql"
            }')
        JOB2_ID=$(echo "$JOB2" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
        echo -e "${GREEN}✅ Thakur College job: ${JOB2_ID}${NC}"
        
        echo ""
        echo -e "${GREEN}Both college databases importing...${NC}"
        ;;
        
    5)
        cat << 'EOF'

================================================
📋 Import Configuration Examples
================================================

Basic Import (Auto-detection):
-------------------------------
curl -X POST "http://localhost:8000/api/v1/import/mysql" \
  -H "Content-Type: application/json" \
  -d '{
    "source_name": "my_database",
    "dump_file": "/dumps/u590166733_login.sql"
  }'

With Custom Field Mapping:
---------------------------
curl -X POST "http://localhost:8000/api/v1/import/mysql" \
  -H "Content-Type: application/json" \
  -d '{
    "source_name": "login_system",
    "dump_file": "/dumps/u590166733_login.sql",
    "field_mapping": {
      "users": {
        "email": "email",
        "username": "username",
        "last_login_ip": "ip",
        "phone": "phone"
      },
      "students": {
        "student_email": "email",
        "mobile_no": "phone",
        "registration_ip": "ip"
      }
    }
  }'

Import Specific Tables Only:
-----------------------------
curl -X POST "http://localhost:8000/api/v1/import/mysql" \
  -H "Content-Type: application/json" \
  -d '{
    "source_name": "login_system",
    "dump_file": "/dumps/u590166733_login.sql",
    "tables": ["users", "students", "login_logs"]
  }'

Monitor Import Progress:
------------------------
# Get job status
curl "http://localhost:8000/api/v1/import/status/{job_id}"

# List all jobs
curl "http://localhost:8000/api/v1/import/jobs"

# Or use the dashboard:
http://localhost:8501 → Import Data → Monitor Jobs

EOF
        ;;
        
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "=================================================="
echo "📚 Next Steps:"
echo "=================================================="
echo ""
echo "1. Monitor import progress:"
echo "   - Dashboard: http://localhost:8501"
echo "   - API: curl ${API_BASE}/import/jobs"
echo ""
echo "2. View logs:"
echo "   docker-compose logs -f celery_worker"
echo ""
echo "3. Once complete, search your data:"
echo "   - Dashboard: http://localhost:8501 → Search"
echo "   - Find emails, IPs, usernames, phone numbers"
echo ""
echo "4. Explore relationships:"
echo "   - Dashboard → Relationships tab"
echo "   - See connections between entities"
echo ""
echo "=================================================="
