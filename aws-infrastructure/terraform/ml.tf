# S3 Bucket for ML Models and artifacts
resource "aws_s3_bucket" "ml_artifacts" {
  bucket        = "${local.name_prefix}-ml-artifacts-${random_string.suffix.result}"
  force_destroy = true

  tags = local.common_tags
}

resource "aws_s3_bucket_versioning" "ml_artifacts" {
  bucket = aws_s3_bucket.ml_artifacts.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ml_artifacts" {
  bucket = aws_s3_bucket.ml_artifacts.bucket

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Lambda function for model evaluation
resource "aws_iam_role" "lambda_evaluation" {
  name = "${local.name_prefix}-lambda-evaluation-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_evaluation.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_evaluation_policy" {
  name = "${local.name_prefix}-lambda-evaluation-policy"
  role = aws_iam_role.lambda_evaluation.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.ml_artifacts.arn,
          "${aws_s3_bucket.ml_artifacts.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "rds:DescribeDBInstances"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = aws_secretsmanager_secret.db_password.arn
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData"
        ]
        Resource = "*"
      }
    ]
  })
}

# SageMaker execution role for model training/inference
resource "aws_iam_role" "sagemaker_execution" {
  name = "${local.name_prefix}-sagemaker-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "sagemaker.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "sagemaker_execution_role" {
  role       = aws_iam_role.sagemaker_execution.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

resource "aws_iam_role_policy" "sagemaker_s3_policy" {
  name = "${local.name_prefix}-sagemaker-s3-policy"
  role = aws_iam_role.sagemaker_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.ml_artifacts.arn,
          "${aws_s3_bucket.ml_artifacts.arn}/*"
        ]
      }
    ]
  })
}

# EventBridge rule for scheduled model evaluation
resource "aws_cloudwatch_event_rule" "model_evaluation" {
  count = var.enable_ml_monitoring ? 1 : 0

  name                = "${local.name_prefix}-model-evaluation"
  description         = "Trigger model evaluation weekly"
  schedule_expression = "rate(7 days)"

  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "model_evaluation" {
  count = var.enable_ml_monitoring ? 1 : 0

  rule      = aws_cloudwatch_event_rule.model_evaluation[0].name
  target_id = "ModelEvaluationTarget"
  arn       = aws_lambda_function.model_evaluation[0].arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  count = var.enable_ml_monitoring ? 1 : 0

  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.model_evaluation[0].function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.model_evaluation[0].arn
}

# Lambda function for model evaluation (placeholder - will need actual code)
resource "aws_lambda_function" "model_evaluation" {
  count = var.enable_ml_monitoring ? 1 : 0

  filename         = "model_evaluation.zip"
  function_name    = "${local.name_prefix}-model-evaluation"
  role            = aws_iam_role.lambda_evaluation.arn
  handler         = "index.handler"
  runtime         = "python3.11"
  timeout         = 300

  environment {
    variables = {
      S3_BUCKET      = aws_s3_bucket.ml_artifacts.bucket
      DB_SECRET_ARN  = aws_secretsmanager_secret.db_password.arn
      ENVIRONMENT    = var.environment
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,
  ]

  tags = local.common_tags
}

# Create a placeholder zip file for the Lambda function
data "archive_file" "model_evaluation_zip" {
  count = var.enable_ml_monitoring ? 1 : 0

  type        = "zip"
  output_path = "model_evaluation.zip"
  source {
    content = <<EOF
import json
import boto3
import os

def handler(event, context):
    """
    Lambda function for ML model evaluation
    This is a placeholder - implement actual evaluation logic
    """
    
    print("Starting model evaluation...")
    
    # Initialize AWS clients
    s3 = boto3.client('s3')
    cloudwatch = boto3.client('cloudwatch')
    
    # Put sample metrics
    cloudwatch.put_metric_data(
        Namespace='HotelReview/ML',
        MetricData=[
            {
                'MetricName': 'ModelAccuracy',
                'Value': 0.92,
                'Unit': 'Percent'
            },
            {
                'MetricName': 'EvaluationCompleted',
                'Value': 1.0,
                'Unit': 'Count'
            }
        ]
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps('Model evaluation completed successfully')
    }
EOF
    filename = "index.py"
  }
}
