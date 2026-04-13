data "aws_caller_identity" "current" {}

# S3 bucket for Zappa deployments
resource "aws_s3_bucket" "zappa_deployments" {
  bucket = "${var.prefix}-zappa-deployments"

  tags = merge(
    var.tags,
    {
      Name    = "${var.prefix}-zappa-deployments"
      Purpose = "Zappa Lambda deployment packages"
    }
  )
}

# Enable versioning for rollback capability
resource "aws_s3_bucket_versioning" "zappa_deployments" {
  bucket = aws_s3_bucket.zappa_deployments.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "zappa_deployments" {
  bucket = aws_s3_bucket.zappa_deployments.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "zappa_deployments" {
  bucket = aws_s3_bucket.zappa_deployments.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle policy to clean up old deployments
resource "aws_s3_bucket_lifecycle_configuration" "zappa_deployments" {
  bucket = aws_s3_bucket.zappa_deployments.id

  rule {
    id     = "delete-old-deployments"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days = 30 # Keep old versions for 30 days
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# Security group for Lambda functions (only if VPC ID is provided)
resource "aws_security_group" "lambda" {
  count = var.create_lambda_sg ? 1 : 0

  name        = "${var.prefix}-lambda"
  description = "Security group for Lambda functions"
  vpc_id      = var.vpc_id

  # Allow outbound traffic to RDS (only if database CIDRs are provided)
  dynamic "egress" {
    for_each = length(var.database_subnet_cidrs) > 0 ? [1] : []
    content {
      from_port   = 5432
      to_port     = 5432
      protocol    = "tcp"
      cidr_blocks = var.database_subnet_cidrs
    }
  }

  # Allow outbound HTTPS for AWS services
  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow outbound HTTP for external APIs
  egress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow DNS
  egress {
    from_port   = 53
    to_port     = 53
    protocol    = "udp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.prefix}-lambda"
    }
  )
}

# IAM role for Zappa deployment
resource "aws_iam_role" "zappa_deployment" {
  name = "${var.prefix}-zappa-deployment"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = [
            "lambda.amazonaws.com",
            "events.amazonaws.com",
            "apigateway.amazonaws.com"
          ]
        }
      }
    ]
  })

  tags = var.tags
}

# IAM policy for Zappa deployment operations
resource "aws_iam_policy" "zappa_deployment" {
  name        = "${var.prefix}-zappa-deployment"
  description = "Policy for Zappa to deploy Lambda functions"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:CreateFunction",
          "lambda:UpdateFunctionCode",
          "lambda:UpdateFunctionConfiguration",
          "lambda:GetFunction",
          "lambda:GetFunctionConfiguration",
          "lambda:DeleteFunction",
          "lambda:AddPermission",
          "lambda:RemovePermission",
          "lambda:InvokeFunction",
          "lambda:GetPolicy",
          "lambda:PutFunctionConcurrency",
          "lambda:DeleteFunctionConcurrency",
          "lambda:PublishVersion",
          "lambda:CreateAlias",
          "lambda:UpdateAlias",
          "lambda:DeleteAlias",
          "lambda:GetAlias",
          "lambda:ListVersionsByFunction"
        ]
        Resource = concat(
          ["arn:aws:lambda:${var.aws_region}:*:function:${var.prefix}-*"],
          var.project_name != "" ? ["arn:aws:lambda:${var.aws_region}:*:function:${var.project_name}-*"] : []
        )
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = aws_s3_bucket.zappa_deployments.arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.zappa_deployments.arn}/*"
      },
      {
        # Zappa needs these API Gateway actions to manage REST APIs
        Effect = "Allow"
        Action = [
          "apigateway:GET",
          "apigateway:POST",
          "apigateway:PUT",
          "apigateway:DELETE",
          "apigateway:PATCH"
        ]
        Resource = "arn:aws:apigateway:${var.aws_region}::/*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "events:PutRule",
          "events:PutTargets",
          "events:RemoveTargets",
          "events:DeleteRule",
          "events:DescribeRule"
        ]
        Resource = concat(
          ["arn:aws:events:${var.aws_region}:*:rule/${var.prefix}-*"],
          var.project_name != "" ? ["arn:aws:events:${var.aws_region}:*:rule/${var.project_name}-*"] : []
        )
      },
      {
        Effect = "Allow"
        Action = [
          "iam:GetRole",
          "iam:PassRole"
        ]
        Resource = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.prefix}-*"
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:GetQueueUrl"
        ]
        Resource = "arn:aws:sqs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:${var.prefix}-evaluation-*"
      }
    ]
  })
}

# IAM policy for Lambda to read secrets at runtime
resource "aws_iam_policy" "lambda_secrets" {
  count = length(var.secret_arns) > 0 ? 1 : 0

  name        = "${var.prefix}-lambda-secrets"
  description = "Allow Lambda to read Secrets Manager secrets"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat(
      [
        {
          Effect   = "Allow"
          Action   = "secretsmanager:GetSecretValue"
          Resource = var.secret_arns
        }
      ],
      var.secrets_kms_key_arn != "" ? [
        {
          Effect   = "Allow"
          Action   = "kms:Decrypt"
          Resource = var.secrets_kms_key_arn
          Condition = {
            StringEquals = {
              "kms:ViaService" = "secretsmanager.${var.aws_region}.amazonaws.com"
            }
          }
        }
      ] : []
    )
  })
}

resource "aws_iam_role_policy_attachment" "lambda_secrets" {
  count = length(var.secret_arns) > 0 ? 1 : 0

  role       = aws_iam_role.zappa_deployment.name
  policy_arn = aws_iam_policy.lambda_secrets[0].arn
}

# Attach the policy to the role
resource "aws_iam_role_policy_attachment" "zappa_deployment" {
  role       = aws_iam_role.zappa_deployment.name
  policy_arn = aws_iam_policy.zappa_deployment.arn
}

# AWS managed policy for Lambda VPC access (ENI permissions)
resource "aws_iam_role_policy_attachment" "lambda_vpc_access" {
  count = var.create_lambda_sg ? 1 : 0

  role       = aws_iam_role.zappa_deployment.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

locals {
  worker_function_name    = "${var.prefix}-worker"
  evaluator_function_name = "${var.prefix}-evaluator"
}

# EventBridge scheduled rule to trigger the worker Lambda
resource "aws_cloudwatch_event_rule" "worker_schedule" {
  count = var.worker_schedule_expression != "" ? 1 : 0

  name                = "${var.prefix}-worker-schedule"
  description         = "Triggers the evaluation worker Lambda on a schedule"
  schedule_expression = var.worker_schedule_expression

  tags = var.tags
}

resource "aws_cloudwatch_event_target" "worker_lambda" {
  count = var.worker_schedule_expression != "" ? 1 : 0

  rule      = aws_cloudwatch_event_rule.worker_schedule[0].name
  target_id = local.worker_function_name
  arn       = "arn:aws:lambda:${var.aws_region}:${data.aws_caller_identity.current.account_id}:function:${local.worker_function_name}"

  input = jsonencode({
    command = "terramedic.nominations.worker.process_evaluation_queue"
    limit   = 50
  })
}

resource "aws_lambda_permission" "eventbridge_worker" {
  count = var.worker_schedule_expression != "" ? 1 : 0

  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = local.worker_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.worker_schedule[0].arn
}

# ── SQS queues for worker ↔ evaluator communication ─────────────

resource "aws_sqs_queue" "evaluation_requests_dlq" {
  count = var.worker_schedule_expression != "" ? 1 : 0

  name                      = "${var.prefix}-evaluation-requests-dlq"
  message_retention_seconds = 604800 # 7 days
  tags                      = var.tags
}

resource "aws_sqs_queue" "evaluation_requests" {
  count = var.worker_schedule_expression != "" ? 1 : 0

  name                       = "${var.prefix}-evaluation-requests"
  visibility_timeout_seconds = 360 # > evaluator Lambda timeout (300s)
  message_retention_seconds  = 86400
  tags                       = var.tags

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.evaluation_requests_dlq[0].arn
    maxReceiveCount     = 2
  })
}

resource "aws_sqs_queue" "evaluation_results_dlq" {
  count = var.worker_schedule_expression != "" ? 1 : 0

  name                      = "${var.prefix}-evaluation-results-dlq"
  message_retention_seconds = 604800 # 7 days
  tags                      = var.tags
}

resource "aws_sqs_queue" "evaluation_results" {
  count = var.worker_schedule_expression != "" ? 1 : 0

  name                       = "${var.prefix}-evaluation-results"
  visibility_timeout_seconds = 60
  message_retention_seconds  = 86400
  tags                       = var.tags

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.evaluation_results_dlq[0].arn
    maxReceiveCount     = 3
  })
}

# SQS → Lambda event source mappings
resource "aws_lambda_event_source_mapping" "evaluator_sqs_trigger" {
  count = var.worker_schedule_expression != "" ? 1 : 0

  event_source_arn = aws_sqs_queue.evaluation_requests[0].arn
  function_name    = "arn:aws:lambda:${var.aws_region}:${data.aws_caller_identity.current.account_id}:function:${local.evaluator_function_name}"
  batch_size       = 1 # One evaluation at a time (each takes ~30s)
  enabled          = true
}

resource "aws_lambda_event_source_mapping" "worker_results_sqs_trigger" {
  count = var.worker_schedule_expression != "" ? 1 : 0

  event_source_arn = aws_sqs_queue.evaluation_results[0].arn
  function_name    = "arn:aws:lambda:${var.aws_region}:${data.aws_caller_identity.current.account_id}:function:${local.worker_function_name}"
  batch_size       = 10
  enabled          = true
}
