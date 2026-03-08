# VPC and Networking Module

# Use existing VPC or create a new one
locals {
  vpc_id = var.create_vpc ? aws_vpc.main[0].id : var.vpc_id

  # Subnet outputs will be either the created subnets or the provided existing ones
  public_subnet_ids = var.create_public_subnets ? [
    aws_subnet.public_a[0].id,
    aws_subnet.public_b[0].id
  ] : var.public_subnet_ids

  private_subnet_ids = var.create_private_subnets ? [
    aws_subnet.private_a[0].id,
    aws_subnet.private_b[0].id
  ] : var.private_subnet_ids

  private_db_subnet_ids = var.create_db_subnets ? [
    aws_subnet.private_db_a[0].id,
    aws_subnet.private_db_b[0].id
  ] : var.db_subnet_ids
}

# VPC configuration - only created if create_vpc is true
resource "aws_vpc" "main" {
  count = var.create_vpc ? 1 : 0

  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.prefix}-vpc"
  }
}

# Data source to get existing VPC information when using an existing VPC
data "aws_vpc" "existing" {
  count = var.create_vpc ? 0 : 1
  id    = var.vpc_id
}

locals {
  # Use existing VPC information for outputs and validations
  existing_vpc_cidr = var.create_vpc ? "" : join("", data.aws_vpc.existing[*].cidr_block)

  vpc_cidr_block = var.create_vpc ? var.vpc_cidr : local.existing_vpc_cidr
}

# Public subnets for ALB - only created if create_public_subnets is true
resource "aws_subnet" "public_a" {
  count = var.create_public_subnets ? 1 : 0

  vpc_id                  = local.vpc_id
  cidr_block              = var.public_subnet_a_cidr
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.prefix}-public-a"
  }
}

resource "aws_subnet" "public_b" {
  count = var.create_public_subnets ? 1 : 0

  vpc_id                  = local.vpc_id
  cidr_block              = var.public_subnet_b_cidr
  availability_zone       = "${var.aws_region}b"
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.prefix}-public-b"
  }
}

# Private app subnets - only created if create_private_subnets is true
resource "aws_subnet" "private_a" {
  count = var.create_private_subnets ? 1 : 0

  vpc_id                  = local.vpc_id
  cidr_block              = var.private_subnet_a_cidr
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = false

  tags = {
    Name = "${var.prefix}-private-a"
  }
}

resource "aws_subnet" "private_b" {
  count = var.create_private_subnets ? 1 : 0

  vpc_id                  = local.vpc_id
  cidr_block              = var.private_subnet_b_cidr
  availability_zone       = "${var.aws_region}b"
  map_public_ip_on_launch = false

  tags = {
    Name = "${var.prefix}-private-b"
  }
}

# Private database subnets - only created if create_db_subnets is true
resource "aws_subnet" "private_db_a" {
  count = var.create_db_subnets ? 1 : 0

  vpc_id                  = local.vpc_id
  cidr_block              = var.private_db_subnet_a_cidr
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = false

  tags = {
    Name = "${var.prefix}-private-db-a"
  }
}

resource "aws_subnet" "private_db_b" {
  count = var.create_db_subnets ? 1 : 0

  vpc_id                  = local.vpc_id
  cidr_block              = var.private_db_subnet_b_cidr
  availability_zone       = "${var.aws_region}b"
  map_public_ip_on_launch = false

  tags = {
    Name = "${var.prefix}-private-db-b"
  }
}

# Internet Gateway - only created if create_vpc is true
resource "aws_internet_gateway" "igw" {
  count = var.create_vpc ? 1 : 0

  vpc_id = local.vpc_id

  tags = {
    Name = "${var.prefix}-igw"
  }
}

# Data source to get existing Internet Gateway if using existing VPC
data "aws_internet_gateway" "existing" {
  count = var.create_vpc ? 0 : 1

  filter {
    name   = "attachment.vpc-id"
    values = [var.vpc_id]
  }
}

# Public route table - only created if create_public_subnets is true
resource "aws_route_table" "public" {
  count = var.create_public_subnets ? 1 : 0

  vpc_id = local.vpc_id

  tags = {
    Name = "${var.prefix}-public-rt"
  }
}

# Routes for the public route table
# Route for the newly created IGW
resource "aws_route" "public_internet_gateway_new" {
  count = var.create_public_subnets && var.create_vpc ? 1 : 0

  route_table_id         = aws_route_table.public[0].id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.igw[0].id

  depends_on = [aws_route_table.public, aws_internet_gateway.igw]
}

# Route for the existing IGW
resource "aws_route" "public_internet_gateway_existing" {
  count = var.create_public_subnets && !var.create_vpc ? 1 : 0

  route_table_id         = aws_route_table.public[0].id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = data.aws_internet_gateway.existing[0].id

  depends_on = [aws_route_table.public, data.aws_internet_gateway.existing]
}

# App subnet route table - only created if create_private_subnets is true
resource "aws_route_table" "private_app" {
  count = var.create_private_subnets ? 1 : 0

  vpc_id = local.vpc_id

  tags = {
    Name = "${var.prefix}-private-app-rt"
  }
}

# Private subnets use VPC endpoints only - no default route to internet
# This allows Lambda to communicate with AWS services without NAT Gateway costs

# Database subnet route table - isolated - only created if create_db_subnets is true
resource "aws_route_table" "private_db" {
  count = var.create_db_subnets ? 1 : 0

  vpc_id = local.vpc_id
  # No route to internet - completely isolated

  tags = {
    Name = "${var.prefix}-private-db-rt"
  }
}

# Route table associations - only created if corresponding subnets are created
resource "aws_route_table_association" "public_a" {
  count = var.create_public_subnets ? 1 : 0

  subnet_id      = aws_subnet.public_a[0].id
  route_table_id = aws_route_table.public[0].id
}

resource "aws_route_table_association" "public_b" {
  count = var.create_public_subnets ? 1 : 0

  subnet_id      = aws_subnet.public_b[0].id
  route_table_id = aws_route_table.public[0].id
}

resource "aws_route_table_association" "private_app_a" {
  count = var.create_private_subnets ? 1 : 0

  subnet_id      = aws_subnet.private_a[0].id
  route_table_id = aws_route_table.private_app[0].id
}

resource "aws_route_table_association" "private_app_b" {
  count = var.create_private_subnets ? 1 : 0

  subnet_id      = aws_subnet.private_b[0].id
  route_table_id = aws_route_table.private_app[0].id
}

resource "aws_route_table_association" "private_db_a" {
  count = var.create_db_subnets ? 1 : 0

  subnet_id      = aws_subnet.private_db_a[0].id
  route_table_id = aws_route_table.private_db[0].id
}

resource "aws_route_table_association" "private_db_b" {
  count = var.create_db_subnets ? 1 : 0

  subnet_id      = aws_subnet.private_db_b[0].id
  route_table_id = aws_route_table.private_db[0].id
}

# VPC Endpoint for S3 - allows private resources to access S3 without internet
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = local.vpc_id
  service_name      = "com.amazonaws.${var.aws_region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids = compact([
    var.create_public_subnets ? aws_route_table.public[0].id : null,
    var.create_private_subnets ? aws_route_table.private_app[0].id : null,
    var.create_db_subnets ? aws_route_table.private_db[0].id : null,
  ])

  tags = {
    Name = "${var.prefix}-s3-endpoint"
  }
}

# Interface VPC Endpoints - allow Lambda in private subnets to reach AWS services
locals {
  interface_endpoints = {
    secretsmanager = "com.amazonaws.${var.aws_region}.secretsmanager"
    logs           = "com.amazonaws.${var.aws_region}.logs"
  }
  endpoint_subnet_ids = (
    length(local.private_subnet_ids) > 0 && var.enable_single_az_endpoints
    ? [local.private_subnet_ids[0]]
    : local.private_subnet_ids
  )
}

resource "aws_security_group" "vpc_endpoints" {
  count = var.create_vpc_endpoints ? 1 : 0

  name        = "${var.prefix}-vpc-endpoints-sg"
  description = "Security group for VPC interface endpoints"
  vpc_id      = local.vpc_id

  ingress {
    description = "HTTPS from VPC"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [local.vpc_cidr_block]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.prefix}-vpc-endpoints-sg"
  }
}

resource "aws_vpc_endpoint" "interface" {
  for_each = var.create_vpc_endpoints ? local.interface_endpoints : {}

  vpc_id              = local.vpc_id
  service_name        = each.value
  vpc_endpoint_type   = "Interface"
  subnet_ids          = local.endpoint_subnet_ids
  security_group_ids  = [aws_security_group.vpc_endpoints[0].id]
  private_dns_enabled = true

  tags = {
    Name = "${var.prefix}-${each.key}-endpoint"
  }
}
