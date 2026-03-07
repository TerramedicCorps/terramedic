variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "terramedic"
}

variable "bucket_prefix" {
  description = "Prefix for bucket names (without environment suffix)"
  type        = string
  default     = "terramedic"
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, production)"
  type        = string
}

variable "use_random_suffix" {
  description = "Whether to add random suffix to bucket names for uniqueness. Set to false if you want predictable names."
  type        = bool
  default     = true
}

variable "force_destroy" {
  description = "Whether to force destroy the bucket even if it contains objects"
  type        = bool
  default     = false
}

variable "enable_lifecycle_rules" {
  description = "Whether to enable lifecycle rules for cost optimization"
  type        = bool
  default     = true
}

variable "enable_cloudfront" {
  description = "Whether to create CloudFront distribution"
  type        = bool
  default     = false
}

variable "cors_origins" {
  description = "Allowed CORS origins for the bucket"
  type        = list(string)
  default     = ["*"]
}

variable "ip_whitelist" {
  description = "IP addresses allowed to access the bucket (leave empty for public access)"
  type        = list(string)
  default     = []
}
