#!/bin/bash

# OSINT Platform - Status Check Script

# Detect compose command
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif command -v podman-compose &> /dev/null; then
    COMPOSE_CMD="podman-compose"
else
    echo "❌ Neither docker-compose nor podman-compose found"
    exit 1
fi

echo "=================================================="
echo "🔍 OSINT Platform - Status Check"
echo "=================================================="
echo ""

# Check if containers are running
echo "📦 Containers:"
$COMPOSE_CMD ps

echo ""
echo "=================================================="
echo "🏥 Service Health:"
echo "=================================================="

# Check backend
echo -n "Backend API:       "
if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    echo "✅ Online"
else
    echo "❌ Offline"
fi

# Check frontend
echo -n "Frontend (Streamlit): "
if curl -s http://localhost:8501 > /dev/null 2>&1; then
    echo "✅ Online"
else
    echo "❌ Offline"
fi

# Check MySQL
echo -n "MySQL:            "
if $COMPOSE_CMD exec -T mysql mysqladmin -uosint_user -posint_pass ping > /dev/null 2>&1; then
    echo "✅ Online"
else
    echo "❌ Offline"
fi

# Check MongoDB
echo -n "MongoDB:          "
if $COMPOSE_CMD exec -T mongodb mongosh --quiet --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
    echo "✅ Online"
else
    echo "❌ Offline"
fi

# Check Elasticsearch
echo -n "Elasticsearch:    "
if curl -s http://localhost:9200/_cluster/health > /dev/null 2>&1; then
    echo "✅ Online"
else
    echo "❌ Offline"
fi

# Check Neo4j
echo -n "Neo4j:            "
if curl -s http://localhost:7474 > /dev/null 2>&1; then
    echo "✅ Online"
else
    echo "❌ Offline"
fi

# Check Redis
echo -n "Redis:            "
if $COMPOSE_CMD exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Online"
else
    echo "❌ Offline"
fi

echo ""
echo "=================================================="
echo "📊 Statistics:"
echo "=================================================="

# Get statistics from API
if curl -s http://localhost:8000/api/v1/stats > /dev/null 2>&1; then
    STATS=$(curl -s http://localhost:8000/api/v1/stats)
    
    echo ""
    echo "Elasticsearch:"
    echo "$STATS" | grep -o '"total_entities":[0-9]*' | head -1 | sed 's/"total_entities":/  Total Entities: /'
    
    echo ""
    echo "MongoDB:"
    echo "$STATS" | grep -o '"total_entities":[0-9]*' | tail -1 | sed 's/"total_entities":/  Total Entities: /'
    
    echo ""
    echo "Neo4j:"
    echo "$STATS" | grep -o '"total_nodes":[0-9]*' | sed 's/"total_nodes":/  Total Nodes: /'
    echo "$STATS" | grep -o '"total_relationships":[0-9]*' | sed 's/"total_relationships":/  Total Relationships: /'
else
    echo "Unable to fetch statistics. Backend may be offline."
fi

echo ""
echo "=================================================="
echo ""
echo "📖 Quick Links:"
echo "  - Dashboard:    http://localhost:8501"
echo "  - API Docs:     http://localhost:8000/docs"
echo "  - Neo4j Browser: http://localhost:7474"
echo ""
echo "=================================================="
