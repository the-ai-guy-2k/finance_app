data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-kernel-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_security_group" "spe01" {
  name        = "${var.project_name}-${var.environment}-sg"
  description = "SPE-01 security group: HTTP and SSH inbound for Financial App PE"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "HTTP for demo access"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = var.http_allowed_cidrs
  }

  ingress {
    description = "SSH for operator access"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.ssh_allowed_cidrs
  }

  egress {
    description = "Allow all outbound (OpenAI API, Docker Hub pulls)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-sg"
  })
}

resource "aws_instance" "spe01" {
  ami                         = data.aws_ami.amazon_linux_2023.id
  instance_type               = var.instance_type
  key_name                    = var.ssh_key_name
  subnet_id                   = data.aws_subnets.default.ids[0]
  vpc_security_group_ids      = [aws_security_group.spe01.id]
  associate_public_ip_address = true

  iam_instance_profile = var.enable_ec2_iam_ssm ? aws_iam_instance_profile.spe01[0].name : null

  user_data = templatefile("${path.module}/user_data.sh", {
    docker_image              = var.docker_image
    aws_region                = var.aws_region
    openai_ssm_parameter_name = var.openai_ssm_parameter_name
    bootstrap_openai_api_key  = var.enable_ec2_iam_ssm ? "" : var.openai_api_key
  })

  user_data_replace_on_change = true

  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.root_volume_size_gb
    encrypted             = true
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 2
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}"
  })
}
