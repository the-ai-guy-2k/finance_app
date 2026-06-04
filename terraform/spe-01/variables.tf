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
  description = "CIDR blocks allowed for SSH (operator IP only; must not be 0.0.0.0/0)"
  type        = list(string)

  validation {
    condition     = length(var.ssh_allowed_cidrs) > 0
    error_message = "ssh_allowed_cidrs must include at least one operator CIDR (e.g. 203.0.113.10/32)."
  }

  validation {
    condition     = !contains(var.ssh_allowed_cidrs, "0.0.0.0/0")
    error_message = "ssh_allowed_cidrs must not include 0.0.0.0/0. Set your operator public IP /32."
  }
}

variable "docker_image" {
  description = "Docker Hub image with exact tag or digest (no latest)"
  type        = string
  default     = "taig2k/finance_app_for_aws:89a4ea50348c73a8fcaf47c95ad7fb24a803d16d"

  validation {
    condition     = !strcontains(var.docker_image, ":latest")
    error_message = "docker_image must use a pinned SHA tag, not :latest."
  }
}

variable "openai_ssm_parameter_name" {
  description = "SSM Parameter Store path for OpenAI API key (SecureString)"
  type        = string
  default     = "/financial-app/spe-01/openai_api_key"
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
