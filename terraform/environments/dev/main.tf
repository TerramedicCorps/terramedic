# Development Account
# Contains: VPC (private app subnets only), Lambda/Zappa (512MB, no keep-warm),
# ECR, S3 (no CloudFront), VPC peering to shared, GitHub OIDC,
# ACM wildcard cert, API Gateway custom domain (test-api.terramedic.org)
# DNS zone lives in shared account; dev creates records via cross-account role

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = var.tags
  }
}

# Provider for the shared account (used by VPC peering accepter)
provider "aws" {
  alias  = "shared"
  region = var.aws_region

  assume_role {
    role_arn = var.shared_peering_role_arn
  }

  default_tags {
    tags = var.tags
  }
}

# Provider for DNS record management in shared account's Route53 zone
provider "aws" {
  alias  = "dns"
  region = var.aws_region

  assume_role {
    role_arn = var.shared_dns_role_arn
  }

  default_tags {
    tags = var.tags
  }
}

# Read shared account outputs
data "terraform_remote_state" "shared" {
  backend = "s3"
  config = {
    bucket = "terramedic-terraform-state-${var.shared_account_id}"
    key    = "shared/terraform.tfstate"
    region = var.aws_region
  }
}

# Networking Module - VPC with private app subnets only (no public, no DB)
module "networking" {
  source = "../../modules/networking"

  prefix     = var.prefix
  aws_region = var.aws_region

  create_vpc = true
  vpc_cidr   = var.vpc_cidr

  # No public subnets in dev (no bastion, no public-facing resources)
  create_public_subnets = false

  create_private_subnets = true
  private_subnet_a_cidr  = var.private_subnet_a_cidr
  private_subnet_b_cidr  = var.private_subnet_b_cidr

  # No DB subnets (DB lives in shared)
  create_db_subnets = false

  # VPC endpoints for Lambda to reach AWS services (toggle to save costs)
  create_vpc_endpoints       = var.enable_vpc_endpoints
  enable_single_az_endpoints = true
}

# VPC Peering - dev to shared
module "vpc_peering" {
  source = "../../modules/vpc-peering"

  providers = {
    aws          = aws
    aws.accepter = aws.shared
  }

  name = "${var.prefix}-dev-to-shared"

  requester_vpc_id          = module.networking.vpc_id
  requester_vpc_cidr        = var.vpc_cidr
  requester_route_table_ids = compact([module.networking.private_app_route_table_id])
  requester_route_count     = 1

  accepter_vpc_id          = data.terraform_remote_state.shared.outputs.vpc_id
  accepter_vpc_cidr        = data.terraform_remote_state.shared.outputs.vpc_cidr
  accepter_account_id      = var.shared_account_id
  accepter_region          = var.aws_region
  accepter_route_table_ids = compact([data.terraform_remote_state.shared.outputs.db_route_table_id])
  accepter_route_count     = 1
}

# Zappa Module - smaller Lambda (512MB, no keep-warm)
module "zappa" {
  source = "../../modules/zappa"

  prefix       = var.prefix
  project_name = "terramedic"
  aws_region   = var.aws_region
  vpc_id       = module.networking.vpc_id

  create_lambda_sg = true
  # Lambda needs to reach shared account's DB subnets via VPC peering
  database_subnet_cidrs = data.terraform_remote_state.shared.outputs.db_subnet_cidrs

  secret_arns = [
    module.secrets.db_url_secret_arn,
    module.secrets.secret_key_secret_arn,
    module.secrets.anthropic_api_key_secret_arn,
  ]
  secrets_kms_key_arn = module.secrets.secrets_kms_key_arn

  worker_schedule_expression = var.worker_schedule_expression

  tags = var.tags
}

# Secrets Module
module "secrets" {
  source = "../../modules/secrets"

  prefix          = var.prefix
  app_db_username = var.app_db_username
  app_db_password = var.app_db_password
  db_endpoint     = data.terraform_remote_state.shared.outputs.database_endpoint
  db_name         = var.db_name
  site_password   = var.site_password
}

# SSM Module
module "ssm" {
  source = "../../modules/ssm"

  prefix          = var.prefix
  db_endpoint     = data.terraform_remote_state.shared.outputs.database_endpoint
  db_name_prefix  = var.db_name
  environments    = ["dev"]
  app_db_username = var.app_db_username
  app_db_password = var.app_db_password
  site_password   = var.site_password
  tags            = var.tags
}

# Attach SSM read policy to Zappa role
resource "aws_iam_role_policy_attachment" "zappa_ssm_access" {
  role       = module.zappa.zappa_deployment_role_name
  policy_arn = module.ssm.ssm_read_policy_arn
}

# Monitoring Module
module "monitoring" {
  source = "../../modules/monitoring"

  prefix              = var.prefix
  vpc_id              = module.networking.vpc_id
  budget_limit_amount = var.budget_limit_amount
  alert_email         = var.alert_email
}

# Serverless Storage Module - S3 bucket (no CloudFront)
module "serverless_storage" {
  source = "../../modules/serverless-storage"

  project_name = var.prefix
  environment  = "dev"

  force_destroy          = true
  enable_lifecycle_rules = true
  enable_cloudfront      = false
  cors_origins           = ["*"]
}

# Lambda ECR Module
module "lambda_ecr" {
  source      = "../../modules/lambda-ecr"
  environment = "dev"
  tags        = var.tags
}

# GitHub OIDC for CI/CD
module "github_oidc" {
  source = "../../modules/github-oidc"

  environment          = "dev"
  create_oidc_provider = true

  github_subjects = [
    "repo:${var.github_repo}:environment:dev",
    "repo:${var.github_repo}:pull_request",
  ]

  enable_terraform_policy      = true
  enable_infrastructure_policy = true
  resource_prefix              = var.resource_prefix
  peering_account_ids          = [var.shared_account_id]
  cross_account_role_arns      = [var.shared_dns_role_arn]
}

# ACM certificate for domain and all subdomains (stays in dev account)
resource "aws_acm_certificate" "main" {
  domain_name               = var.domain_name
  subject_alternative_names = ["*.${var.domain_name}"]
  validation_method         = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

# ACM validation records in shared account's Route53 zone
resource "aws_route53_record" "cert_validation" {
  provider = aws.dns
  for_each = toset([var.domain_name, "*.${var.domain_name}"])

  allow_overwrite = true
  zone_id         = data.terraform_remote_state.shared.outputs.route53_zone_id
  name = [
    for dvo in aws_acm_certificate.main.domain_validation_options : dvo.resource_record_name
    if dvo.domain_name == each.value
  ][0]
  type = [
    for dvo in aws_acm_certificate.main.domain_validation_options : dvo.resource_record_type
    if dvo.domain_name == each.value
  ][0]
  ttl = 60
  records = [
    [
      for dvo in aws_acm_certificate.main.domain_validation_options : dvo.resource_record_value
      if dvo.domain_name == each.value
    ][0]
  ]
}

resource "aws_acm_certificate_validation" "main" {
  certificate_arn         = aws_acm_certificate.main.arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
}

# API Gateway custom domain, base path mapping, and Route53 A record
# are managed by the deploy workflow (post-deploy step) since the API Gateway
# is created by Zappa, not Terraform. See .github/workflows/deploy.yml.
