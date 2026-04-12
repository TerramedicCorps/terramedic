variable "prefix" {
  description = "Prefix to use for resource names"
  type        = string
  default     = "terramedic-dev"
}

variable "resource_prefix" {
  description = "Resource prefix for IAM policies"
  type        = string
  default     = "terramedic"
}

variable "aws_region" {
  description = "The AWS region to deploy to"
  type        = string
  default     = "us-east-1"
}

variable "tags" {
  description = "Default tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "terramedic"
    Environment = "dev"
    ManagedBy   = "terraform"
  }
}

# Cross-account references
variable "shared_account_id" {
  description = "AWS account ID of the shared account"
  type        = string
}

variable "shared_peering_role_arn" {
  description = "IAM role ARN in the shared account for VPC peering acceptance"
  type        = string
}

variable "shared_dns_role_arn" {
  description = "IAM role ARN in the shared account for Route53 DNS management"
  type        = string
}

# Networking
variable "vpc_cidr" {
  description = "CIDR block for the dev VPC"
  type        = string
  default     = "10.2.0.0/16"
}

variable "private_subnet_a_cidr" {
  description = "CIDR block for private app subnet A"
  type        = string
  default     = "10.2.3.0/24"
}

variable "private_subnet_b_cidr" {
  description = "CIDR block for private app subnet B"
  type        = string
  default     = "10.2.4.0/24"
}

# Cost control
variable "enable_vpc_endpoints" {
  description = "Enable VPC endpoints (disable to save costs when not actively developing)"
  type        = bool
  default     = true
}

# Database (in shared account, accessed via peering)
variable "db_name" {
  description = "Database name in the shared RDS instance (dev database)"
  type        = string
  default     = "terramedic"
}

variable "app_db_username" {
  description = "Application database username"
  type        = string
}

variable "app_db_password" {
  description = "Application database password"
  type        = string
  sensitive   = true
}

variable "site_password" {
  description = "Password for site access protection"
  type        = string
  default     = ""
  sensitive   = true
}

# Monitoring
variable "alert_email" {
  description = "Email address to receive alerts"
  type        = string
}

variable "budget_limit_amount" {
  description = "Monthly budget limit amount in USD"
  type        = string
  default     = "30"
}

# Domain & DNS
variable "domain_name" {
  description = "The domain name for the application"
  type        = string
}

# Worker schedule
variable "worker_schedule_expression" {
  description = "Schedule expression for the worker Lambda (e.g. 'rate(5 minutes)'). Empty to disable."
  type        = string
  default     = "rate(5 minutes)"
}

# GitHub OIDC
variable "github_repo" {
  description = "GitHub repository in org/repo format"
  type        = string
}
