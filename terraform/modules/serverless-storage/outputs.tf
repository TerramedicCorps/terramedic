output "bucket_suffix" {
  description = "The random suffix used for the bucket (if enabled)"
  value       = var.use_random_suffix && length(random_id.bucket_suffix) > 0 ? random_id.bucket_suffix[0].hex : "none"
}

output "bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.assets.id
}

output "bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.assets.arn
}

output "bucket_regional_domain" {
  description = "Regional domain name of the S3 bucket"
  value       = aws_s3_bucket.assets.bucket_regional_domain_name
}

output "cloudfront_domain" {
  description = "CloudFront distribution domain (if enabled)"
  value       = length(aws_cloudfront_distribution.cdn) > 0 ? aws_cloudfront_distribution.cdn[0].domain_name : null
}

output "lambda_s3_policy_arn" {
  description = "IAM policy ARN for Lambda S3 access"
  value       = aws_iam_policy.lambda_s3_access.arn
}

output "configuration_summary" {
  description = "Summary of S3 bucket configuration"
  value = {
    bucket_name = aws_s3_bucket.assets.id
    versioning  = aws_s3_bucket_versioning.assets.versioning_configuration[0].status
    lifecycle   = length(aws_s3_bucket_lifecycle_configuration.assets) > 0 ? aws_s3_bucket_lifecycle_configuration.assets[0].rule[0].status : "Disabled"
    cloudfront  = length(aws_cloudfront_distribution.cdn) > 0 ? aws_cloudfront_distribution.cdn[0].domain_name : "Not enabled"
  }
}
