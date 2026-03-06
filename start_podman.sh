#!/bin/bash

# OSINT Platform - Podman Start Script
set -e

echo "=================================================="
echo "🔍 OSINT Platform - Starting with Podman"
echo "=================================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "📁 Creating necessary directories..."
mkdir -p data/{mysql,mongodb,elasticsearch,neo4j,redis,mysql_dumps} logs

echo "🔑 Setting permissions..."
chmod -R 777 data logs 2>/dev/null || true

echo "⚙️  Configuring system for Elasticsearch..."
sudo sysctl -w vm.max_map_count=262144 > /dev/null 2>&1 || true

echo ""
echo "🚀 Starting OSINT Platform services with Podman..."
echo ""

# Start services
podman-compose up -d

echo ""
echo "⏳ Waiting for services to initialize (this may take 3-5 minutes)..."
sleep 60

# Check service health
echo ""
echo "🏥 Checking service health..."

MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend is ready!${NC}"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT+1))
    if [ $((RETRY_COUNT % 5)) -eq 0 ]; then
        echo "⏳ Still waiting for backend... ($RETRY_COUNT/$MAX_RETRIES)"
    fi
    sleep 5
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}❌ Backend failed to start. Check logs with: podman-compose logs backend${NC}"
    echo ""
    echo "Showing last 20 lines of backend logs:"
    podman-compose logs --tail=20 backend
    exit 1
fi

echo ""
echo "=================================================="
echo -e "${GREEN}✅ OSINT Platform is ready!${NC}"
echo "=================================================="
echo ""
echo "📊 Access Points:"
echo "  - Dashboard:     http://localhost:8501"
echo "  - API Docs:      http://localhost:8000/docs"
echo "  - Neo4j Browser: http://localhost:7475"
echo ""
echo "🔐 Default Credentials:"
echo "  - Neo4j:        neo4j / osint_neo4j_pass"
echo "  - MySQL:        osint_user / osint_pass"
echo "  - MongoDB:      osint_admin / osint_mongo_pass"
echo ""
echo "📖 Next Steps:"
echo "  1. Place MySQL dumps in: data/mysql_dumps/"
echo "  2. Open dashboard at http://localhost:8501"
echo "  3. Go to 'Import Data' tab to start importing"
echo ""
echo "📝 Useful Commands:"
echo "  - View logs:    podman-compose logs -f"
echo "  - Stop services: podman-compose down"
echo "  - Restart:      podman-compose restart"
echo "  - Status:       podman-compose ps"
echo ""
echo "=================================================="
