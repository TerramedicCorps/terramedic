output "bastion_public_ip" {
  description = "Public IP address of the bastion host (Elastic IP)"
  value       = aws_eip.bastion.public_ip
}

output "bastion_key_pair_name" {
  description = "Name of the bastion key pair"
  value       = var.bastion_key_name
}

output "bastion_key_pair_created" {
  description = "Whether the bastion key pair was created"
  value       = var.create_new_key_pair && length(aws_key_pair.bastion) > 0
}
