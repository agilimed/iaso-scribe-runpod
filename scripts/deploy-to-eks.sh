#!/bin/bash

# Deploy IASO services to EKS cluster
# This script handles the complete deployment process including fixes

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}🚀 IASO EKS Deployment Script${NC}"
    echo -e "${BLUE}=============================${NC}"
}

usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --fix-only        Only fix deployment issues"
    echo "  --deploy-only     Only deploy services (skip fixes)"
    echo "  --namespace NAME  Kubernetes namespace (default: nexuscare)"
    echo "  --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Full deployment with fixes"
    echo "  $0 --fix-only         # Only fix issues"
    echo "  $0 --deploy-only      # Only deploy services"
}

# Default values
NAMESPACE="nexuscare"
FIX_ISSUES=true
DEPLOY_SERVICES=true

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --fix-only)
            DEPLOY_SERVICES=false
            shift
            ;;
        --deploy-only)
            FIX_ISSUES=false
            shift
            ;;
        --namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        --help|-h)
            print_header
            usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            usage
            exit 1
            ;;
    esac
done

print_header

# Check dependencies
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl is required but not installed${NC}"
    exit 1
fi

if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}❌ Not connected to Kubernetes cluster${NC}"
    echo "Please configure kubectl to connect to your EKS cluster"
    exit 1
fi

# Step 1: Fix deployment issues
if [ "$FIX_ISSUES" = true ]; then
    echo -e "${YELLOW}🔧 Step 1: Fixing deployment issues...${NC}"
    $SCRIPT_DIR/ai-services.sh fix-issues
    echo ""
fi

# Step 2: Deploy services
if [ "$DEPLOY_SERVICES" = true ]; then
    echo -e "${YELLOW}🚀 Step 2: Deploying services...${NC}"
    
    # Check current status
    echo "Current deployment status:"
    $SCRIPT_DIR/ai-services.sh status
    echo ""
    
    # Deploy databases if needed
    echo -e "${YELLOW}📦 Checking database services...${NC}"
    if ! kubectl get service qdrant -n $NAMESPACE &>/dev/null; then
        echo "Deploying Qdrant..."
        $SCRIPT_DIR/ai-services.sh deploy-db qdrant
    else
        echo "✅ Qdrant already deployed"
    fi
    
    if ! kubectl get service pgbouncer -n default &>/dev/null; then
        echo -e "${YELLOW}⚠️  PgBouncer not deployed. To deploy:${NC}"
        echo "   1. Update RDS endpoint in infrastructure/kubernetes/deployments/pgbouncer.yaml"
        echo "   2. Run: $0 deploy-db postgres"
    fi
    
    echo ""
    
    # Deploy AI services
    echo -e "${YELLOW}📦 Deploying AI services...${NC}"
    echo "Starting embedding service only (cost-optimized)..."
    $SCRIPT_DIR/ai-services.sh start embedding-only
    
    echo ""
    echo -e "${GREEN}✅ Deployment complete!${NC}"
    echo ""
    echo "To deploy additional services:"
    echo "  - CPU services: $SCRIPT_DIR/ai-services.sh start cpu-only"
    echo "  - All services: $SCRIPT_DIR/ai-services.sh start all"
fi

# Step 3: Final status check
echo ""
echo -e "${YELLOW}📊 Final deployment status:${NC}"
$SCRIPT_DIR/ai-services.sh status

echo ""
echo -e "${BLUE}💡 Tips:${NC}"
echo "  - Monitor costs: kubectl top nodes"
echo "  - Check logs: kubectl logs -f deployment/embeddings-service-cpu -n ai-services"
echo "  - Stop all services: $SCRIPT_DIR/ai-services.sh stop"
echo "  - Scale to zero for zero cost when not in use"