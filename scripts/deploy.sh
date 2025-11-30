#!/bin/bash

# AWS Infrastructure Deployment Script
# This script deploys the complete hotel review NLP application to AWS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-prod}
AWS_REGION=${2:-ap-south-1}  # Default to Mumbai for India users
PROJECT_NAME="hotel-review-nlp"

print_status() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if Terraform is installed
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform is not installed. Please install it first."
        exit 1
    fi
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials are not configured. Please run 'aws configure'."
        exit 1
    fi
    
    print_success "Prerequisites check completed"
}

# Initialize Terraform backend
setup_terraform_backend() {
    print_status "Setting up Terraform backend..."
    
    # Create S3 bucket for Terraform state
    BUCKET_NAME="${PROJECT_NAME}-terraform-state-$(date +%s)"
    
    aws s3 mb "s3://${BUCKET_NAME}" --region "${AWS_REGION}" || {
        print_error "Failed to create S3 bucket for Terraform state"
        exit 1
    }
    
    # Enable versioning
    aws s3api put-bucket-versioning \
        --bucket "${BUCKET_NAME}" \
        --versioning-configuration Status=Enabled
    
    # Create DynamoDB table for state locking
    aws dynamodb create-table \
        --table-name "${PROJECT_NAME}-terraform-lock" \
        --attribute-definitions AttributeName=LockID,AttributeType=S \
        --key-schema AttributeName=LockID,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --region "${AWS_REGION}" || {
        print_error "Failed to create DynamoDB table for Terraform locking"
    }
    
    # Update Terraform backend configuration
    cat > aws-infrastructure/terraform/backend.tf << EOF
terraform {
  backend "s3" {
    bucket         = "${BUCKET_NAME}"
    key            = "${ENVIRONMENT}/terraform.tfstate"
    region         = "${AWS_REGION}"
    dynamodb_table = "${PROJECT_NAME}-terraform-lock"
    encrypt        = true
  }
}
EOF
    
    print_success "Terraform backend configured"
}

# Deploy infrastructure
deploy_infrastructure() {
    print_status "Deploying AWS infrastructure..."
    
    cd aws-infrastructure/terraform
    
    # Initialize Terraform with backend reconfiguration
    terraform init -reconfigure
    
    # Create terraform.tfvars
    cat > terraform.tfvars << EOF
aws_region = "${AWS_REGION}"
environment = "${ENVIRONMENT}"
project_name = "${PROJECT_NAME}"
monitoring_email = "$(git config user.email || echo "admin@example.com")"
github_repo = "$(git config --get remote.origin.url | sed 's/.*github.com[:/]\([^.]*\).git/\1/' || echo "")"
EOF
    
    # Plan and apply
    terraform plan -var-file=terraform.tfvars
    terraform apply -var-file=terraform.tfvars -auto-approve
    
    # Get outputs
    terraform output -json > ../../terraform-outputs.json
    
    cd ../..
    
    print_success "Infrastructure deployed successfully"
}

# Build and push Docker images
build_and_push_images() {
    print_status "Building and pushing Docker images..."
    
    # Get ECR repository URLs from Terraform outputs
    BACKEND_REPO=$(jq -r '.ecr_backend_repository_url.value' terraform-outputs.json)
    FRONTEND_REPO=$(jq -r '.ecr_frontend_repository_url.value' terraform-outputs.json)
    
    # Login to ECR
    aws ecr get-login-password --region "${AWS_REGION}" | docker login --username AWS --password-stdin "${BACKEND_REPO%%/*}"
    
    # Build and push backend image
    print_status "Building backend image..."
    cd backend
    docker build -t "${BACKEND_REPO}:latest" .
    docker push "${BACKEND_REPO}:latest"
    cd ..
    
    # Build and push frontend image  
    print_status "Building frontend image..."
    cd frontend
    docker build -t "${FRONTEND_REPO}:latest" .
    docker push "${FRONTEND_REPO}:latest"
    cd ..
    
    print_success "Docker images built and pushed"
}

# Update ECS services
update_services() {
    print_status "Updating ECS services..."
    
    # Get cluster and service names from outputs
    CLUSTER_NAME=$(jq -r '.ecs_cluster_name.value' terraform-outputs.json)
    BACKEND_SERVICE=$(jq -r '.backend_service_name.value' terraform-outputs.json)
    FRONTEND_SERVICE=$(jq -r '.frontend_service_name.value' terraform-outputs.json)
    
    # Force new deployment
    aws ecs update-service \
        --cluster "${CLUSTER_NAME}" \
        --service "${BACKEND_SERVICE}" \
        --force-new-deployment \
        --region "${AWS_REGION}"
    
    aws ecs update-service \
        --cluster "${CLUSTER_NAME}" \
        --service "${FRONTEND_SERVICE}" \
        --force-new-deployment \
        --region "${AWS_REGION}"
    
    # Wait for services to be stable
    print_status "Waiting for services to stabilize..."
    aws ecs wait services-stable \
        --cluster "${CLUSTER_NAME}" \
        --services "${BACKEND_SERVICE}" \
        --region "${AWS_REGION}"
    
    aws ecs wait services-stable \
        --cluster "${CLUSTER_NAME}" \
        --services "${FRONTEND_SERVICE}" \
        --region "${AWS_REGION}"
    
    print_success "ECS services updated"
}

# Run health checks
health_check() {
    print_status "Running health checks..."
    
    ALB_DNS=$(jq -r '.load_balancer_dns_name.value' terraform-outputs.json)
    
    # Wait a bit for ALB to be ready
    sleep 30
    
    # Test health endpoint
    if curl -f "http://${ALB_DNS}/health" > /dev/null 2>&1; then
        print_success "Application health check passed"
    else
        print_error "Application health check failed"
        exit 1
    fi
    
    # Test API endpoint
    if curl -f "http://${ALB_DNS}/" > /dev/null 2>&1; then
        print_success "API health check passed"
    else
        print_error "API health check failed"
        exit 1
    fi
}

# Display deployment information
show_deployment_info() {
    print_success "Deployment completed successfully!"
    
    echo ""
    echo "=== DEPLOYMENT INFORMATION ==="
    echo "Environment: ${ENVIRONMENT}"
    echo "Region: ${AWS_REGION}"
    
    if [ -f terraform-outputs.json ]; then
        echo "Application URL: $(jq -r '.application_url.value' terraform-outputs.json)"
        echo "API URL: $(jq -r '.api_url.value' terraform-outputs.json)"
        echo "CloudWatch Dashboard: $(jq -r '.cloudwatch_dashboard_url.value' terraform-outputs.json)"
        echo ""
        echo "=== NEXT STEPS ==="
        echo "1. Configure your domain name (if using custom domain)"
        echo "2. Set up SSL certificate in AWS Certificate Manager"
        echo "3. Update GitHub repository secrets for CI/CD:"
        echo "   - AWS_ROLE_TO_ASSUME: $(jq -r '.github_actions_role_arn.value' terraform-outputs.json)"
        echo "   - ALB_DNS_NAME: $(jq -r '.load_balancer_dns_name.value' terraform-outputs.json)"
        echo "   - ML_ARTIFACTS_BUCKET: $(jq -r '.s3_ml_artifacts_bucket.value' terraform-outputs.json)"
        echo "4. Subscribe to SNS topic for monitoring alerts"
        echo ""
        echo "=== MONITORING ==="
        echo "CloudWatch Dashboard: $(jq -r '.cloudwatch_dashboard_url.value' terraform-outputs.json)"
        echo "SNS Topic ARN: $(jq -r '.sns_topic_arn.value' terraform-outputs.json)"
    fi
}

# Cleanup function
cleanup() {
    if [ $? -ne 0 ]; then
        print_error "Deployment failed. Check the logs above for details."
        exit 1
    fi
}

trap cleanup EXIT

# Main execution
main() {
    echo "=== AWS DEPLOYMENT SCRIPT ==="
    echo "Environment: ${ENVIRONMENT}"
    echo "Region: ${AWS_REGION}"
    echo "Project: ${PROJECT_NAME}"
    echo ""
    
    check_prerequisites
    setup_terraform_backend
    deploy_infrastructure
    build_and_push_images
    update_services
    health_check
    show_deployment_info
}

# Run main function
main "$@"
