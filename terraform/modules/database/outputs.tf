output "db_instance_endpoint" {
  description = "The endpoint of the database"
  value       = aws_db_instance.postgres.endpoint
}

output "db_instance_address" {
  description = "The hostname of the database instance"
  value       = aws_db_instance.postgres.address
}

output "db_instance_port" {
  description = "The port of the database"
  value       = aws_db_instance.postgres.port
}

output "db_instance_name" {
  description = "The name of the database"
  value       = aws_db_instance.postgres.db_name
}

output "db_kms_key_arn" {
  description = "The ARN of the KMS key used for RDS encryption"
  value       = aws_kms_key.rds.arn
}

# Technical connection info for automation
output "database_connection_info" {
  description = "Database connection information for automation"
  value = {
    endpoint    = aws_db_instance.postgres.endpoint
    address     = aws_db_instance.postgres.address
    port        = aws_db_instance.postgres.port
    database    = aws_db_instance.postgres.db_name
    master_user = local.master_username
    app_user    = local.app_username
  }
  sensitive = true
}
