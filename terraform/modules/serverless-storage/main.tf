# Serverless Storage Module - S3 bucket for Lambda/serverless deployments
# Creates a single environment-specific S3 bucket for static assets and uploads

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.0"
    }
  }
}

# Random suffix for bucket uniqueness (only if enabled)
resource "random_id" "bucket_suffix" {
  count       = var.use_random_suffix ? 1 : 0
  byte_length = 4
}

locals {
  suffix      = var.use_random_suffix && length(random_id.bucket_suffix) > 0 ? "-${random_id.bucket_suffix[0].hex}" : ""
  bucket_name = "${var.bucket_prefix}-${var.environment}-assets${local.suffix}"
  is_prod     = var.environment == "production" || var.environment == "prod"
}

# S3 bucket for this environment
resource "aws_s3_bucket" "assets" {
  bucket        = local.bucket_name
  force_destroy = var.force_destroy

  tags = {
    Name        = local.bucket_name
    Environment = var.environment
    Purpose     = "Static assets for ${var.environment} environment"
    ManagedBy   = "Terraform"
    Project     = var.project_name
  }
}

# Bucket versioning
resource "aws_s3_bucket_versioning" "assets" {
  bucket = aws_s3_bucket.assets.id

  versioning_configuration {
    status = local.is_prod ? "Enabled" : "Suspended"
  }
}

# Public access block
resource "aws_s3_bucket_public_access_block" "assets" {
  bucket = aws_s3_bucket.assets.id

  block_public_acls       = local.is_prod
  block_public_policy     = false
  ignore_public_acls      = local.is_prod
  restrict_public_buckets = false
}

# CORS configuration
resource "aws_s3_bucket_cors_configuration" "assets" {
  bucket = aws_s3_bucket.assets.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "POST", "PUT", "HEAD"]
    allowed_origins = var.cors_origins
    expose_headers  = ["ETag"]
    max_age_seconds = 3600
  }
}

# Lifecycle rules for cost optimization
resource "aws_s3_bucket_lifecycle_configuration" "assets" {
  count = var.enable_lifecycle_rules && !local.is_prod ? 1 : 0

  bucket = aws_s3_bucket.assets.id

  rule {
    id     = "cleanup-old-files"
    status = "Enabled"

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    expiration {
      days = var.environment == "dev" ? 90 : 180
    }

    noncurrent_version_expiration {
      noncurrent_days = var.environment == "dev" ? 7 : 30
    }
  }
}

# Bucket policy for public read access
resource "aws_s3_bucket_policy" "assets" {
  bucket = aws_s3_bucket.assets.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      merge(
        {
          Sid       = "PublicReadGetObject"
          Effect    = "Allow"
          Principal = "*"
          Action    = "s3:GetObject"
          Resource  = "${aws_s3_bucket.assets.arn}/*"
        },
        local.is_prod && length(var.ip_whitelist) > 0 ? {
          Condition = {
            IpAddress = {
              "aws:SourceIp" = var.ip_whitelist
            }
          }
        } : {}
      )
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.assets]
}

# CloudFront distribution (optional)
resource "aws_cloudfront_distribution" "cdn" {
  count = var.enable_cloudfront ? 1 : 0

  enabled             = true
  is_ipv6_enabled     = true
  comment             = "CDN for ${var.environment} static assets"
  default_root_object = "index.html"
  price_class         = local.is_prod ? "PriceClass_All" : "PriceClass_100"

  origin {
    domain_name = aws_s3_bucket.assets.bucket_regional_domain_name
    origin_id   = "S3-${local.bucket_name}"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.cdn[0].cloudfront_access_identity_path
    }
  }

  default_cache_behavior {
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD", "OPTIONS"]
    target_origin_id = "S3-${local.bucket_name}"

    forwarded_values {
      query_string = true
      headers      = ["Origin", "Access-Control-Request-Method", "Access-Control-Request-Headers"]

      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = local.is_prod ? 86400 : 3600
    max_ttl                = local.is_prod ? 31536000 : 86400
    compress               = true
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Environment = var.environment
    Purpose     = "CDN for ${var.environment} static assets"
  }
}

# CloudFront OAI for secure S3 access
resource "aws_cloudfront_origin_access_identity" "cdn" {
  count = var.enable_cloudfront ? 1 : 0

  comment = "OAI for ${var.environment} environment CDN"
}

# IAM policy for Lambda to access this bucket
resource "aws_iam_policy" "lambda_s3_access" {
  name        = "${local.bucket_name}-lambda-access"
  description = "Allow Lambda functions to access ${var.environment} S3 bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.assets.arn,
          "${aws_s3_bucket.assets.arn}/*"
        ]
      }
    ]
  })
}
