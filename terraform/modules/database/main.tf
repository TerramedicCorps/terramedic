# Database Module

# Local values for conditional resources
locals {
  # Extract PostgreSQL major version for parameter group naming
  pg_version = split(".", var.db_engine_version)[0]

  # Parameter group names based on prevent_destroy setting
  parameter_group_name = var.prevent_destroy ? aws_db_parameter_group.postgres[0].name : aws_db_parameter_group.postgres_testing[0].name
}

# KMS key for RDS encryption
resource "aws_kms_key" "rds" {
  description             = "KMS key for RDS encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  tags = {
    Name = "${var.prefix}-rds-kms-key"
  }
}

resource "aws_kms_alias" "rds" {
  name          = "alias/${var.prefix}-rds"
  target_key_id = aws_kms_key.rds.key_id
}

# DB Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${var.prefix}-db-subnet"
  subnet_ids = var.db_subnet_ids

  tags = {
    Name = "${var.prefix}-db-subnet"
  }
}

# Create the master DB secret in Secrets Manager if it doesn't exist
resource "aws_secretsmanager_secret" "db_master" {
  count       = var.use_secrets_manager ? 1 : 0
  name        = "${var.prefix}/database-master"
  description = "Master credentials for the ${var.prefix} database"

  # Add KMS key when available
  # kms_key_id  = var.kms_key_id

  tags = {
    Name = "${var.prefix}-db-master-secret"
  }

  # Handle resource conflict
  lifecycle {
    ignore_changes = [
      tags
    ]
  }
}

# Store initial credentials in the secret
resource "aws_secretsmanager_secret_version" "db_master_initial" {
  count     = var.use_secrets_manager ? 1 : 0
  secret_id = aws_secretsmanager_secret.db_master[0].id
  secret_string = jsonencode({
    username = var.db_username
    password = var.db_password
    host     = "" # Will be updated after DB creation
    port     = "" # Will be updated after DB creation
    dbname   = var.db_name
  })
}

locals {
  # Always use the input variables for initial creation
  # The secret will be updated with actual values after DB creation
  master_username = var.db_username
  master_password = var.db_password

  # Set a default value for app_username if not specified
  app_username = var.app_db_username == "" ? "app_user" : var.app_db_username
}

# RDS PostgreSQL Instance
resource "aws_db_instance" "postgres" {
  identifier        = "${var.prefix}-db" # Set a consistent identifier with the project prefix
  allocated_storage = var.db_allocated_storage
  storage_type      = "gp3"
  engine            = "postgres"
  engine_version    = var.db_engine_version
  instance_class    = var.db_instance_class
  db_name           = var.db_name
  username          = local.master_username
  password          = local.master_password
  # Use the regular parameter group for basic parameters
  # Note: Static parameters are defined in postgres_static but not associated with the instance
  parameter_group_name         = local.parameter_group_name
  db_subnet_group_name         = aws_db_subnet_group.main.name
  vpc_security_group_ids       = [var.db_security_group_id]
  skip_final_snapshot          = can(regex("test|dev", var.prefix)) ? true : false
  final_snapshot_identifier    = can(regex("test|dev", var.prefix)) ? null : "${var.prefix}-final-snapshot"
  deletion_protection          = can(regex("test|dev", var.prefix)) ? false : true
  multi_az                     = false
  backup_retention_period      = var.db_backup_retention_period
  backup_window                = "03:00-04:00"
  maintenance_window           = "mon:04:00-mon:05:00"
  performance_insights_enabled = false
  storage_encrypted            = true
  kms_key_id                   = aws_kms_key.rds.arn
  monitoring_interval          = 0
  publicly_accessible          = false

  tags = {
    Name = "${var.prefix}-db"
  }
}

# PostgreSQL Parameter Group - Production (with prevent_destroy)
resource "aws_db_parameter_group" "postgres" {
  count  = var.prevent_destroy ? 1 : 0
  name   = "${var.prefix}-pg-${local.pg_version}-prod"
  family = "postgres${local.pg_version}"

  tags = {
    Name = "${var.prefix}-pg-${local.pg_version}-prod"
  }

  lifecycle {
    prevent_destroy = true
  }
}

# PostgreSQL Parameter Group - Testing (without prevent_destroy)
resource "aws_db_parameter_group" "postgres_testing" {
  count  = var.prevent_destroy ? 0 : 1
  name   = "${var.prefix}-pg-${local.pg_version}-test"
  family = "postgres${local.pg_version}"

  tags = {
    Name = "${var.prefix}-pg-${local.pg_version}-test"
  }
}

# Static Parameter Group - Production (with prevent_destroy)
resource "aws_db_parameter_group" "postgres_static" {
  count  = var.prevent_destroy ? 1 : 0
  name   = "${var.prefix}-pg-${local.pg_version}-static-prod"
  family = "postgres${local.pg_version}"

  # Include static parameters with pending-reboot apply method
  parameter {
    name         = "shared_preload_libraries"
    value        = "pg_stat_statements"
    apply_method = "pending-reboot"
  }

  tags = {
    Name = "${var.prefix}-pg-${local.pg_version}-static-prod"
  }

  lifecycle {
    prevent_destroy = true
  }

  depends_on = [
    aws_db_instance.postgres
  ]
}

# Static Parameter Group - Testing (without prevent_destroy)
resource "aws_db_parameter_group" "postgres_static_testing" {
  count  = var.prevent_destroy ? 0 : 1
  name   = "${var.prefix}-pg-${local.pg_version}-static-test"
  family = "postgres${local.pg_version}"

  # Include static parameters with pending-reboot apply method
  parameter {
    name         = "shared_preload_libraries"
    value        = "pg_stat_statements"
    apply_method = "pending-reboot"
  }

  tags = {
    Name = "${var.prefix}-pg-${local.pg_version}-static-test"
  }

  depends_on = [
    aws_db_instance.postgres
  ]
}
