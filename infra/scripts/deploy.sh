#!/bin/bash
set -euo pipefail

# BizPulse AI — Production Deploy Script
# Pulls latest images, starts services, verifies health, rolls back on failure.
#
# Usage: ./deploy.sh [--rollback]

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
HEALTH_TIMEOUT=60  # seconds to wait for health checks
HEALTH_INTERVAL=5  # seconds between health check attempts

echo "=== BizPulse AI Deploy ==="
echo "Compose file: $COMPOSE_FILE"
echo ""

# Save current image tags for rollback
if docker compose -f "$COMPOSE_FILE" ps -q 2>/dev/null | head -1 | grep -q .; then
    echo "Saving current state for rollback..."
    docker compose -f "$COMPOSE_FILE" config > /tmp/bizpulse-rollback-compose.yml 2>/dev/null || true
fi

if [ "${1:-}" = "--rollback" ]; then
    echo "Rolling back to previous deployment..."
    if [ -f /tmp/bizpulse-rollback-compose.yml ]; then
        docker compose -f /tmp/bizpulse-rollback-compose.yml up -d
        echo "Rollback complete."
    else
        echo "ERROR: No rollback state found."
        exit 1
    fi
    exit 0
fi

# Pull latest images and rebuild
echo "Pulling and rebuilding services..."
docker compose -f "$COMPOSE_FILE" build --pull
docker compose -f "$COMPOSE_FILE" up -d

# Health check loop
echo ""
echo "Waiting for services to become healthy..."

check_health() {
    local service=$1
    local port=$2
    curl -sf "http://localhost:${port}/health" > /dev/null 2>&1
}

elapsed=0
txn_healthy=false
analytics_healthy=false

while [ $elapsed -lt $HEALTH_TIMEOUT ]; do
    if ! $txn_healthy && check_health "transaction-svc" 8080; then
        echo "  transaction-svc: healthy"
        txn_healthy=true
    fi

    if ! $analytics_healthy && check_health "analytics-svc" 8081; then
        echo "  analytics-svc: healthy"
        analytics_healthy=true
    fi

    if $txn_healthy && $analytics_healthy; then
        break
    fi

    sleep $HEALTH_INTERVAL
    elapsed=$((elapsed + HEALTH_INTERVAL))
done

echo ""

if $txn_healthy && $analytics_healthy; then
    echo "=== Deploy SUCCESS ==="
    echo "All services healthy."
    docker compose -f "$COMPOSE_FILE" ps
else
    echo "=== Deploy FAILED ==="
    echo "Services did not become healthy within ${HEALTH_TIMEOUT}s."
    echo ""

    if [ -f /tmp/bizpulse-rollback-compose.yml ]; then
        echo "Rolling back..."
        docker compose -f /tmp/bizpulse-rollback-compose.yml up -d
        echo "Rollback complete. Check logs with: docker compose logs"
    else
        echo "No rollback state available. Check logs with: docker compose logs"
    fi

    exit 1
fi
