variable "environment" {
  description = "Environment name (e.g., shared, prod, dev)"
  type        = string
}

variable "aws_region" {
  description = "AWS region for scoping resource ARNs"
  type        = string
  default     = "us-east-1"
}

variable "create_oidc_provider" {
  description = "Whether to create the OIDC provider (only needed once per account)"
  type        = bool
  default     = true
}

variable "existing_oidc_provider_arn" {
  description = "ARN of an existing OIDC provider (used when create_oidc_provider is false)"
  type        = string
  default     = ""

  validation {
    condition     = var.existing_oidc_provider_arn != "" || var.create_oidc_provider
    error_message = "existing_oidc_provider_arn must be set when create_oidc_provider is false."
  }
}

variable "github_subjects" {
  description = "List of GitHub OIDC subject claims to allow (e.g., repo:org/repo:environment:prod)"
  type        = list(string)
}

variable "policy_arns" {
  description = "List of IAM policy ARNs to attach to the GitHub Actions role"
  type        = list(string)
  default     = []
}

variable "enable_terraform_policy" {
  description = "Whether to attach the inline Terraform state/lock policy"
  type        = bool
  default     = true
}

variable "enable_infrastructure_policy" {
  description = "Whether to attach the inline infrastructure management policy for Terraform CI/CD"
  type        = bool
  default     = false
}

variable "peering_account_ids" {
  description = "Account IDs for STS AssumeRole (VPC peering). Empty = no STS."
  type        = list(string)
  default     = []
}

variable "cross_account_role_arns" {
  description = "Additional cross-account IAM role ARNs to allow assuming (e.g., dns-manager)"
  type        = list(string)
  default     = []
}

variable "resource_prefix" {
  description = "Prefix for IAM resource ARN scoping"
  type        = string
  default     = "terramedic"
}
