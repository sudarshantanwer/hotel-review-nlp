#!/bin/bash

# Quick Deployment Status Check
# Shows current status of AWS deployment

REGION=${1:-ap-south-1}
PROJECT_NAME="hotel-review-nlp"
ENVIRONMENT=${2:-prod}
NAME_PREFIX="${PROJECT_NAME}-${ENVIRONMENT}"

echo "🇮🇳 Hotel Review NLP - Mumbai Deployment Status"
echo "=============================================="
echo ""

# Quick health check
echo "🏥 DEPLOYMENT HEALTH:"

# Check if any resources exist
VPC_EXISTS=$(aws ec2 describe-vpcs --filters "Name=tag:Name,Values=${NAME_PREFIX}-vpc" --region $REGION --query "length(Vpcs)" --output text 2>/dev/null || echo "0")
RDS_EXISTS=$(aws rds describe-db-instances --db-instance-identifier "${NAME_PREFIX}-postgres" --region $REGION >/dev/null 2>&1 && echo "1" || echo "0")
ECS_EXISTS=$(aws ecs describe-clusters --clusters "${NAME_PREFIX}-cluster" --region $REGION >/dev/null 2>&1 && echo "1" || echo "0")

if [ "$VPC_EXISTS" = "1" ] || [ "$RDS_EXISTS" = "1" ] || [ "$ECS_EXISTS" = "1" ]; then
    echo "✅ Deployment in progress or completed"
    
    # Check application URL
    ALB_DNS=$(aws elbv2 describe-load-balancers --names "${NAME_PREFIX}-alb" --query "LoadBalancers[0].DNSName" --output text --region $REGION 2>/dev/null || echo "")
    if [ "$ALB_DNS" != "" ] && [ "$ALB_DNS" != "None" ]; then
        echo "🌐 Your app will be available at: http://$ALB_DNS"
        echo ""
        echo "🧪 Testing application health..."
        if curl -s --connect-timeout 5 "http://$ALB_DNS/health" >/dev/null 2>&1; then
            echo "✅ Application is healthy and responding!"
        else
            echo "⏳ Application is still starting up..."
        fi
    else
        echo "⏳ Load balancer not ready yet"
    fi
else
    echo "🆕 No deployment detected - ready to deploy!"
fi

echo ""
echo "📊 Want continuous monitoring? Run:"
echo "   ./scripts/monitor-deployment.sh"
echo ""
echo "🚀 Ready to deploy? Run:"
echo "   ./scripts/deploy.sh prod ap-south-1"
