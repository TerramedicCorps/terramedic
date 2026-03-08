# Network Outputs
output "vpc_id" {
  description = "Prod VPC ID"
  value       = module.networking.vpc_id
}

output "private_subnet_ids" {
  description = "Private app subnet IDs"
  value       = module.networking.private_subnet_ids
}

# VPC Peering
output "peering_connection_id" {
  description = "VPC peering connection ID to shared account"
  value       = module.vpc_peering.peering_connection_id
}

# Database (from shared)
output "database_endpoint" {
  description = "RDS endpoint (from shared account)"
  value       = data.terraform_remote_state.shared.outputs.database_endpoint
}

# Zappa/Lambda
output "zappa_deployment_role_arn" {
  description = "ARN of the Zappa Lambda execution role"
  value       = module.zappa.zappa_deployment_role_arn
}

output "zappa_s3_bucket" {
  description = "S3 bucket for Zappa deployment packages"
  value       = module.zappa.s3_bucket_name
}

output "lambda_security_group_id" {
  description = "Security group ID for Lambda functions"
  value       = module.zappa.lambda_security_group_id
}

# ECR
output "lambda_repository_url" {
  description = "URL of the Lambda ECR repository"
  value       = module.lambda_ecr.lambda_repository_url
}

# Storage
output "static_assets_bucket_name" {
  description = "Name of the static assets S3 bucket"
  value       = module.storage.static_assets_bucket_name
}

output "cloudfront_distribution_domain_name" {
  description = "CloudFront distribution domain"
  value       = module.storage.cloudfront_distribution_domain_name
}

# DNS (API Gateway custom domain is managed by the deploy workflow)

# ACM
output "acm_certificate_arn" {
  description = "ARN of the ACM certificate"
  value       = aws_acm_certificate.main.arn
}

# WAF
output "waf_web_acl_arn" {
  description = "ARN of the WAF Web ACL"
  value       = module.security.waf_web_acl_arn
}

# GitHub OIDC
output "github_oidc_role_arn" {
  description = "ARN of the GitHub Actions role for the prod account"
  value       = module.github_oidc.role_arn
}

# Monitoring
output "budget_info" {
  description = "Budget configuration summary"
  value       = module.monitoring.budget_info
}
