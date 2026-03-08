variable "environment" {
  description = "Environment name (e.g., dev, prod) -- used for ECR repository naming"
  type        = string
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
