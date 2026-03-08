variable "credential_rotation_trigger" {
  description = "Change this value to trigger credential rotation (e.g., use timestamp or version)"
  type        = string
  default     = "initial-v1"
}

variable "prevent_destroy" {
  description = "Whether to prevent destruction of database resources (set to false for testing)"
  type        = bool
  default     = true
}

variable "prefix" {
  description = "Prefix to use for resource names"
  type        = string
  default     = "terramedic"
}

variable "aws_region" {
  description = "The AWS region to deploy to"
  type        = string
}

variable "db_subnet_ids" {
  description = "List of subnet IDs for the DB subnet group"
  type        = list(string)
}

variable "db_security_group_id" {
  description = "ID of the security group for the database"
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

variable "db_name" {
  description = "Name of the database"
  type        = string
}

variable "db_username" {
  description = "Master username for the database"
  type        = string
}

variable "db_password" {
  description = "Master password for the database"
  type        = string
  sensitive   = true
}

variable "app_db_username" {
  description = "Application database username with restricted privileges"
  type        = string
}

variable "use_secrets_manager" {
  description = "Whether to use Secrets Manager for database passwords"
  type        = bool
  default     = false
}

variable "db_backup_retention_period" {
  description = "Backup retention period in days"
  type        = number
  default     = 14
}
