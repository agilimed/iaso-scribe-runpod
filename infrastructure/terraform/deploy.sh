#!/bin/bash

# IASO Terraform Deployment Script
# Supports multiple environments and cloud providers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="dev"
ACTION="plan"
AUTO_APPROVE=""

# Function to print colored output
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to print usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -e, --environment ENV    Environment to deploy (dev/staging/prod) [default: dev]"
    echo "  -a, --action ACTION      Terraform action (plan/apply/destroy) [default: plan]"
    echo "  -y, --auto-approve       Auto-approve terraform apply"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -e dev -a plan                    # Plan dev environment"
    echo "  $0 -e prod -a apply -y               # Apply prod environment with auto-approve"
    echo "  $0 -e staging -a destroy -y          # Destroy staging environment"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -a|--action)
            ACTION="$2"
            shift 2
            ;;
        -y|--auto-approve)
            AUTO_APPROVE="-auto-approve"
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            print_message $RED "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    print_message $RED "Invalid environment: $ENVIRONMENT"
    usage
    exit 1
fi

# Validate action
if [[ ! "$ACTION" =~ ^(plan|apply|destroy)$ ]]; then
    print_message $RED "Invalid action: $ACTION"
    usage
    exit 1
fi

# Set environment directory
ENV_DIR="environments/$ENVIRONMENT"

# Check if environment directory exists
if [ ! -d "$ENV_DIR" ]; then
    print_message $RED "Environment directory not found: $ENV_DIR"
    exit 1
fi

# Change to environment directory
cd "$ENV_DIR"

print_message $BLUE "🚀 IASO Terraform Deployment"
print_message $BLUE "============================="
print_message $YELLOW "Environment: $ENVIRONMENT"
print_message $YELLOW "Action: $ACTION"
print_message $YELLOW "Directory: $PWD"
echo ""

# Check for terraform.tfvars
if [ ! -f "terraform.tfvars" ]; then
    print_message $YELLOW "⚠️  terraform.tfvars not found!"
    if [ -f "terraform.tfvars.example" ]; then
        print_message $YELLOW "   Copy terraform.tfvars.example to terraform.tfvars and update values"
        exit 1
    fi
fi

# Initialize Terraform
print_message $GREEN "📦 Initializing Terraform..."
terraform init -upgrade

# Validate configuration
print_message $GREEN "✅ Validating configuration..."
terraform validate

# Format check
print_message $GREEN "📐 Checking formatting..."
terraform fmt -check -recursive || {
    print_message $YELLOW "⚠️  Some files need formatting. Run 'terraform fmt -recursive'"
}

# Execute action
case $ACTION in
    plan)
        print_message $GREEN "📋 Creating execution plan..."
        terraform plan -out=tfplan
        print_message $GREEN "✅ Plan saved to tfplan"
        print_message $YELLOW "   Review the plan and run with -a apply to deploy"
        ;;
    apply)
        if [ -f "tfplan" ]; then
            print_message $GREEN "🚀 Applying saved plan..."
            terraform apply $AUTO_APPROVE tfplan
            rm -f tfplan
        else
            print_message $GREEN "🚀 Applying configuration..."
            terraform apply $AUTO_APPROVE
        fi
        
        if [ $? -eq 0 ]; then
            print_message $GREEN "✅ Deployment successful!"
            
            # Show outputs
            print_message $BLUE "📊 Deployment Outputs:"
            terraform output -json | jq '.'
            
            # Show connection instructions
            print_message $BLUE "🔗 Connection Instructions:"
            echo "   kubectl config use-context $(terraform output -raw eks_cluster_name 2>/dev/null || echo 'your-cluster')"
            echo "   kubectl -n $(terraform output -raw namespace) get pods"
            echo ""
            echo "   To access services locally:"
            echo "   kubectl -n $(terraform output -raw namespace) port-forward svc/iaso-api-gateway 8080:8080"
        fi
        ;;
    destroy)
        print_message $RED "⚠️  WARNING: This will destroy all resources!"
        if [ -z "$AUTO_APPROVE" ]; then
            read -p "Are you sure? (yes/no): " confirm
            if [ "$confirm" != "yes" ]; then
                print_message $YELLOW "Cancelled"
                exit 0
            fi
        fi
        
        print_message $RED "💥 Destroying resources..."
        terraform destroy $AUTO_APPROVE
        ;;
esac

print_message $GREEN "✅ Done!"