output "instance_id" {
  description = "EC2 instance ID for SPE-01"
  value       = aws_instance.spe01.id
}

output "public_ip" {
  description = "Public IPv4 address for browser and SSH access"
  value       = aws_instance.spe01.public_ip
}

output "public_dns" {
  description = "Public DNS name for the instance"
  value       = aws_instance.spe01.public_dns
}

output "security_group_id" {
  description = "Security group ID attached to the SPE-01 instance"
  value       = aws_security_group.spe01.id
}

output "app_url" {
  description = "HTTP URL to access the Financial App demo"
  value       = "http://${aws_instance.spe01.public_ip}"
}

output "ssh_command" {
  description = "Example SSH command for operator access (Amazon Linux default user: ec2-user)"
  value       = "ssh -i <your-private-key.pem> ec2-user@${aws_instance.spe01.public_ip}"
}

output "docker_service_name" {
  description = "Systemd unit name for the container on the instance"
  value       = "financial-app.service"
}

output "openai_ssm_parameter_name" {
  description = "SSM parameter path for OpenAI API key"
  value       = var.openai_ssm_parameter_name
}

output "docker_image" {
  description = "Pinned Docker image used by SPE-01 bootstrap"
  value       = var.docker_image
}
