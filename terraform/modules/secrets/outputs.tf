output "db_url_secret_arn" {
  description = "ARN of the database URL secret"
  value       = aws_secretsmanager_secret.db_url.arn
}

output "secret_key_secret_arn" {
  description = "ARN of the Django secret key secret"
  value       = aws_secretsmanager_secret.secret_key.arn
}

output "secrets_kms_key_arn" {
  description = "ARN of the KMS key used for Secrets Manager"
  value       = aws_kms_key.secrets.arn
}

output "site_password_secret_arn" {
  description = "ARN of the site password secret"
  value       = aws_secretsmanager_secret.site_password_secret.arn
}
