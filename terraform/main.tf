terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ── Provider ────────────────────────────────────────────────────────────────
provider "aws" {
  region = var.aws_region
}

data "aws_ami" "ubuntu_2204" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# ── SSH Key Pair ─────────────────────────────────────────────────────────────
# Reads the public key you generate locally (see README step 1)
resource "aws_key_pair" "sre_key" {
  key_name   = var.key_name
  public_key = file(pathexpand(var.public_key_path))
}

# ── Security Group ────────────────────────────────────────────────────────────
resource "aws_security_group" "sre_sg" {
  name        = "sre-project-sg"
  description = "SRE End-Term Project — allow SSH, app, and monitoring ports"

  # SSH
  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_admin_cidr]
  }

  # Frontend (Nginx)
  ingress {
    description = "Frontend HTTP"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Prometheus
  ingress {
    description = "Prometheus"
    from_port   = 9091
    to_port     = 9091
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Grafana
  ingress {
    description = "Grafana"
    from_port   = 52057
    to_port     = 52057
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # cAdvisor
  ingress {
    description = "cAdvisor"
    from_port   = 8081
    to_port     = 8081
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # All outbound allowed
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "sre-project-sg"
    Project = "SRE-EndTerm"
  }
}

# ── EC2 Instance ──────────────────────────────────────────────────────────────
resource "aws_instance" "sre_server" {
  ami                    = var.ami_id != "" ? var.ami_id : data.aws_ami.ubuntu_2204.id
  instance_type          = var.instance_type # t2.micro = free tier
  key_name               = aws_key_pair.sre_key.key_name
  vpc_security_group_ids = [aws_security_group.sre_sg.id]

  # Give the instance enough disk space for Docker images
  root_block_device {
    volume_size = 20 # GB  (free tier allows up to 30 GB)
    volume_type = "gp3"
  }

  metadata_options {
    http_tokens = "required"
  }

  # Bootstrap script — runs once on first boot
  user_data = <<-EOF
    #!/bin/bash
    apt-get update -y
    apt-get install -y python3 python3-pip
    # Python3 is required by Ansible; nothing else needed here —
    # the Ansible playbook handles the full Docker install.
  EOF

  tags = {
    Name    = "sre-project-server"
    Project = "SRE-EndTerm"
  }
}
