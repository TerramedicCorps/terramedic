# GitHub OIDC Module
# Creates an IAM OIDC provider for GitHub Actions and an IAM role
# that GitHub Actions workflows can assume via OIDC federation.

terraform {
  required_version = ">= 1.12.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.99.0"
    }
  }
}

data "aws_caller_identity" "current" {}

# GitHub OIDC Provider
# Only one provider per account is needed (GitHub's thumbprint is stable)
resource "aws_iam_openid_connect_provider" "github" {
  count = var.create_oidc_provider ? 1 : 0

  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["ffffffffffffffffffffffffffffffffffffffff"]

  tags = {
    Name = "github-actions-oidc"
  }
}

locals {
  oidc_provider_arn = var.create_oidc_provider ? aws_iam_openid_connect_provider.github[0].arn : var.existing_oidc_provider_arn
}

# IAM Role for GitHub Actions
resource "aws_iam_role" "github_actions" {
  name = "github-actions-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = local.oidc_provider_arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = var.github_subjects
          }
        }
      }
    ]
  })

  tags = {
    Name        = "github-actions-${var.environment}"
    Environment = var.environment
  }
}

# Attach managed policies to the role
resource "aws_iam_role_policy_attachment" "github_actions" {
  count = length(var.policy_arns)

  role       = aws_iam_role.github_actions.name
  policy_arn = var.policy_arns[count.index]
}

# Inline policy for Terraform operations (S3 state, DynamoDB locks)
resource "aws_iam_role_policy" "terraform_operations" {
  count = var.enable_terraform_policy ? 1 : 0

  name = "${var.environment}-terraform-operations"
  role = aws_iam_role.github_actions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "TerraformStateAccess"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::terramedic-terraform-state-*",
          "arn:aws:s3:::terramedic-terraform-state-*/*"
        ]
      },
      {
        Sid    = "TerraformLockAccess"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:DeleteItem",
          "dynamodb:CreateTable",
          "dynamodb:DescribeTable",
          "dynamodb:TagResource"
        ]
        Resource = "arn:aws:dynamodb:${var.aws_region}:${data.aws_caller_identity.current.account_id}:table/terramedic-terraform-locks"
      }
    ]
  })
}

# Inline policy for infrastructure management (Terraform plan/apply)
resource "aws_iam_role_policy" "infrastructure" {
  count = var.enable_infrastructure_policy ? 1 : 0

  name = "${var.environment}-infrastructure"
  role = aws_iam_role.github_actions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat(
      [
        # --- Read-only across all services (some list/describe actions require Resource: *) ---
        {
          Sid    = "ServiceReadOnly"
          Effect = "Allow"
          Action = [
            "ec2:Describe*",
            "ec2:Get*",
            "ec2:List*",
            "cloudfront:Get*",
            "cloudfront:List*",
            "wafv2:Describe*",
            "wafv2:Get*",
            "wafv2:List*",
            "ses:Describe*",
            "ses:Get*",
            "ses:List*",
            "acm:Describe*",
            "acm:Get*",
            "acm:List*",
            "kms:Describe*",
            "kms:Get*",
            "kms:List*",
            "budgets:Describe*",
            "budgets:View*",
            "ecr:GetAuthorizationToken",
          ]
          Resource = "*"
        },

        # --- S3: read-only at * (list/describe need it), mutate scoped to project buckets ---
        {
          Sid      = "S3ReadOnly"
          Effect   = "Allow"
          Action   = ["s3:Get*", "s3:List*", "s3:HeadBucket", "s3:HeadObject"]
          Resource = "*"
        },
        {
          Sid    = "S3Mutate"
          Effect = "Allow"
          Action = [
            "s3:PutObject",
            "s3:DeleteObject",
            "s3:CreateBucket",
            "s3:DeleteBucket",
            "s3:PutBucketPolicy",
            "s3:DeleteBucketPolicy",
            "s3:PutBucketVersioning",
            "s3:PutBucketEncryption",
            "s3:PutBucketPublicAccessBlock",
            "s3:PutBucketLifecycleConfiguration",
            "s3:PutBucketTagging",
            "s3:PutBucketCORS",
            "s3:PutBucketNotification",
            "s3:PutBucketLogging",
            "s3:PutBucketWebsite",
            "s3:DeleteBucketWebsite",
            "s3:PutObjectAcl",
            "s3:PutBucketAcl",
          ]
          Resource = [
            "arn:aws:s3:::${var.resource_prefix}-*",
            "arn:aws:s3:::${var.resource_prefix}-*/*",
            "arn:aws:s3:::terramedic-terraform-state-*",
            "arn:aws:s3:::terramedic-terraform-state-*/*",
          ]
        },
        {
          Sid    = "Route53"
          Effect = "Allow"
          Action = [
            "route53:GetHostedZone",
            "route53:ListHostedZones",
            "route53:ListHostedZonesByName",
            "route53:GetHostedZoneCount",
            "route53:ChangeResourceRecordSets",
            "route53:GetChange",
            "route53:ListResourceRecordSets",
            "route53:ListTagsForResource",
            "route53:ChangeTagsForResource",
            "route53:CreateHostedZone",
            "route53:GetDNSSEC",
            "route53:ListTagsForResources",
          ]
          Resource = "*"
        },
        {
          Sid      = "APIGateway"
          Effect   = "Allow"
          Action   = ["apigateway:*"]
          Resource = "*"
        },
        {
          Sid      = "CostExplorer"
          Effect   = "Allow"
          Action   = ["ce:*"]
          Resource = "*"
        },

        # --- IAM read-only (safe at *) ---
        {
          Sid    = "IAMReadOnly"
          Effect = "Allow"
          Action = [
            "iam:GetRole",
            "iam:GetRolePolicy",
            "iam:GetPolicy",
            "iam:GetPolicyVersion",
            "iam:GetInstanceProfile",
            "iam:GetOpenIDConnectProvider",
            "iam:GetUser",
            "iam:GetUserPolicy",
            "iam:ListRolePolicies",
            "iam:ListAttachedRolePolicies",
            "iam:ListInstanceProfilesForRole",
            "iam:ListPolicyVersions",
            "iam:ListRoleTags",
            "iam:ListUserPolicies",
            "iam:ListUserTags",
            "iam:ListAccessKeys",
          ]
          Resource = "*"
        },

        # --- IAM mutate (scoped to prefix and OIDC provider) ---
        {
          Sid    = "IAMMutate"
          Effect = "Allow"
          Action = [
            "iam:CreateRole",
            "iam:DeleteRole",
            "iam:UpdateRole",
            "iam:TagRole",
            "iam:UntagRole",
            "iam:PutRolePolicy",
            "iam:DeleteRolePolicy",
            "iam:AttachRolePolicy",
            "iam:DetachRolePolicy",
            "iam:PassRole",
            "iam:CreatePolicy",
            "iam:DeletePolicy",
            "iam:CreatePolicyVersion",
            "iam:DeletePolicyVersion",
            "iam:CreateInstanceProfile",
            "iam:DeleteInstanceProfile",
            "iam:AddRoleToInstanceProfile",
            "iam:RemoveRoleFromInstanceProfile",
            "iam:CreateServiceLinkedRole",
            "iam:CreateUser",
            "iam:DeleteUser",
            "iam:TagUser",
            "iam:UntagUser",
            "iam:PutUserPolicy",
            "iam:DeleteUserPolicy",
            "iam:CreateAccessKey",
            "iam:DeleteAccessKey",
          ]
          Resource = [
            "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.resource_prefix}-*",
            "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/github-actions-*",
            "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/${var.resource_prefix}-*",
            "arn:aws:iam::${data.aws_caller_identity.current.account_id}:instance-profile/${var.resource_prefix}-*",
            "arn:aws:iam::${data.aws_caller_identity.current.account_id}:user/ses/${var.resource_prefix}-*",
          ]
        },

        # --- OIDC provider management (scoped to single GitHub provider) ---
        {
          Sid    = "OIDCProviderMutate"
          Effect = "Allow"
          Action = [
            "iam:DeleteOpenIDConnectProvider",
            "iam:TagOpenIDConnectProvider",
            "iam:UpdateOpenIDConnectProviderThumbprint",
            "iam:AddClientIDToOpenIDConnectProvider",
          ]
          Resource = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/token.actions.githubusercontent.com"
        },

        # --- CloudFormation Cloud Control API (required by awscc provider) ---
        {
          Sid    = "CloudControlAPI"
          Effect = "Allow"
          Action = [
            "cloudformation:GetResource",
            "cloudformation:CreateResource",
            "cloudformation:UpdateResource",
            "cloudformation:DeleteResource",
            "cloudformation:ListResources",
          ]
          Resource = "*"
        },

        # --- Account-scoped services (regional) ---
        {
          Sid      = "EC2ReadOnly"
          Effect   = "Allow"
          Action   = ["ec2:Describe*", "ec2:Get*", "ec2:List*"]
          Resource = "*"
        },
        {
          Sid      = "EC2Mutate"
          Effect   = "Allow"
          Action   = ["ec2:*"]
          Resource = "arn:aws:ec2:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*"
        },
        {
          Sid      = "RDS"
          Effect   = "Allow"
          Action   = ["rds:*"]
          Resource = "arn:aws:rds:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*"
        },
        {
          Sid      = "Lambda"
          Effect   = "Allow"
          Action   = ["lambda:*"]
          Resource = "arn:aws:lambda:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*"
        },
        {
          Sid      = "ECR"
          Effect   = "Allow"
          Action   = ["ecr:*"]
          Resource = "arn:aws:ecr:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*"
        },
        {
          Sid      = "SecretsManager"
          Effect   = "Allow"
          Action   = ["secretsmanager:*"]
          Resource = "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*"
        },
        {
          Sid      = "SSM"
          Effect   = "Allow"
          Action   = ["ssm:*"]
          Resource = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*"
        },
        {
          Sid      = "SNS"
          Effect   = "Allow"
          Action   = ["sns:*"]
          Resource = "arn:aws:sns:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*"
        },
        {
          Sid    = "CloudWatch"
          Effect = "Allow"
          Action = ["cloudwatch:*", "logs:*"]
          Resource = [
            "arn:aws:cloudwatch:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*",
            "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*",
          ]
        },
        {
          Sid    = "EventBridgeRead"
          Effect = "Allow"
          Action = [
            "events:DescribeRule",
            "events:ListRules",
            "events:ListRuleNamesByTarget",
            "events:ListTargetsByRule",
            "events:ListTagsForResource",
          ]
          Resource = "*"
        },
        {
          Sid    = "EventBridgeWrite"
          Effect = "Allow"
          Action = [
            "events:PutRule",
            "events:PutTargets",
            "events:DeleteRule",
            "events:RemoveTargets",
            "events:TagResource",
            "events:UntagResource",
          ]
          Resource = "arn:aws:events:${var.aws_region}:${data.aws_caller_identity.current.account_id}:rule/*"
        },
        {
          Sid      = "WAF"
          Effect   = "Allow"
          Action   = ["wafv2:*"]
          Resource = "arn:aws:wafv2:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*"
        },
        {
          Sid      = "SES"
          Effect   = "Allow"
          Action   = ["ses:*"]
          Resource = "arn:aws:ses:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*"
        },
        {
          Sid      = "ACM"
          Effect   = "Allow"
          Action   = ["acm:*"]
          Resource = "arn:aws:acm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*"
        },
        {
          Sid      = "KMS"
          Effect   = "Allow"
          Action   = ["kms:*"]
          Resource = "arn:aws:kms:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*"
        },

        # --- Account-scoped services (global, no region) ---
        {
          Sid      = "CloudFront"
          Effect   = "Allow"
          Action   = ["cloudfront:*"]
          Resource = "arn:aws:cloudfront::${data.aws_caller_identity.current.account_id}:*"
        },
        {
          Sid      = "Budgets"
          Effect   = "Allow"
          Action   = ["budgets:*"]
          Resource = "arn:aws:budgets::${data.aws_caller_identity.current.account_id}:*"
        },
      ],

      # --- STS: only if peering_account_ids is non-empty ---
      length(var.peering_account_ids) > 0 ? [
        {
          Sid    = "STS"
          Effect = "Allow"
          Action = ["sts:AssumeRole"]
          Resource = [
            for account_id in var.peering_account_ids :
            "arn:aws:iam::${account_id}:role/vpc-peering-accepter"
          ]
        },
      ] : [],
    )
  })
}
