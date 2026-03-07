# Shared Account
# Contains: VPC, RDS, Bastion, DB security group, Secrets (master), Monitoring,
# VPC peering accepter (for prod and dev), GitHub OIDC

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = var.tags
  }
}

provider "awscc" {
  region = var.aws_region
}

# Networking Module - VPC with public + DB subnets (no private app subnets needed)
module "networking" {
  source = "../../modules/networking"

  prefix     = var.prefix
  aws_region = var.aws_region

  create_vpc = true
  vpc_cidr   = var.vpc_cidr

  create_public_subnets = true
  public_subnet_a_cidr  = var.public_subnet_a_cidr
  public_subnet_b_cidr  = var.public_subnet_b_cidr

  # No private app subnets in shared account (Lambda runs in prod/dev accounts)
  create_private_subnets = false

  create_db_subnets        = true
  private_db_subnet_a_cidr = var.private_db_subnet_a_cidr
  private_db_subnet_b_cidr = var.private_db_subnet_b_cidr

  # No VPC endpoints needed in shared (Lambda accesses from prod/dev)
  create_vpc_endpoints = false
}

# Security Module - DB SG with cross-account CIDR-based ingress
module "security" {
  source = "../../modules/security"

  prefix = var.prefix
  vpc_id = module.networking.vpc_id

  # No Lambda in shared account, so no SG-based ingress
  lambda_security_group_id = ""

  # Cross-account Lambda subnet CIDRs for DB access
  allowed_lambda_cidrs = var.allowed_lambda_cidrs

  # Bastion SG for DB access
  create_bastion_sg     = true
  allowed_bastion_cidrs = var.allowed_bastion_cidrs

  # No WAF in shared account
  create_waf = false
}

# Database Module
module "database" {
  source = "../../modules/database"

  prefix                     = var.prefix
  aws_region                 = var.aws_region
  db_subnet_ids              = module.networking.private_db_subnet_ids
  db_security_group_id       = module.security.db_security_group_id
  db_allocated_storage       = var.db_allocated_storage
  db_engine_version          = var.db_engine_version
  db_instance_class          = var.db_instance_class
  db_name                    = var.db_name
  db_username                = var.db_username
  db_password                = var.db_password
  app_db_username            = var.app_db_username
  use_secrets_manager        = true
  db_backup_retention_period = 14
  auto_setup_database        = var.auto_setup_database
  prevent_destroy            = var.prevent_destroy
}

# Bastion Host Module
module "bastion" {
  source = "../../modules/bastion"

  prefix                    = var.prefix
  public_subnet_id          = module.networking.public_subnet_ids[0]
  bastion_security_group_id = module.security.bastion_security_group_id
  bastion_key_name          = var.bastion_key_name
  bastion_public_key        = var.bastion_public_key
  create_new_key_pair       = var.create_new_key_pair
}

# Monitoring Module
module "monitoring" {
  source = "../../modules/monitoring"

  prefix              = var.prefix
  vpc_id              = module.networking.vpc_id
  budget_limit_amount = var.budget_limit_amount
  alert_email         = var.alert_email
}

# GitHub OIDC for CI/CD
module "github_oidc" {
  source = "../../modules/github-oidc"

  environment          = "shared"
  create_oidc_provider = true

  github_subjects = [
    "repo:${var.github_repo}:environment:shared",
  ]

  enable_terraform_policy      = true
  enable_infrastructure_policy = true
  resource_prefix              = var.resource_prefix
  peering_account_ids          = []
}
