# SSM Parameter Store Module for Simple Values
# Uses free SSM parameters for simple string values
# Complex JSON objects remain in Secrets Manager

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

# Django Secret Key Parameter (simple string)
resource "aws_ssm_parameter" "secret_key" {
  name        = "/${var.prefix}/secret-key"
  description = "Django secret key for the application"
  type        = "SecureString"
  tier        = "Standard" # Free tier (< 4KB)

  value = var.django_secret_key != "" ? var.django_secret_key : "dummy-value-to-be-changed"

  tags = merge(
    var.tags,
    {
      Name = "${var.prefix}-secret-key"
    }
  )

  lifecycle {
    ignore_changes = [value]
  }
}

# Site Password Parameter (simple string)
resource "aws_ssm_parameter" "site_password" {
  name        = "/${var.prefix}/site-password"
  description = "Site password for access protection"
  type        = "SecureString"
  tier        = "Standard" # Free tier (< 4KB)

  value = var.site_password != "" ? var.site_password : "changeme"

  tags = merge(
    var.tags,
    {
      Name = "${var.prefix}-site-password"
    }
  )

  lifecycle {
    ignore_changes = [value]
  }
}

# Database URL Parameters - one per environment
# Using same RDS instance but different databases
resource "aws_ssm_parameter" "db_url" {
  for_each = var.environments

  name        = "/${var.prefix}/${each.key}/database-url"
  description = "PostgreSQL database connection URL for ${each.key} environment"
  type        = "SecureString"
  tier        = "Standard" # Free tier (< 4KB)

  # Connection string with environment-specific database name
  value = "postgis://${var.app_db_username}:${var.app_db_password}@${var.db_endpoint}/${var.db_name_prefix}_${each.key}"

  tags = merge(
    var.tags,
    {
      Name        = "${var.prefix}-${each.key}-db-url"
      Environment = each.key
    }
  )

  lifecycle {
    ignore_changes = [value]
  }
}

# IAM policy for reading SSM parameters
resource "aws_iam_policy" "ssm_read" {
  name        = "${var.prefix}-ssm-read"
  description = "Policy to read SSM parameters for ${var.prefix}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParameterHistory",
          "ssm:DescribeParameters"
        ]
        Resource = concat(
          [for env, param in aws_ssm_parameter.db_url : param.arn],
          [
            aws_ssm_parameter.secret_key.arn,
            aws_ssm_parameter.site_password.arn
          ]
        )
      },
      {
        # Allow KMS decrypt for SecureString parameters
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey"
        ]
        Resource = "*" # Uses AWS managed keys
      }
    ]
  })

  tags = var.tags
}
