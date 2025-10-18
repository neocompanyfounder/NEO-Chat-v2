#!/bin/bash
# Database Migration Runner

set -e

echo "🔄 Running Database Migrations"
echo "=============================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Load environment
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Database connection
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-postgres}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${POSTGRES_PASSWORD:-your-super-secret-and-long-postgres-password}"

MIGRATIONS_DIR="src/db/migrations"

# Check if migrations directory exists
if [ ! -d "$MIGRATIONS_DIR" ]; then
    log_error "Migrations directory not found: $MIGRATIONS_DIR"
    exit 1
fi

# Run migrations in order
log_info "Found migrations directory: $MIGRATIONS_DIR"

for migration in $(ls -1 $MIGRATIONS_DIR/*.sql | sort); do
    migration_name=$(basename "$migration")
    log_info "Running migration: $migration_name"
    
    # Execute migration
    PGPASSWORD="$DB_PASSWORD" psql \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        -f "$migration" \
        -v ON_ERROR_STOP=1
    
    if [ $? -eq 0 ]; then
        log_info "✓ $migration_name completed"
    else
        log_error "✗ $migration_name failed"
        exit 1
    fi
done

log_info "=============================="
log_info "✅ All migrations completed successfully!"

# Verify schema
log_info "Verifying schema..."
PGPASSWORD="$DB_PASSWORD" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -c "\dt" \
    -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public';"

log_info "Schema verification complete ✓"
