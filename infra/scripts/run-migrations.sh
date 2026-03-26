#!/bin/bash
set -euo pipefail

# BizPulse AI — Run database migrations
# Requires: golang-migrate CLI (https://github.com/golang-migrate/migrate)
#
# Usage: ./run-migrations.sh [up|down|version]

MIGRATIONS_DIR="${MIGRATIONS_DIR:-../../services/transaction-svc/migrations}"
DATABASE_URL="${DATABASE_URL:-postgres://bizpulse:changeme_in_production@localhost:5432/bizpulse?sslmode=disable}"

ACTION="${1:-up}"

echo "=== BizPulse AI Migrations ==="
echo "Action: $ACTION"
echo "Migrations: $MIGRATIONS_DIR"
echo ""

case "$ACTION" in
    up)
        migrate -path "$MIGRATIONS_DIR" -database "$DATABASE_URL" up
        echo "Migrations applied successfully."
        ;;
    down)
        echo "WARNING: This will reverse the last migration."
        read -p "Continue? (y/N) " confirm
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            migrate -path "$MIGRATIONS_DIR" -database "$DATABASE_URL" down 1
            echo "Last migration reversed."
        else
            echo "Cancelled."
        fi
        ;;
    version)
        migrate -path "$MIGRATIONS_DIR" -database "$DATABASE_URL" version
        ;;
    *)
        echo "Usage: $0 [up|down|version]"
        exit 1
        ;;
esac
