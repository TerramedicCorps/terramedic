variable "prefix" {
  description = "Prefix to use for resource names"
  type        = string
  default     = "terramedic-shared"
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
    Environment = "shared"
    ManagedBy   = "terraform"
  }
}

# Networking
variable "vpc_cidr" {
  description = "CIDR block for the shared VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_a_cidr" {
  description = "CIDR block for public subnet A"
  type        = string
  default     = "10.0.1.0/24"
}

variable "public_subnet_b_cidr" {
  description = "CIDR block for public subnet B"
  type        = string
  default     = "10.0.2.0/24"
}

variable "private_db_subnet_a_cidr" {
  description = "CIDR block for private DB subnet A"
  type        = string
  default     = "10.0.5.0/24"
}

variable "private_db_subnet_b_cidr" {
  description = "CIDR block for private DB subnet B"
  type        = string
  default     = "10.0.6.0/24"
}

# Cross-account Lambda access
variable "allowed_lambda_cidrs" {
  description = "CIDR blocks of Lambda subnets in prod and dev accounts that need DB access"
  type        = list(string)
  default     = []
}

# Database
variable "db_name" {
  description = "Database name"
  type        = string
  default     = "terramedic"
}

variable "db_username" {
  description = "Database master username"
  type        = string
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
}

variable "app_db_username" {
  description = "Application database username"
  type        = string
}

variable "db_allocated_storage" {
  description = "Allocated storage for the database in GB"
  type        = number
  default     = 20
}

variable "db_engine_version" {
  description = "Version of PostgreSQL to use"
  type        = string
  default     = "16.9"
}

variable "db_instance_class" {
  description = "Instance class for the database"
  type        = string
  default     = "db.t4g.micro"
}

variable "auto_setup_database" {
  description = "Whether to automatically run database setup after RDS creation"
  type        = bool
  default     = false
}

variable "prevent_destroy" {
  description = "Whether to prevent destruction of database resources"
  type        = bool
  default     = true
}

# Bastion
variable "allowed_bastion_cidrs" {
  description = "List of CIDR blocks allowed to access the bastion host"
  type        = list(string)
}

variable "bastion_key_name" {
  description = "SSH key pair name for the bastion host"
  type        = string
}

variable "bastion_public_key" {
  description = "SSH public key for the bastion host"
  type        = string
  default     = ""
  sensitive   = true
}

variable "create_new_key_pair" {
  description = "Whether to create a new key pair"
  type        = bool
  default     = false
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

# GitHub OIDC
variable "github_repo" {
  description = "GitHub repository in org/repo format"
  type        = string
}
