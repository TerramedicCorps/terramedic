variable "prefix" {
  description = "Prefix to use for resource names"
  type        = string
  default     = "terramedic"
}

variable "vpc_id" {
  description = "ID of the VPC to monitor"
  type        = string
}

variable "budget_limit_amount" {
  description = "Monthly budget limit amount in USD"
  type        = string
  default     = "30"
}

variable "alert_email" {
  description = "Email address to receive budget and other alerts"
  type        = string
}
