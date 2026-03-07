# Security Module

# Database Security Group
resource "aws_security_group" "db_sg" {
  count = var.create_db_sg ? 1 : 0

  name        = "${var.prefix}-db-sg"
  description = "Allow PostgreSQL inbound traffic"
  vpc_id      = var.vpc_id

  tags = {
    Name = "${var.prefix}-db-sg"
  }
}

# Same-account Lambda SG-based ingress (used when Lambda is in the same account)
resource "aws_security_group_rule" "db_ingress_lambda_sg" {
  count = var.create_db_sg && var.enable_lambda_sg_rules ? 1 : 0

  lifecycle {
    precondition {
      condition     = var.lambda_security_group_id != ""
      error_message = "lambda_security_group_id must be set when enable_lambda_sg_rules is true."
    }
  }

  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = var.lambda_security_group_id
  security_group_id        = aws_security_group.db_sg[0].id
  description              = "PostgreSQL from Lambda security group"
}

resource "aws_security_group_rule" "db_egress_lambda_sg" {
  count = var.create_db_sg && var.enable_lambda_sg_rules ? 1 : 0

  type                     = "egress"
  from_port                = 0
  to_port                  = 0
  protocol                 = "-1"
  source_security_group_id = var.lambda_security_group_id
  security_group_id        = aws_security_group.db_sg[0].id
  description              = "Allow return traffic to the Lambda security group"
}

# Cross-account CIDR-based ingress (used when Lambda is in a different account)
resource "aws_security_group_rule" "db_ingress_lambda_cidrs" {
  count = var.create_db_sg && length(var.allowed_lambda_cidrs) > 0 ? 1 : 0

  type              = "ingress"
  from_port         = 5432
  to_port           = 5432
  protocol          = "tcp"
  cidr_blocks       = var.allowed_lambda_cidrs
  security_group_id = aws_security_group.db_sg[0].id
  description       = "PostgreSQL from cross-account Lambda subnets"
}

resource "aws_security_group_rule" "db_egress_lambda_cidrs" {
  count = var.create_db_sg && length(var.allowed_lambda_cidrs) > 0 ? 1 : 0

  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = var.allowed_lambda_cidrs
  security_group_id = aws_security_group.db_sg[0].id
  description       = "Allow return traffic to cross-account Lambda subnets"
}

# Bastion host ingress (only when bastion SG exists)
resource "aws_security_group_rule" "db_ingress_bastion" {
  count = var.create_db_sg && var.create_bastion_sg ? 1 : 0

  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.bastion_sg[0].id
  security_group_id        = aws_security_group.db_sg[0].id
  description              = "PostgreSQL from bastion host"
}

resource "aws_security_group_rule" "db_egress_bastion" {
  count = var.create_db_sg && var.create_bastion_sg ? 1 : 0

  type                     = "egress"
  from_port                = 0
  to_port                  = 0
  protocol                 = "-1"
  source_security_group_id = aws_security_group.bastion_sg[0].id
  security_group_id        = aws_security_group.db_sg[0].id
  description              = "Allow return traffic to the bastion host"
}

# Bastion Host Security Group
resource "aws_security_group" "bastion_sg" {
  count = var.create_bastion_sg ? 1 : 0

  name        = "${var.prefix}-bastion-sg"
  description = "Security group for bastion host"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_bastion_cidrs
    description = "SSH access from allowed IPs"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name = "${var.prefix}-bastion-sg"
  }
}

# WAF Web ACL
resource "aws_wafv2_web_acl" "main" {
  count = var.create_waf ? 1 : 0

  name        = "${var.prefix}-waf"
  description = "WAF for Terramedic application"
  scope       = "REGIONAL"

  default_action {
    allow {}
  }

  rule {
    name     = "AWS-AWSManagedRulesSQLiRuleSet"
    priority = 1

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesSQLiRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWS-AWSManagedRulesSQLiRuleSet"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.prefix}-waf"
    sampled_requests_enabled   = true
  }

  tags = {
    Name = "${var.prefix}-waf"
  }
}
