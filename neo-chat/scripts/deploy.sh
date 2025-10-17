#!/bin/bash
# NEO Chat Deployment Script
# Constitution Principle I: Docker Build from Source with commit SHA tracking

set -e  # Exit on error

echo "🚀 NEO Chat Deployment Script"
echo "================================"

# Configuration
REPO_URL="${REPO_URL:-https://github.com/your-org/neo-chat.git}"
DEPLOY_DIR="${DEPLOY_DIR:-/opt/neo-chat}"
BRANCH="${BRANCH:-main}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v git &> /dev/null; then
        log_error "git is not installed"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        log_error "docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose is not installed"
        exit 1
    fi
    
    log_info "Prerequisites check passed ✓"
}

# Clone or update repository
clone_or_update() {
    log_info "Cloning/updating repository..."
    
    if [ -d "$DEPLOY_DIR/.git" ]; then
        log_info "Repository exists, pulling latest changes..."
        cd "$DEPLOY_DIR"
        git fetch origin
        git checkout "$BRANCH"
        git pull origin "$BRANCH"
    else
        log_info "Cloning repository..."
        git clone "$REPO_URL" "$DEPLOY_DIR"
        cd "$DEPLOY_DIR"
        git checkout "$BRANCH"
    fi
    
    # Get commit SHA
    COMMIT_SHA=$(git rev-parse HEAD)
    COMMIT_SHORT=$(git rev-parse --short HEAD)
    COMMIT_DATE=$(git log -1 --format=%cd --date=iso)
    
    log_info "Commit SHA: $COMMIT_SHA"
    log_info "Commit Date: $COMMIT_DATE"
    
    # Save build info
    cat > build-info.txt <<EOF
Build Information
=================
Commit SHA: $COMMIT_SHA
Commit Short: $COMMIT_SHORT
Branch: $BRANCH
Build Date: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
Build Host: $(hostname)
EOF
    
    log_info "Build info saved to build-info.txt"
}

# Build Docker image
build_image() {
    log_info "Building Docker image from source..."
    
    cd "$DEPLOY_DIR"
    
    # Build with commit SHA as tag
    docker build \
        -f docker/Dockerfile \
        -t "neo-chat:$COMMIT_SHORT" \
        -t "neo-chat:latest" \
        --build-arg COMMIT_SHA="$COMMIT_SHA" \
        --build-arg BUILD_DATE="$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
        .
    
    log_info "Docker image built successfully ✓"
    log_info "Tags: neo-chat:$COMMIT_SHORT, neo-chat:latest"
}

# Verify build
verify_build() {
    log_info "Verifying Docker image..."
    
    if docker inspect "neo-chat:$COMMIT_SHORT" &> /dev/null; then
        log_info "Image verification passed ✓"
        
        # Show image details
        docker images "neo-chat:$COMMIT_SHORT" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    else
        log_error "Image verification failed"
        exit 1
    fi
}

# Deploy
deploy() {
    log_info "Deploying application..."
    
    cd "$DEPLOY_DIR"
    
    # Stop existing containers
    if docker-compose ps | grep -q "Up"; then
        log_warn "Stopping existing containers..."
        docker-compose down
    fi
    
    # Start services
    log_info "Starting services..."
    docker-compose up -d
    
    # Wait for health check
    log_info "Waiting for health check..."
    sleep 10
    
    # Check if services are running
    if docker-compose ps | grep -q "Up"; then
        log_info "Deployment successful ✓"
        docker-compose ps
    else
        log_error "Deployment failed - services not running"
        docker-compose logs --tail=50
        exit 1
    fi
}

# Rollback
rollback() {
    log_warn "Rolling back to previous version..."
    
    cd "$DEPLOY_DIR"
    
    # Get previous commit
    PREV_COMMIT=$(git rev-parse HEAD~1)
    PREV_SHORT=$(git rev-parse --short HEAD~1)
    
    log_info "Rolling back to commit: $PREV_SHORT"
    
    # Checkout previous commit
    git checkout "$PREV_COMMIT"
    
    # Rebuild and deploy
    build_image
    verify_build
    deploy
}

# Main execution
main() {
    log_info "Starting deployment process..."
    
    check_prerequisites
    clone_or_update
    build_image
    verify_build
    deploy
    
    log_info "================================"
    log_info "✅ Deployment completed successfully!"
    log_info "Commit: $COMMIT_SHORT"
    log_info "Application: http://localhost:8000"
    log_info "Health: http://localhost:8000/health"
}

# Handle arguments
case "${1:-}" in
    rollback)
        rollback
        ;;
    *)
        main
        ;;
esac
