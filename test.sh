#!/bin/bash

# OSINT Platform - Quick Test Script
# Tests basic functionality of the platform

set -e

echo "=================================================="
echo "🧪 OSINT Platform - Quick Test"
echo "=================================================="
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

BACKEND_URL="http://localhost:8000"
API_BASE="${BACKEND_URL}/api/v1"

# Test 1: Health Check
echo "1️⃣  Testing health check..."
HEALTH=$(curl -s "${API_BASE}/health")
if echo "$HEALTH" | grep -q "healthy\|degraded"; then
    echo -e "${GREEN}✅ Health check passed${NC}"
else
    echo -e "${RED}❌ Health check failed${NC}"
    exit 1
fi

# Test 2: Initialize indices
echo ""
echo "2️⃣  Initializing database indices..."
INIT=$(curl -s -X POST "${API_BASE}/import/initialize")
if echo "$INIT" | grep -q "started"; then
    echo -e "${GREEN}✅ Index initialization started${NC}"
    sleep 5
else
    echo -e "${YELLOW}⚠️  Indices may already be initialized${NC}"
fi

# Test 3: Get statistics
echo ""
echo "3️⃣  Testing statistics endpoint..."
STATS=$(curl -s "${API_BASE}/stats")
if echo "$STATS" | grep -q "elasticsearch\|mongodb\|neo4j"; then
    echo -e "${GREEN}✅ Statistics endpoint working${NC}"
else
    echo -e "${RED}❌ Statistics endpoint failed${NC}"
fi

# Test 4: Quick search test
echo ""
echo "4️⃣  Testing search endpoint..."
SEARCH=$(curl -s -X POST "${API_BASE}/search" \
    -H "Content-Type: application/json" \
    -d '{"query": "test", "limit": 10}')
if echo "$SEARCH" | grep -q "total\|results"; then
    echo -e "${GREEN}✅ Search endpoint working${NC}"
else
    echo -e "${RED}❌ Search endpoint failed${NC}"
fi

# Test 5: Create sample data (optional)
echo ""
echo "5️⃣  Would you like to create sample test data? (y/n)"
read -r CREATE_SAMPLE

if [ "$CREATE_SAMPLE" = "y" ] || [ "$CREATE_SAMPLE" = "Y" ]; then
    echo "Creating sample data..."
    
    # Create a test SQL file
    cat > /tmp/osint_test_data.sql << 'EOF'
CREATE DATABASE IF NOT EXISTS osint_raw;
USE osint_raw;

DROP TABLE IF EXISTS test_users;
CREATE TABLE test_users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255),
    username VARCHAR(100),
    ip_address VARCHAR(45),
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO test_users (email, username, ip_address, phone) VALUES
('john.doe@example.com', 'johndoe', '192.168.1.100', '+1234567890'),
('jane.smith@example.com', 'janesmith', '192.168.1.101', '+1234567891'),
('bob.wilson@example.com', 'bobwilson', '192.168.1.102', '+1234567892'),
('alice.brown@example.com', 'alicebrown', '192.168.1.103', '+1234567893'),
('charlie.davis@example.com', 'charliedavis', '192.168.1.104', '+1234567894');
EOF
    
    # Import into MySQL
    docker cp /tmp/osint_test_data.sql osint_mysql:/tmp/
    docker exec osint_mysql mysql -uosint_user -posint_pass < /tmp/osint_test_data.sql
    
    echo -e "${GREEN}✅ Sample data created${NC}"
    
    # Start import job
    echo "Starting import job for test data..."
    IMPORT_JOB=$(curl -s -X POST "${API_BASE}/import/mysql" \
        -H "Content-Type: application/json" \
        -d '{
            "source_name": "test_data",
            "tables": ["test_users"],
            "field_mapping": {
                "test_users": {
                    "email": "email",
                    "username": "username",
                    "ip_address": "ip",
                    "phone": "phone"
                }
            }
        }')
    
    JOB_ID=$(echo "$IMPORT_JOB" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
    
    if [ -n "$JOB_ID" ]; then
        echo -e "${GREEN}✅ Import job started: ${JOB_ID}${NC}"
        echo ""
        echo "Waiting for import to complete (30 seconds)..."
        sleep 30
        
        # Check job status
        JOB_STATUS=$(curl -s "${API_BASE}/import/status/${JOB_ID}")
        echo "Job Status:"
        echo "$JOB_STATUS" | python3 -m json.tool 2>/dev/null || echo "$JOB_STATUS"
        
        echo ""
        echo "Testing search with sample data..."
        SEARCH_RESULT=$(curl -s "${API_BASE}/search/quick?q=example.com&limit=10")
        RESULT_COUNT=$(echo "$SEARCH_RESULT" | grep -o '"total":[0-9]*' | grep -o '[0-9]*')
        
        if [ "$RESULT_COUNT" -gt 0 ]; then
            echo -e "${GREEN}✅ Found ${RESULT_COUNT} results for 'example.com'${NC}"
        else
            echo -e "${YELLOW}⚠️  No results found yet. Import may still be processing.${NC}"
        fi
    else
        echo -e "${RED}❌ Failed to start import job${NC}"
    fi
fi

echo ""
echo "=================================================="
echo -e "${GREEN}🎉 Testing Complete!${NC}"
echo "=================================================="
echo ""
echo "📊 View statistics: ${API_BASE}/stats"
echo "🔍 Search interface: http://localhost:8501"
echo "📖 API Documentation: ${BACKEND_URL}/docs"
echo ""
echo "To import your own data:"
echo "  1. Place MySQL dump in: data/mysql_dumps/"
echo "  2. Use the dashboard or API to start import"
echo "  3. See IMPORT_EXAMPLES.md for configuration examples"
echo ""
echo "=================================================="
