variable "aws_profile" {
  description = "AWS CLI profile name"
  type        = string
  default     = "nebula"
}

variable "aws_region" {
  description = "AWS region for SPE-01 resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project identifier used in resource names and tags"
  type        = string
  default     = "financial-app"
}

variable "environment" {
  description = "Environment label for SPE-01"
  type        = string
  default     = "spe-01"
}

variable "instance_type" {
  description = "EC2 instance type (t2.micro or t3.micro recommended for free tier)"
  type        = string
  default     = "t2.micro"
}

variable "root_volume_size_gb" {
  description = "Root EBS volume size in GB"
  type        = number
  default     = 8
}

variable "ssh_key_name" {
  description = "Name of an existing EC2 key pair in us-east-1 for SSH access"
  type        = string
}

variable "http_allowed_cidrs" {
  description = "CIDR blocks allowed to reach the app on HTTP port 80"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "ssh_allowed_cidrs" {
  description = "CIDR blocks allowed to reach the instance on SSH port 22"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "docker_image" {
  description = "Docker Hub image to run the Financial App"
  type        = string
  default     = "taig2k/finance_app_for_aws:latest"
}

variable "openai_api_key" {
  description = "OpenAI API key injected into the container at bootstrap. Pass via TF_VAR_openai_api_key or -var at apply time. Never commit this value."
  type        = string
  sensitive   = true
  default     = ""
}

variable "tags" {
  description = "Additional tags applied to all resources"
  type        = map(string)
  default = {
    Project     = "financial-app"
    Environment = "spe-01"
    ManagedBy   = "terraform"
    Purpose     = "NDM PE validation"
  }
}
