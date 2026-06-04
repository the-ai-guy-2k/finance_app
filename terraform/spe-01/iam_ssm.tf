resource "aws_ssm_parameter" "openai_api_key" {
  count = var.openai_api_key != "" ? 1 : 0

  name  = var.openai_ssm_parameter_name
  type  = "SecureString"
  value = var.openai_api_key

  tags = merge(var.tags, {
    Name = "${var.project_name}-${var.environment}-openai-key"
  })
}

resource "aws_iam_role" "spe01_ec2" {
  name = "${var.project_name}-${var.environment}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy" "spe01_ssm_read" {
  name = "${var.project_name}-${var.environment}-ssm-openai-read"
  role = aws_iam_role.spe01_ec2.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters"
        ]
        Resource = "arn:aws:ssm:${var.aws_region}:*:parameter${var.openai_ssm_parameter_name}"
      }
    ]
  })
}

resource "aws_iam_instance_profile" "spe01" {
  name = "${var.project_name}-${var.environment}-instance-profile"
  role = aws_iam_role.spe01_ec2.name
}
