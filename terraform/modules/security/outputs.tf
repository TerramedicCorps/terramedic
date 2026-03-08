output "db_security_group_id" {
  description = "ID of the database security group"
  value       = length(aws_security_group.db_sg) > 0 ? aws_security_group.db_sg[0].id : null
}

output "bastion_security_group_id" {
  description = "ID of the bastion host security group"
  value       = length(aws_security_group.bastion_sg) > 0 ? aws_security_group.bastion_sg[0].id : null
}

output "waf_web_acl_arn" {
  description = "ARN of the WAF Web ACL"
  value       = length(aws_wafv2_web_acl.main) > 0 ? aws_wafv2_web_acl.main[0].arn : null
}
