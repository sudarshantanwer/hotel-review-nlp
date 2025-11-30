#!/bin/bash

# Quick Setup Script for AWS Deployment
# This script installs prerequisites and guides through AWS configuration

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}=== Hotel Review NLP - AWS Deployment Setup ===${NC}"
echo ""

# Check OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected macOS"
    PACKAGE_MANAGER="brew"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Detected Linux"
    if command -v apt-get &> /dev/null; then
        PACKAGE_MANAGER="apt"
    elif command -v yum &> /dev/null; then
        PACKAGE_MANAGER="yum"
    else
        echo -e "${RED}Unsupported Linux distribution${NC}"
        exit 1
    fi
else
    echo -e "${RED}Unsupported operating system${NC}"
    exit 1
fi

# Function to install tools
install_tools() {
    echo -e "${YELLOW}Installing required tools...${NC}"
    
    if [[ "$PACKAGE_MANAGER" == "brew" ]]; then
        # Check if Homebrew is installed
        if ! command -v brew &> /dev/null; then
            echo "Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        
        echo "Installing AWS CLI..."
        brew install awscli
        
        echo "Installing Terraform..."
        brew install terraform
        
        echo "Installing jq..."
        brew install jq
        
    elif [[ "$PACKAGE_MANAGER" == "apt" ]]; then
        sudo apt-get update
        
        echo "Installing AWS CLI..."
        curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
        unzip awscliv2.zip
        sudo ./aws/install
        rm -rf aws awscliv2.zip
        
        echo "Installing Terraform..."
        wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg
        echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
        sudo apt-get update && sudo apt-get install terraform
        
        echo "Installing jq..."
        sudo apt-get install jq
    fi
}

# Check if tools are already installed
check_tools() {
    echo -e "${YELLOW}Checking installed tools...${NC}"
    
    MISSING_TOOLS=()
    
    if ! command -v aws &> /dev/null; then
        MISSING_TOOLS+=("AWS CLI")
    fi
    
    if ! command -v terraform &> /dev/null; then
        MISSING_TOOLS+=("Terraform")
    fi
    
    if ! command -v docker &> /dev/null; then
        MISSING_TOOLS+=("Docker")
    fi
    
    if ! command -v jq &> /dev/null; then
        MISSING_TOOLS+=("jq")
    fi
    
    if [ ${#MISSING_TOOLS[@]} -eq 0 ]; then
        echo -e "${GREEN}All tools are already installed!${NC}"
        return 0
    else
        echo -e "${YELLOW}Missing tools: ${MISSING_TOOLS[*]}${NC}"
        return 1
    fi
}

# Configure AWS
configure_aws() {
    echo -e "${YELLOW}Configuring AWS...${NC}"
    echo ""
    echo "You'll need your AWS credentials:"
    echo "1. AWS Access Key ID"
    echo "2. AWS Secret Access Key"
    echo "3. Default region (e.g., us-east-1)"
    echo "4. Output format (recommend: json)"
    echo ""
    read -p "Press Enter to continue with AWS configuration..."
    aws configure
}

# Main execution
main() {
    if check_tools; then
        echo -e "${GREEN}Prerequisites are ready!${NC}"
    else
        read -p "Install missing tools? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            install_tools
        else
            echo -e "${RED}Please install missing tools manually and run this script again.${NC}"
            exit 1
        fi
    fi
    
    # Check AWS configuration
    if aws sts get-caller-identity &> /dev/null; then
        echo -e "${GREEN}AWS is already configured!${NC}"
        aws sts get-caller-identity
    else
        echo -e "${YELLOW}AWS needs to be configured${NC}"
        configure_aws
    fi
    
    echo ""
    echo -e "${GREEN}=== Setup Complete! ===${NC}"
    echo ""
    echo "You can now run the deployment script:"
    echo -e "${YELLOW}./scripts/deploy.sh${NC}"
    echo ""
    echo "Available options:"
    echo "  ./scripts/deploy.sh                    # Deploy to prod in us-east-1"
    echo "  ./scripts/deploy.sh staging            # Deploy to staging in us-east-1"
    echo "  ./scripts/deploy.sh prod us-west-2     # Deploy to prod in us-west-2"
}

main "$@"
