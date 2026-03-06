#!/bin/bash

# OSINT Platform - Quick Start Script
# This script helps you set up and start the OSINT platform

set -e

echo "=================================================="
echo "🔍 OSINT Platform - Quick Start"
echo "=================================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Detect container runtime (Docker or Podman)
DOCKER_ACCESSIBLE=false
PODMAN_ACCESSIBLE=false

# Check if Docker is accessible (not just installed)
if command -v docker &> /dev/null; then
    if docker ps &> /dev/null; then
        DOCKER_ACCESSIBLE=true
    fi
fi

# Check if Podman is accessible
if command -v podman &> /dev/null; then
    if podman ps &> /dev/null; then
        PODMAN_ACCESSIBLE=true
    fi
fi

# Choose the appropriate runtime
# Prefer podman-compose if available (more reliable on modern systems)
if [ "$PODMAN_ACCESSIBLE" = true ] && command -v podman-compose &> /dev/null; then
    CONTAINER_CMD="podman"
    COMPOSE_CMD="podman-compose"
elif [ "$DOCKER_ACCESSIBLE" = true ]; then
    CONTAINER_CMD="docker"
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        echo -e "${RED}❌ docker-compose is not installed.${NC}"
        exit 1
    fi
elif [ "$PODMAN_ACCESSIBLE" = true ]; then
    CONTAINER_CMD="podman"
    if command -v podman-compose &> /dev/null; then
        COMPOSE_CMD="podman-compose"
    else
        echo -e "${YELLOW}⚠️  podman-compose is not installed. Installing...${NC}"
        sudo apt install -y podman-compose || exit 1
        COMPOSE_CMD="podman-compose"
    fi
elif command -v docker &> /dev/null; then
    # Docker exists but not accessible - need to add user to docker group
    echo -e "${YELLOW}⚠️  Docker is installed but you don't have permission to use it.${NC}"
    echo -e "${YELLOW}Adding your user to the docker group...${NC}"
    sudo usermod -aG docker $USER
    echo -e "${GREEN}✅ Added to docker group. Please log out and log back in, then run this script again.${NC}"
    echo -e "${YELLOW}Or run: newgrp docker${NC}"
    exit 1
else
    echo -e "${RED}❌ Neither Docker nor Podman is installed or accessible.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Using $CONTAINER_CMD with $COMPOSE_CMD${NC}"
echo ""

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p data/{mysql,mongodb,elasticsearch,neo4j,redis,mysql_dumps} logs

# Set permissions (skip if already set to avoid errors)
echo "🔑 Setting permissions..."
chmod -R 777 data logs 2>/dev/null || true

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please review and update .env file with your settings${NC}"
fi

# Increase vm.max_map_count for Elasticsearch
echo "⚙️  Configuring system for Elasticsearch..."
sudo sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf > /dev/null

echo ""
echo "🚀 Starting OSINT Platform services..."
echo ""

# Start services
$COMPOSE_CMD up -d

echo ""
echo "⏳ Waiting for services to initialize (this may take 2-3 minutes)..."
sleep 30

# Check service health
echo ""
echo "🏥 Checking service health..."

MAX_RETRIES=20
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend is ready!${NC}"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT+1))
    echo "⏳ Waiting for backend... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 5
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}❌ Backend failed to start. Check logs with: $COMPOSE_CMD logs backend${NC}"
    exit 1
fi

# Initialize indices
echo ""
echo "🔧 Initializing database indices..."
curl -s -X POST http://localhost:8000/api/v1/import/initialize > /dev/null 2>&1
sleep 5

echo ""
echo "=================================================="
echo -e "${GREEN}✅ OSINT Platform is ready!${NC}"
echo "=================================================="
echo ""
echo "📊 Access Points:"
echo "  - Dashboard:    http://localhost:8501"
echo "  - API Docs:     http://localhost:8000/docs"
echo "  - Neo4j Browser: http://localhost:7474"
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
echo "  - View logs:    $COMPOSE_CMD logs -f"
echo "  - Stop services: $COMPOSE_CMD down"
echo "  - Restart:      $COMPOSE_CMD restart"
echo ""
echo "=================================================="
