output "lambda_repository_url" {
  description = "URL of the Lambda ECR repository"
  value       = aws_ecr_repository.lambda.repository_url
}

output "lambda_repository_name" {
  description = "Name of the Lambda ECR repository"
  value       = aws_ecr_repository.lambda.name
}
