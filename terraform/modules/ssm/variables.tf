variable "prefix" {
  description = "Resource name prefix"
  type        = string
}

variable "db_endpoint" {
  description = "Database endpoint"
  type        = string
}

variable "db_name_prefix" {
  description = "Database name prefix (will append _dev, _staging, _prod)"
  type        = string
  default     = "terramedic"
}

variable "environments" {
  description = "Set of environment names"
  type        = set(string)
  default     = ["dev", "prod"]
}

variable "app_db_username" {
  description = "Database username for the application"
  type        = string
}

variable "app_db_password" {
  description = "Database password for the application"
  type        = string
  sensitive   = true
}

variable "django_secret_key" {
  description = "Django secret key"
  type        = string
  default     = ""
  sensitive   = true
}

variable "site_password" {
  description = "Site password for access protection"
  type        = string
  default     = ""
  sensitive   = true
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
