# ACI-DEVOPS-09 SPE-01 Stop Report

**Report ID:** ACI-DEVOPS-09  
**Timestamp:** 2026-06-03 16:37:24 -04:00  
**Mission:** Stop SPE-01 EC2 instance for break / relocation without destroying infrastructure

---

## Executive Summary

SPE-01 EC2 instance **`i-0b68a04f4d3aa5ab9`** was **stopped successfully**. Instance was **not destroyed**. Terraform state remains intact for resume from home.

**PAPE:** Not declared (full PE validation still pending)

---

## AWS Identity

| Field | Value |
|-------|-------|
| Account | `526123657916` |
| ARN | `arn:aws:iam::526123657916:user/nebula` |

---

## Instance Details

| Field | Value |
|-------|-------|
| **Instance ID** | `i-0b68a04f4d3aa5ab9` |
| **Name** | `financial-app-spe-01` |
| **Type** | `t3.micro` |
| **Region** | `us-east-1` |
| **Security group** | `sg-012c65dcf1602c97c` (unchanged) |

---

## State Transition

| Stage | State |
|-------|-------|
| **Previous state** | `running` |
| **Stop initiated** | `stopping` |
| **Final state** | **`stopped`** |

---

## Stop Command Result

**Success**

```powershell
aws ec2 stop-instances --profile nebula --region us-east-1 --instance-ids i-0b68a04f4d3aa5ab9
```

Wait confirmed via:

```powershell
aws ec2 wait instance-stopped --profile nebula --region us-east-1 --instance-ids i-0b68a04f4d3aa5ab9
```

---

## Public URL Before Stop

| Field | Value |
|-------|-------|
| **app_url** | http://98.92.209.167 |
| **HTTP status before stop** | 200 (verified during ACI-DEVOPS-08) |

App is **not reachable** while instance is stopped.

---

## Terraform State

| Check | Result |
|-------|--------|
| `terraform destroy` executed | **No** |
| Local state preserved | **Yes** (`terraform/spe-01/terraform.tfstate`) |
| EC2 instance deleted | **No** |
| Security group deleted | **No** |

---

## Resume Instructions (From Home)

### 1. Start the instance

```powershell
aws ec2 start-instances --profile nebula --region us-east-1 --instance-ids i-0b68a04f4d3aa5ab9
aws ec2 wait instance-running --profile nebula --region us-east-1 --instance-ids i-0b68a04f4d3aa5ab9
```

### 2. Get new public IP (may change after stop/start)

```powershell
aws ec2 describe-instances --profile nebula --region us-east-1 --instance-ids i-0b68a04f4d3aa5ab9 --query "Reservations[0].Instances[0].PublicIpAddress" --output text
```

Or from Terraform (after start):

```powershell
cd terraform/spe-01
terraform refresh -var-file=terraform.tfvars
terraform output app_url
```

**Note:** Public IP may differ from `98.92.209.167` after restart (no Elastic IP provisioned).

### 3. Wait for bootstrap / Docker (~1–2 minutes)

Poll HTTP until 200:

```powershell
curl http://<new-public-ip>
```

### 4. SSH (if needed)

```powershell
ssh -i terraform/spe-01/gina.pem ec2-user@<new-public-ip>
```

### 5. Continue PE validation

Follow `terraform/spe-01/VALIDATION.md` — full validation was pending before stop.

---

## Next Action From Home

1. Verify AWS profile `nebula` on home machine (or configure credentials)
2. Start instance (`aws ec2 start-instances ...`)
3. Refresh Terraform outputs for new `app_url`
4. Complete PE validation checklist
5. When done long-term, use `terraform/spe-01/CLEANUP.md` for destroy (only when explicitly approved)

---

## Success Criteria Checklist

| Criterion | Status |
|-----------|--------|
| AWS identity verified | Pass |
| Instance found | Pass |
| Instance stopped | Pass |
| Final state = stopped | Pass |
| Terraform state preserved | Pass |
| No destroy executed | Pass |
| Shutdown report created | Pass |

---

## Scope Compliance

- `terraform destroy` **not** executed
- EC2 instance **not** deleted
- Security group **not** deleted
- No Terraform or application code modified
- No commit or push
- PAPE not declared

---

## Can We Continue From Home?

**Yes.**

Infrastructure is preserved in stopped state. Start the instance when ready, refresh public IP, and resume PE validation.
