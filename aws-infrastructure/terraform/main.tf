# AWS Infrastructure for Hotel Review NLP Application
# Complete production-ready setup with VPC, ECS, RDS, Lambda, and monitoring

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Environment = var.environment
      Project     = "hotel-review-nlp"
      Owner       = "team"
      Terraform   = "true"
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# Local variables
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  azs         = slice(data.aws_availability_zones.available.names, 0, 2)
  
  # Common tags
  common_tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}
