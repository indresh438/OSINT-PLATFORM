#!/bin/bash

# OSINT Platform - Stop Script

# Detect compose command
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif command -v podman-compose &> /dev/null; then
    COMPOSE_CMD="podman-compose"
else
    echo "❌ Neither docker-compose nor podman-compose found"
    exit 1
fi

echo "🛑 Stopping OSINT Platform services..."

$COMPOSE_CMD down

echo "✅ All services stopped"
echo ""
echo "To remove all data (destructive!):"
echo "  $COMPOSE_CMD down -v"
echo ""
echo "To restart:"
echo "  ./start.sh"
