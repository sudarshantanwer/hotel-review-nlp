#!/bin/bash

# Deployment Progress Monitor
# This script monitors the AWS deployment progress in real-time

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
REGION=${1:-ap-south-1}
PROJECT_NAME="hotel-review-nlp"
ENVIRONMENT=${2:-prod}
NAME_PREFIX="${PROJECT_NAME}-${ENVIRONMENT}"

print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}  AWS Deployment Progress Monitor${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo "Region: $REGION"
    echo "Environment: $ENVIRONMENT"
    echo "Project: $PROJECT_NAME"
    echo ""
}

check_terraform_progress() {
    echo -e "${YELLOW}📊 Checking Terraform State...${NC}"
    
    if [ -f "aws-infrastructure/terraform/terraform.tfstate" ]; then
        echo "✅ Terraform state file exists"
        
        # Check for key resources
        cd aws-infrastructure/terraform
        
        if terraform show | grep -q "aws_vpc.main"; then
            echo "✅ VPC created"
        else
            echo "⏳ VPC pending..."
        fi
        
        if terraform show | grep -q "aws_db_instance.main"; then
            echo "✅ RDS Database created"
        else
            echo "⏳ RDS Database pending..."
        fi
        
        if terraform show | grep -q "aws_ecs_cluster.main"; then
            echo "✅ ECS Cluster created"
        else
            echo "⏳ ECS Cluster pending..."
        fi
        
        cd ../..
    else
        echo "⏳ Terraform not initialized yet"
    fi
    echo ""
}

check_aws_resources() {
    echo -e "${YELLOW}🔍 Checking AWS Resources...${NC}"
    
    # Check VPC
    VPC_ID=$(aws ec2 describe-vpcs --filters "Name=tag:Name,Values=${NAME_PREFIX}-vpc" --query "Vpcs[0].VpcId" --output text --region $REGION 2>/dev/null || echo "None")
    if [ "$VPC_ID" != "None" ] && [ "$VPC_ID" != "null" ]; then
        echo "✅ VPC: $VPC_ID"
    else
        echo "⏳ VPC: Not created yet"
    fi
    
    # Check ECS Cluster
    ECS_STATUS=$(aws ecs describe-clusters --clusters "${NAME_PREFIX}-cluster" --query "clusters[0].status" --output text --region $REGION 2>/dev/null || echo "NOTFOUND")
    if [ "$ECS_STATUS" = "ACTIVE" ]; then
        echo "✅ ECS Cluster: Active"
    elif [ "$ECS_STATUS" != "NOTFOUND" ]; then
        echo "⏳ ECS Cluster: $ECS_STATUS"
    else
        echo "⏳ ECS Cluster: Not created yet"
    fi
    
    # Check RDS
    RDS_STATUS=$(aws rds describe-db-instances --db-instance-identifier "${NAME_PREFIX}-postgres" --query "DBInstances[0].DBInstanceStatus" --output text --region $REGION 2>/dev/null || echo "NOTFOUND")
    if [ "$RDS_STATUS" = "available" ]; then
        echo "✅ RDS Database: Available"
    elif [ "$RDS_STATUS" != "NOTFOUND" ]; then
        echo "⏳ RDS Database: $RDS_STATUS (this takes 10-15 minutes)"
    else
        echo "⏳ RDS Database: Not created yet"
    fi
    
    # Check Load Balancer
    ALB_STATE=$(aws elbv2 describe-load-balancers --names "${NAME_PREFIX}-alb" --query "LoadBalancers[0].State.Code" --output text --region $REGION 2>/dev/null || echo "NOTFOUND")
    if [ "$ALB_STATE" = "active" ]; then
        ALB_DNS=$(aws elbv2 describe-load-balancers --names "${NAME_PREFIX}-alb" --query "LoadBalancers[0].DNSName" --output text --region $REGION 2>/dev/null)
        echo "✅ Load Balancer: Active"
        echo "   📍 URL: http://$ALB_DNS"
    elif [ "$ALB_STATE" != "NOTFOUND" ]; then
        echo "⏳ Load Balancer: $ALB_STATE"
    else
        echo "⏳ Load Balancer: Not created yet"
    fi
    
    echo ""
}

check_ecs_services() {
    echo -e "${YELLOW}🐳 Checking ECS Services...${NC}"
    
    # Check if cluster exists first
    if aws ecs describe-clusters --clusters "${NAME_PREFIX}-cluster" --region $REGION >/dev/null 2>&1; then
        # Backend Service
        BACKEND_STATUS=$(aws ecs describe-services --cluster "${NAME_PREFIX}-cluster" --services "${NAME_PREFIX}-backend" --query "services[0].status" --output text --region $REGION 2>/dev/null || echo "NOTFOUND")
        if [ "$BACKEND_STATUS" = "ACTIVE" ]; then
            RUNNING_TASKS=$(aws ecs describe-services --cluster "${NAME_PREFIX}-cluster" --services "${NAME_PREFIX}-backend" --query "services[0].runningCount" --output text --region $REGION 2>/dev/null || echo "0")
            DESIRED_TASKS=$(aws ecs describe-services --cluster "${NAME_PREFIX}-cluster" --services "${NAME_PREFIX}-backend" --query "services[0].desiredCount" --output text --region $REGION 2>/dev/null || echo "0")
            echo "✅ Backend Service: $RUNNING_TASKS/$DESIRED_TASKS tasks running"
        elif [ "$BACKEND_STATUS" != "NOTFOUND" ]; then
            echo "⏳ Backend Service: $BACKEND_STATUS"
        else
            echo "⏳ Backend Service: Not created yet"
        fi
        
        # Frontend Service
        FRONTEND_STATUS=$(aws ecs describe-services --cluster "${NAME_PREFIX}-cluster" --services "${NAME_PREFIX}-frontend" --query "services[0].status" --output text --region $REGION 2>/dev/null || echo "NOTFOUND")
        if [ "$FRONTEND_STATUS" = "ACTIVE" ]; then
            RUNNING_TASKS=$(aws ecs describe-services --cluster "${NAME_PREFIX}-cluster" --services "${NAME_PREFIX}-frontend" --query "services[0].runningCount" --output text --region $REGION 2>/dev/null || echo "0")
            DESIRED_TASKS=$(aws ecs describe-services --cluster "${NAME_PREFIX}-cluster" --services "${NAME_PREFIX}-frontend" --query "services[0].desiredCount" --output text --region $REGION 2>/dev/null || echo "0")
            echo "✅ Frontend Service: $RUNNING_TASKS/$DESIRED_TASKS tasks running"
        elif [ "$FRONTEND_STATUS" != "NOTFOUND" ]; then
            echo "⏳ Frontend Service: $FRONTEND_STATUS"
        else
            echo "⏳ Frontend Service: Not created yet"
        fi
    else
        echo "⏳ ECS Cluster not available yet"
    fi
    
    echo ""
}

check_deployment_logs() {
    echo -e "${YELLOW}📋 Recent CloudFormation/Deployment Events...${NC}"
    
    # Check for CloudFormation stacks (in case Terraform creates any)
    STACKS=$(aws cloudformation describe-stacks --query "Stacks[?contains(StackName, '${PROJECT_NAME}')].{Name:StackName,Status:StackStatus}" --output table --region $REGION 2>/dev/null || echo "No CloudFormation stacks found")
    echo "$STACKS"
    echo ""
}

show_estimated_time() {
    echo -e "${YELLOW}⏱️  Estimated Deployment Times:${NC}"
    echo "• VPC & Networking: 2-3 minutes"
    echo "• RDS Database: 10-15 minutes (longest step)"
    echo "• ECS Cluster: 3-5 minutes"
    echo "• Load Balancer: 2-3 minutes"
    echo "• Docker Images: 5-10 minutes"
    echo "• Service Deployment: 5-7 minutes"
    echo "• Total Time: 25-40 minutes"
    echo ""
}

monitor_loop() {
    echo -e "${BLUE}🔄 Starting continuous monitoring (Ctrl+C to stop)...${NC}"
    echo ""
    
    while true; do
        clear
        print_header
        show_estimated_time
        check_terraform_progress
        check_aws_resources
        check_ecs_services
        check_deployment_logs
        
        echo -e "${BLUE}Last updated: $(date)${NC}"
        echo -e "${BLUE}Refreshing in 30 seconds... (Ctrl+C to stop)${NC}"
        
        sleep 30
    done
}

# Main execution
case "${3:-monitor}" in
    "once")
        print_header
        check_terraform_progress
        check_aws_resources
        check_ecs_services
        ;;
    "monitor")
        monitor_loop
        ;;
    *)
        echo "Usage: $0 [region] [environment] [once|monitor]"
        exit 1
        ;;
esac
