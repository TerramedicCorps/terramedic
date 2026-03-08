output "db_url_parameter_arns" {
  description = "Map of database URL SSM parameter ARNs by environment"
  value       = { for env, param in aws_ssm_parameter.db_url : env => param.arn }
}

output "db_url_parameter_names" {
  description = "Map of database URL SSM parameter names by environment"
  value       = { for env, param in aws_ssm_parameter.db_url : env => param.name }
}

# Provide direct access for production (default for ECS)
output "production_db_url_arn" {
  description = "ARN of the production database URL parameter"
  value       = contains(keys(aws_ssm_parameter.db_url), "prod") ? aws_ssm_parameter.db_url["prod"].arn : null
}

output "secret_key_parameter_arn" {
  description = "ARN of the Django secret key SSM parameter"
  value       = aws_ssm_parameter.secret_key.arn
}

output "site_password_parameter_arn" {
  description = "ARN of the site password SSM parameter"
  value       = aws_ssm_parameter.site_password.arn
}

output "ssm_read_policy_arn" {
  description = "ARN of the IAM policy for reading SSM parameters"
  value       = aws_iam_policy.ssm_read.arn
}

output "parameter_names" {
  description = "Map of all SSM parameter names"
  value = merge(
    { for env, param in aws_ssm_parameter.db_url : "db_url_${env}" => param.name },
    {
      secret_key    = aws_ssm_parameter.secret_key.name
      site_password = aws_ssm_parameter.site_password.name
    }
  )
}
