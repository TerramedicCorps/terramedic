# Network Outputs (consumed by prod/dev via terraform_remote_state)
output "vpc_id" {
  description = "Shared VPC ID"
  value       = module.networking.vpc_id
}

output "vpc_cidr" {
  description = "Shared VPC CIDR block"
  value       = module.networking.vpc_cidr
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.networking.public_subnet_ids
}

output "db_subnet_ids" {
  description = "Database subnet IDs"
  value       = module.networking.private_db_subnet_ids
}

output "db_subnet_cidrs" {
  description = "Database subnet CIDRs"
  value       = module.networking.db_subnet_cidrs
}

# Database Outputs
output "database_endpoint" {
  description = "RDS instance endpoint (host:port)"
  value       = module.database.db_instance_endpoint
}

output "database_address" {
  description = "RDS instance address (host only)"
  value       = module.database.db_instance_address
}

output "database_name" {
  description = "Primary database name"
  value       = module.database.db_instance_name
}

# Bastion Outputs
output "bastion_public_ip" {
  description = "Public IP of the bastion host"
  value       = module.bastion.bastion_public_ip
}

# Route table IDs (needed by prod/dev for VPC peering routes)
output "db_route_table_id" {
  description = "Route table ID for the DB subnets (for VPC peering routes)"
  value       = module.networking.private_db_route_table_id
}

# Monitoring
output "budget_info" {
  description = "Budget configuration summary"
  value       = module.monitoring.budget_info
}

# DNS
output "route53_zone_id" {
  description = "Route53 zone ID for the domain"
  value       = aws_route53_zone.main.zone_id
}

output "route53_nameservers" {
  description = "Route53 zone nameservers (update at domain registrar)"
  value       = aws_route53_zone.main.name_servers
}

output "dns_manager_role_arn" {
  description = "IAM role ARN for cross-account DNS management"
  value       = aws_iam_role.dns_manager.arn
}

# GitHub OIDC
output "github_oidc_role_arn" {
  description = "ARN of the GitHub Actions role for the shared account"
  value       = module.github_oidc.role_arn
}
