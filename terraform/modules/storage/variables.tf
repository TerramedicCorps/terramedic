variable "prefix" {
  description = "Prefix for all resources"
  type        = string
}

variable "domain_name" {
  description = "The domain name for the application"
  type        = string
}

variable "force_destroy" {
  description = "Whether to force destroy the bucket even if it contains objects"
  type        = bool
  default     = false
}

variable "cors_allowed_origins" {
  description = "List of allowed origins for CORS configuration"
  type        = list(string)
  default     = ["*"]
}

variable "enable_versioning" {
  description = "Whether to enable versioning on the bucket"
  type        = bool
  default     = true
}

variable "enable_lifecycle_rules" {
  description = "Whether to enable lifecycle rules for cost optimization"
  type        = bool
  default     = true
}

variable "noncurrent_version_expiration_days" {
  description = "Number of days after which to expire noncurrent versions"
  type        = number
  default     = 30
}

variable "enable_cloudfront" {
  description = "Whether to create CloudFront distribution (set to false for dev environments)"
  type        = bool
  default     = true
}

# CloudFront TTL variables for S3 content (user uploads, media files)
variable "s3_cache_min_ttl" {
  description = "Minimum TTL for S3 content in seconds"
  type        = number
  default     = 0
}

variable "s3_cache_default_ttl" {
  description = "Default TTL for S3 content in seconds"
  type        = number
  default     = 3600 # 1 hour (development-friendly)
}

variable "s3_cache_max_ttl" {
  description = "Maximum TTL for S3 content in seconds"
  type        = number
  default     = 86400 # 1 day
}

# CloudFront TTL variables for Django static files
variable "static_cache_min_ttl" {
  description = "Minimum TTL for Django static files in seconds"
  type        = number
  default     = 0
}

variable "static_cache_default_ttl" {
  description = "Default TTL for Django static files in seconds"
  type        = number
  default     = 3600 # 1 hour (development-friendly)
}

variable "static_cache_max_ttl" {
  description = "Maximum TTL for Django static files in seconds"
  type        = number
  default     = 86400 # 1 day
}
