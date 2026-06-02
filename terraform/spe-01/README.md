# SPE-01 Terraform Artifact — Financial App PE

Terraform artifact package for **AIQ-PE-01**: Service Production Environment #1 (SPE-01).

This package provisions a minimal, free-tier-friendly AWS EC2 instance to validate that NDM can deploy and operate an internet-accessible AI-powered service.

## Scope

### Creates

| Resource | Purpose |
|----------|---------|
| EC2 instance | Runs Dockerized Flask app (`taig2k/finance_app_for_aws`) |
| Security group | HTTP (80) and SSH (22) inbound |
| Root EBS volume | 8 GB gp3, encrypted |
| User-data bootstrap | Installs Docker, pulls image, starts systemd service |

### Does NOT create

RDS, load balancer, Route 53, CloudFront, ECS, EKS, Fargate, NAT Gateway, multi-AZ resources, or other paid managed services.

## Prerequisites

- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.5
- [AWS CLI](https://aws.amazon.com/cli/) configured with profile **`nebula`**
- An existing EC2 key pair in **`us-east-1`** for SSH
- OpenAI API key (provided at apply time, never committed)

Verify AWS access:

```powershell
aws sts get-caller-identity --profile nebula
```

## Quick Start (Operator — after DWN TVR approval)

> **Governance:** AIW creates this artifact only. Do not run `terraform apply` until DWN review, TVR creation, and operator approval.

```powershell
cd terraform/spe-01

# Copy and edit non-secret variables
copy terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars: set ssh_key_name (and optionally restrict CIDRs)

terraform init
terraform plan -var-file=terraform.tfvars

# Provide OpenAI key via environment variable (preferred — not written to disk)
$env:TF_VAR_openai_api_key = "sk-your-key-here"
terraform apply -var-file=terraform.tfvars
```

Alternatively pass the key inline (avoid shell history on shared machines):

```powershell
terraform apply -var-file=terraform.tfvars -var="openai_api_key=sk-your-key-here"
```

## Outputs

After apply:

```powershell
terraform output app_url
terraform output public_ip
terraform output ssh_command
```

Open the `app_url` in a browser (HTTP only — no HTTPS for this PE).

## Architecture

```
Internet
   │
   ├─ HTTP :80  ──► EC2 (t2.micro, public IP)
   │                  └─ Docker: taig2k/finance_app_for_aws
   │                       └─ Flask :5000 (mapped to host :80)
   │                            └─ OpenAI API (outbound HTTPS)
   │
   └─ SSH :22   ──► ec2-user (operator)
```

## Secret Handling

| Rule | Implementation |
|------|----------------|
| No hardcoded secrets | `openai_api_key` is a sensitive Terraform variable with empty default |
| No committed secrets | `terraform.tfvars` is gitignored; example file has no key |
| Environment variable | Container receives `OPENAI_API_KEY` via systemd `EnvironmentFile` |

If the key is not passed at apply time, bootstrap writes a placeholder env file. SSH in, edit `/opt/financial-app/env`, then:

```bash
sudo systemctl restart financial-app
```

## Instance Layout

| Path | Purpose |
|------|---------|
| `/opt/financial-app/config.json` | App config (mounted read-only into container) |
| `/opt/financial-app/env` | `OPENAI_API_KEY` (mode 600) |
| `/opt/financial-app/data` | Transaction persistence |
| `/opt/financial-app/uploads` | Upload storage |
| `/var/log/financial-app-bootstrap.log` | User-data bootstrap log |

## Service Management (SSH)

```bash
sudo systemctl status financial-app
sudo journalctl -u financial-app -f
sudo docker ps
```

## Variables Reference

See `variables.tf` and `terraform.tfvars.example` for all inputs.

Required:

- `ssh_key_name` — EC2 key pair name in us-east-1

Sensitive (apply-time only):

- `openai_api_key` — passed via `TF_VAR_openai_api_key` or `-var`

## Files in This Package

| File | Description |
|------|-------------|
| `provider.tf` | AWS provider (profile `nebula`, region `us-east-1`) |
| `main.tf` | EC2 instance, security group, AMI lookup |
| `variables.tf` | Input variables |
| `outputs.tf` | Public IP, app URL, SSH command |
| `terraform.tfvars.example` | Non-secret variable template |
| `user_data.sh` | Bootstrap: Docker install, image pull, systemd unit |
| `VALIDATION.md` | Post-apply PE validation checklist |
| `CLEANUP.md` | Teardown instructions |

## Governance

1. AIW creates this Terraform artifact (complete).
2. DWN reviews artifact and creates TVR.
3. Operator approves execution.
4. Operator runs `terraform plan` / `terraform apply`.
5. Operator validates PE per `VALIDATION.md`.
6. Operator destroys PE per `CLEANUP.md` when done.

## Cost Notes

Designed for AWS Free Tier where eligible:

- `t2.micro` EC2 (750 hrs/month free tier)
- 8 GB gp3 EBS (within 30 GB free tier allowance)
- Public IP with direct internet egress (no NAT Gateway)

Stop the instance when not in use to conserve free-tier hours.
