# Bastion Host Module

data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-arm64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Create a key pair only if explicitly instructed to do so
# This approach ensures we avoid conflicts with existing key pairs
resource "aws_key_pair" "bastion" {
  count      = var.create_new_key_pair ? 1 : 0
  key_name   = var.bastion_key_name
  public_key = var.bastion_public_key

  # Fail the apply if create_new_key_pair is true but no public key was provided
  lifecycle {
    precondition {
      condition     = var.bastion_public_key != ""
      error_message = "When create_new_key_pair is set to true, you must provide a bastion_public_key value."
    }
  }
}

resource "aws_instance" "bastion" {
  ami           = data.aws_ami.amazon_linux_2.id
  instance_type = "t4g.nano"
  # Use the key_name provided in the variable
  # This will refer to an existing key pair or one we're creating with the aws_key_pair resource
  # When bastion_public_key is empty, it is assumed the key pair already exists in AWS
  key_name                    = var.bastion_key_name
  vpc_security_group_ids      = [var.bastion_security_group_id]
  subnet_id                   = var.public_subnet_id
  associate_public_ip_address = true

  root_block_device {
    volume_size = 8
    volume_type = "gp3"
    encrypted   = true
  }

  user_data = <<-EOF
    #!/bin/bash
    # Install PostgreSQL client for troubleshooting if needed
    amazon-linux-extras enable postgresql13
    yum install -y postgresql

    # Set up automatic shutdown to save costs when idle
    # Auto-shutdown after 2 hours of idle time
    yum install -y bc

    cat > /usr/local/bin/check-idle.sh << 'IDLE'
    #!/bin/bash
    # Check if there are active SSH sessions
    ACTIVE_SSH=$(who | grep -c pts)
    # Check load average
    LOAD=$(uptime | awk '{print $(NF-2)}' | sed 's/,//')
    # If no SSH sessions and load is low, shut down
    if [ $ACTIVE_SSH -eq 0 ] && [ $(echo "$LOAD < 0.1" | bc) -eq 1 ]; then
      # Check how long it's been idle
      UPTIME=$(cat /proc/uptime | awk '{print $1}')
      LAST_LOGIN=$(last -n 1 | grep -v 'still logged in' | awk '{print $7,$8,$9,$10}')
      # If uptime is more than 2 hours, shut down
      if [ $(echo "$UPTIME > 7200" | bc) -eq 1 ]; then
        shutdown -h now "Auto-shutdown due to inactivity"
      fi
    fi
    IDLE

    chmod +x /usr/local/bin/check-idle.sh

    # Add cron job to check every 15 minutes
    echo "*/15 * * * * /usr/local/bin/check-idle.sh" > /etc/cron.d/idle-shutdown

    # Update server
    yum update -y

    # Create a welcome message with usage instructions
    cat > /etc/motd << 'MOTD'
    =======================================================
    Welcome to the Terramedic Database Jump Box
    =======================================================

    This server is configured to automatically shut down after
    2 hours of inactivity to save costs.

    To use with pgAdmin on your local machine:
    1. Keep this SSH session open
    2. In pgAdmin, connect to:
       - Host: localhost
       - Port: 5432
       - Username: (your database username)
       - Password: (your database password)

    =======================================================
    MOTD
  EOF

  tags = {
    Name = "${var.prefix}-bastion"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Elastic IP for Bastion Host
resource "aws_eip" "bastion" {
  domain = "vpc"

  tags = {
    Name = "${var.prefix}-bastion-eip"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Associate Elastic IP with Bastion Instance
resource "aws_eip_association" "bastion" {
  instance_id   = aws_instance.bastion.id
  allocation_id = aws_eip.bastion.id

  depends_on = [aws_instance.bastion]
}
