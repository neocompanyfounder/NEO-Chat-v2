#!/bin/bash
# Supabase Self-Hosted Setup Script

set -e  # Exit on error

echo "🗄️  Supabase Setup Script"
echo "========================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
check_docker() {
    log_info "Checking Docker..."
    
    if ! docker info &> /dev/null; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    log_info "Docker is running ✓"
}

# Setup environment
setup_env() {
    log_info "Setting up environment..."
    
    cd docker/supabase
    
    if [ ! -f .env ]; then
        log_warn ".env file not found, creating from example..."
        cp .env.example .env
        log_warn "⚠️  Please edit docker/supabase/.env with your own secrets!"
        log_warn "Generate JWT secret: openssl rand -base64 32"
    else
        log_info ".env file exists ✓"
    fi
}

# Start Supabase services
start_services() {
    log_info "Starting Supabase services..."
    
    # Get script directory and navigate to docker/supabase
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
    SUPABASE_DIR="$PROJECT_ROOT/docker/supabase"
    
    if [ ! -d "$SUPABASE_DIR" ]; then
        log_error "Supabase directory not found: $SUPABASE_DIR"
        exit 1
    fi
    
    cd "$SUPABASE_DIR"
    docker-compose up -d
    
    log_info "Waiting for services to be ready..."
    sleep 15
    
    # Check if services are running
    if docker-compose ps | grep -q "Up"; then
        log_info "Supabase services started ✓"
        docker-compose ps
    else
        log_error "Failed to start services"
        docker-compose logs --tail=50
        exit 1
    fi
}

# Run migrations
run_migrations() {
    log_info "Running database migrations..."
    
    cd ../..
    
    if [ -f scripts/run_migrations.sh ]; then
        bash scripts/run_migrations.sh
    else
        log_warn "Migration script not found, skipping..."
    fi
}

# Verify setup
verify_setup() {
    log_info "Verifying Supabase setup..."
    
    # Check PostgreSQL
    if docker exec supabase-db pg_isready -U postgres &> /dev/null; then
        log_info "PostgreSQL is ready ✓"
    else
        log_error "PostgreSQL is not ready"
        exit 1
    fi
    
    # Check pgvector extension
    if docker exec supabase-db psql -U postgres -c "SELECT * FROM pg_extension WHERE extname='vector';" | grep -q "vector"; then
        log_info "pgvector extension installed ✓"
    else
        log_warn "pgvector extension not found, installing..."
        docker exec supabase-db psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"
        log_info "pgvector extension installed ✓"
    fi
    
    # Show connection info
    log_info "========================="
    log_info "✅ Supabase is ready!"
    log_info ""
    log_info "Connection Details:"
    log_info "  PostgreSQL (Direct): postgresql://postgres:password@localhost:5432/postgres"
    log_info "  PostgreSQL (Pooled): postgresql://postgres:password@localhost:6543/postgres"
    log_info "  PostgREST API: http://localhost:3000"
    log_info "  Realtime: http://localhost:4000"
    log_info "  Storage: http://localhost:5000"
    log_info ""
    log_info "⚠️  Remember to:"
    log_info "  1. Update .env with your Supabase connection details"
    log_info "  2. Run migrations: bash scripts/run_migrations.sh"
    log_info "  3. Set up RLS policies for security"
}

# Stop services
stop_services() {
    log_warn "Stopping Supabase services..."
    cd docker/supabase
    docker-compose down
    log_info "Services stopped ✓"
}

# Main execution
main() {
    check_docker
    setup_env
    start_services
    run_migrations
    verify_setup
}

# Handle arguments
case "${1:-}" in
    stop)
        stop_services
        ;;
    restart)
        stop_services
        main
        ;;
    *)
        main
        ;;
esac
