 #!/bin/bash

# Import All Databases Script - Fixed Version
# This script imports all 6 databases with proper configuration

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo "=================================================="
echo "📥 Importing All Databases into OSINT Platform"
echo "=================================================="
echo ""

# Check backend health
if ! curl -sf http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    echo -e "${RED}❌ Backend is not responding. Please start the platform first.${NC}"
    echo "Run: sudo docker-compose up -d"
    exit 1
fi

echo -e "${GREEN}✅ Backend is healthy!${NC}"
echo ""

# Database files and their friendly names
declare -A databases=(
    ["user.sql"]="User Database"
    ["u590166733_dashboard.sql"]="Dashboard System"
    ["u590166733_fyadmission.sql"]="FY Admission Records"
    ["u590166733_jai_hind_college.sql"]="Jai Hind College"
    ["u590166733_thakur_college_of_science_and_commerce.sql"]="Thakur College"
    ["u590166733_login.sql"]="Login System (72 tables)"
)

# Order of import (smallest to largest)
import_order=(
    "user.sql"
    "u590166733_jai_hind_college.sql"
    "u590166733_fyadmission.sql"
    "u590166733_dashboard.sql"
    "u590166733_thakur_college_of_science_and_commerce.sql"
    "u590166733_login.sql"
)

total=${#import_order[@]}
counter=1
successful=0
failed=0

echo "📊 Total databases to import: $total"
echo "⏱️  Estimated total time: 45-60 minutes"
echo ""
read -p "Press Enter to start importing..."
echo ""

for db_file in "${import_order[@]}"; do
    source_name=$(echo "$db_file" | sed 's/\.sql$//' | sed 's/u590166733_//' | sed 's/_/ /g')
    friendly_name="${databases[$db_file]}"
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${BLUE}📥 Importing ${counter}/${total}: ${friendly_name}${NC}"
    echo "   File: $db_file"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # Start import
    response=$(curl -s -X POST http://localhost:8000/api/v1/import/mysql \
        -H "Content-Type: application/json" \
        -d "{\"dump_file\": \"/dumps/${db_file}\", \"source_name\": \"${source_name}\"}")
    
    job_id=$(echo $response | python3 -c "import sys, json; print(json.load(sys.stdin).get('job_id', ''))" 2>/dev/null)
    
    if [ -z "$job_id" ]; then
        echo -e "${RED}❌ Failed to start import${NC}"
        echo "Response: $response"
        failed=$((failed + 1))
        counter=$((counter + 1))
        continue
    fi
    
    echo "✅ Job started: $job_id"
    echo "⏳ Processing..."
    echo ""
    
    # Monitor progress
    last_status=""
    dots=0
    while true; do
        status_response=$(curl -s "http://localhost:8000/api/v1/import/status/${job_id}")
        status=$(echo $status_response | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'UNKNOWN'))" 2>/dev/null)
        
        if [ "$status" = "SUCCESS" ]; then
            echo ""
            echo -e "${GREEN}✅ Import completed successfully!${NC}"
            
            # Extract statistics
            total_records=$(echo $status_response | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('result', {}).get('total_records', 0))" 2>/dev/null)
            tables=$(echo $status_response | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('result', {}).get('tables_processed', 0))" 2>/dev/null)
            
            if [ -n "$total_records" ]; then
                echo "   📊 Records processed: $total_records"
                echo "   📋 Tables processed: $tables"
            fi
            
            successful=$((successful + 1))
            break
        elif [ "$status" = "FAILURE" ]; then
            echo ""
            echo -e "${RED}❌ Import failed${NC}"
            error=$(echo $status_response | python3 -c "import sys, json; print(json.load(sys.stdin).get('error', 'Unknown error'))" 2>/dev/null)
            echo "   Error: $error"
            failed=$((failed + 1))
            break
        elif [ "$status" = "PROGRESS" ]; then
            progress=$(echo $status_response | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('info', {}).get('progress', 0))" 2>/dev/null)
            current_table=$(echo $status_response | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('info', {}).get('current_table', ''))" 2>/dev/null)
            
            if [ -n "$progress" ] && [ -n "$current_table" ]; then
                printf "\r   Progress: %.1f%% - Table: %-40s" "$progress" "$current_table"
            else
                printf "\r   Processing"
                for ((i=0; i<$dots; i++)); do printf "."; done
                dots=$(( (dots + 1) % 4 ))
            fi
        else
            # Still pending or unknown
            printf "\r   Waiting"
            for ((i=0; i<$dots; i++)); do printf "."; done
            dots=$(( (dots + 1) % 4 ))
        fi
        
        sleep 3
    done
    
    echo ""
    echo ""
    counter=$((counter + 1))
    
    # Brief pause between imports
    if [ $counter -le $total ]; then
        sleep 2
    fi
done

echo "=================================================="
echo -e "${GREEN}🎉 Import Process Complete!${NC}"
echo "=================================================="
echo ""
echo "📊 Summary:"
echo "   ✅ Successful: $successful"
echo "   ❌ Failed: $failed"
echo "   📝 Total: $total"
echo ""

# Get final statistics
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📈 Final Statistics:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s http://localhost:8000/api/v1/stats | python3 -m json.tool
echo ""
echo "=================================================="
echo ""
echo "🎯 Your OSINT platform is ready!"
echo ""
echo "Access points:"
echo "  🖥️  Dashboard:  http://localhost:8501"
echo "  🔌 API:        http://localhost:8000"
echo "  📚 API Docs:   http://localhost:8000/docs"
echo ""
echo "=================================================="
