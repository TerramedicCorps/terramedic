variable "prefix" {
  description = "Prefix to use for resource names"
  type        = string
  default     = "terramedic"
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "allowed_bastion_cidrs" {
  description = "List of CIDR blocks allowed to access the bastion host"
  type        = list(string)
  default     = []
}

variable "lambda_security_group_id" {
  description = "ID of the Lambda security group (from the Zappa module). Used for same-account SG-based ingress."
  type        = string
  default     = ""
}

variable "enable_lambda_sg_rules" {
  description = "Whether to create SG rules for Lambda access to database. Use this instead of checking lambda_security_group_id, which may be unknown at plan time."
  type        = bool
  default     = false
}

variable "allowed_lambda_cidrs" {
  description = "CIDR blocks allowed to access the database (for cross-account access where SG references don't work)"
  type        = list(string)
  default     = []
}

variable "create_db_sg" {
  description = "Whether to create the database security group (only needed in shared account)"
  type        = bool
  default     = true
}

variable "create_waf" {
  description = "Whether to create the WAF Web ACL (set to false for dev environments)"
  type        = bool
  default     = true
}

variable "create_bastion_sg" {
  description = "Whether to create the bastion security group (only needed in shared account)"
  type        = bool
  default     = true
}
