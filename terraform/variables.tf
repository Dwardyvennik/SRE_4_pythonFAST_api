variable "aws_region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "us-east-1" # cheapest / most AMIs available; change if needed
}

variable "instance_type" {
  description = "EC2 instance type. t2.micro is free-tier eligible."
  type        = string
  default     = "t2.micro"
}

variable "ami_id" {
  description = "Optional Ubuntu 22.04 LTS AMI override. Leave empty to auto-detect per region."
  type        = string
  default     = ""
}

variable "key_name" {
  description = "Name for the AWS Key Pair resource."
  type        = string
  default     = "sre-deployer-key"
}

variable "public_key_path" {
  description = "Path to the LOCAL public key file to upload to AWS."
  type        = string
  default     = "~/.ssh/sre-key.pub"
}

variable "private_key_path" {
  description = "Path to the LOCAL private key used by SSH and Ansible."
  type        = string
  default     = "~/.ssh/sre-key"
}

variable "allowed_admin_cidr" {
  description = "CIDR allowed to SSH into the instance. For demos, set this to your public IP with /32."
  type        = string
  default     = "0.0.0.0/0"
}
