# Storage Module - S3 bucket for static assets

# Random suffix for S3 bucket to ensure global uniqueness
resource "random_id" "assets_bucket_suffix" {
  byte_length = 4
}

# S3 Bucket for Static Assets
resource "aws_s3_bucket" "static_assets" {
  bucket        = "${var.prefix}-static-assets-${random_id.assets_bucket_suffix.hex}"
  force_destroy = var.force_destroy

  tags = {
    Name        = "${var.prefix}-static-assets"
    Environment = var.prefix
    Purpose     = "Static assets storage"
  }
}

# Bucket ACL - Allow public read access
resource "aws_s3_bucket_public_access_block" "static_assets" {
  bucket = aws_s3_bucket.static_assets.id

  block_public_acls       = var.enable_cloudfront
  block_public_policy     = false
  ignore_public_acls      = var.enable_cloudfront
  restrict_public_buckets = false
}

# Bucket ownership controls
resource "aws_s3_bucket_ownership_controls" "static_assets" {
  bucket = aws_s3_bucket.static_assets.id

  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

# Bucket ACL (only when CloudFront is disabled for direct public access)
resource "aws_s3_bucket_acl" "static_assets" {
  count = var.enable_cloudfront ? 0 : 1

  bucket = aws_s3_bucket.static_assets.id
  acl    = "public-read"

  depends_on = [
    aws_s3_bucket_ownership_controls.static_assets,
    aws_s3_bucket_public_access_block.static_assets
  ]
}

# CORS Configuration for browser uploads
resource "aws_s3_bucket_cors_configuration" "static_assets" {
  bucket = aws_s3_bucket.static_assets.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD", "PUT", "POST"]
    allowed_origins = var.cors_allowed_origins
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# Versioning (optional, can be useful for recovery)
resource "aws_s3_bucket_versioning" "static_assets" {
  bucket = aws_s3_bucket.static_assets.id

  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Disabled"
  }
}

# Server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "static_assets" {
  bucket = aws_s3_bucket.static_assets.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Lifecycle rules for cost optimization (optional)
resource "aws_s3_bucket_lifecycle_configuration" "static_assets" {
  count  = var.enable_lifecycle_rules ? 1 : 0
  bucket = aws_s3_bucket.static_assets.id

  rule {
    id     = "cleanup-old-versions"
    status = "Enabled"

    filter {
      prefix = ""
    }

    noncurrent_version_expiration {
      noncurrent_days = var.noncurrent_version_expiration_days
    }
  }
}

# Bucket Policy for CloudFront access only (when CloudFront is enabled)
resource "aws_s3_bucket_policy" "static_assets_cloudfront" {
  count = var.enable_cloudfront ? 1 : 0

  bucket = aws_s3_bucket.static_assets.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontAccess"
        Effect = "Allow"
        Principal = {
          AWS = aws_cloudfront_origin_access_identity.static_assets[0].iam_arn
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.static_assets.arn}/*"
      }
    ]
  })

  depends_on = [
    aws_s3_bucket_public_access_block.static_assets,
    aws_cloudfront_origin_access_identity.static_assets
  ]
}

# Bucket Policy for direct public read access (when CloudFront is disabled)
resource "aws_s3_bucket_policy" "static_assets_public" {
  count = var.enable_cloudfront ? 0 : 1

  bucket = aws_s3_bucket.static_assets.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.static_assets.arn}/*"
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.static_assets]
}

# CloudFront Origin Access Identity
resource "aws_cloudfront_origin_access_identity" "static_assets" {
  count = var.enable_cloudfront ? 1 : 0

  comment = "OAI for ${var.prefix} static assets"
}

# CloudFront Distribution for static assets
resource "aws_cloudfront_distribution" "static_assets" {
  count = var.enable_cloudfront ? 1 : 0

  # S3 origin for user uploads and media files
  origin {
    domain_name = aws_s3_bucket.static_assets.bucket_regional_domain_name
    origin_id   = "S3-${aws_s3_bucket.static_assets.id}"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.static_assets[0].cloudfront_access_identity_path
    }
  }

  # Domain origin for Django static files served by WhiteNoise via ALB
  origin {
    domain_name = var.domain_name
    origin_id   = "Django-Static"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  enabled             = true
  is_ipv6_enabled     = true
  comment             = "CDN for ${var.prefix} static assets"
  default_root_object = "index.html"

  # Default cache behavior for S3 content (user uploads, media files)
  default_cache_behavior {
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${aws_s3_bucket.static_assets.id}"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl     = var.s3_cache_min_ttl
    default_ttl = var.s3_cache_default_ttl
    max_ttl     = var.s3_cache_max_ttl
  }

  # Cache behavior for Django static files served by WhiteNoise
  ordered_cache_behavior {
    path_pattern           = "/static/*"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "Django-Static"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
      headers = ["Origin", "Access-Control-Request-Headers", "Access-Control-Request-Method"]
    }

    min_ttl     = var.static_cache_min_ttl
    default_ttl = var.static_cache_default_ttl
    max_ttl     = var.static_cache_max_ttl
  }

  # Geographic restrictions (none by default)
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # SSL/TLS configuration
  viewer_certificate {
    cloudfront_default_certificate = true
  }

  # Price class (all edge locations for best performance)
  price_class = "PriceClass_All"

  tags = {
    Name = "${var.prefix}-static-assets-cdn"
  }
}

# IAM Policy for application uploads
resource "aws_iam_policy" "static_assets_upload" {
  name        = "${var.prefix}-static-assets-upload"
  description = "Policy for uploading static assets to S3"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:PutObjectAcl",
          "s3:GetObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.static_assets.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = aws_s3_bucket.static_assets.arn
      }
    ]
  })
}
