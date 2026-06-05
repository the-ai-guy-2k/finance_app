# ACI-PE-08 — Financial App SPE-01 Shutdown

**Project:** Financial App  
**Date:** 2026-06-02  
**Mission:** Stop SPE-01 EC2 to control AWS cost while preserving infrastructure  
**PAPE:** Deferred (unchanged)

---

## Executive Summary

SPE-01 EC2 instance **`i-0055c22499e9b2853`** (`financial-app-spe-01`) was **stopped successfully**. No resources were destroyed. Terraform state, security groups, SSM parameters, and key pairs remain intact.

---

## 1. AWS Identity

| Field | Value |
|-------|--------|
| Account | `526123657916` |
| User | `nebula` |
| ARN | `arn:aws:iam::526123657916:user/nebula` |

---

## 2. Instance Located

| Field | Value |
|-------|--------|
| **Instance ID** | `i-0055c22499e9b2853` |
| **Name** | `financial-app-spe-01` |
| **Environment tag** | `spe-01` |
| **Region** | `us-east-1` |
| **Instance type** | `t3.micro` |
| **AMI** | `ami-074bb5e3c681b0735` |
| **Launch time** | `2026-06-04T19:29:48+00:00` |

---

## 3. State Before Shutdown

| Field | Value |
|-------|--------|
| **Previous state** | `running` |
| **Public IP** | `44.192.97.51` |
| **App URL** | http://44.192.97.51 |
| **HTTP status (pre-stop)** | `200` |
| **Deployed image (last PE)** | `taig2k/finance_app_for_aws:124d790aa19ddf6592fcd1bbb016275c60bcb683` (Receipt Intelligence v2, ACI-PE-07) |

---

## 4. Stop Operation

| Step | Result |
|------|--------|
| Command | `aws ec2 stop-instances --profile nebula --region us-east-1 --instance-ids i-0055c22499e9b2853` |
| Immediate state | `stopping` (from `running`) |
| Wait | `aws ec2 wait instance-stopped` — **completed** |
| **Final state** | **`stopped`** |
| Public IP while stopped | `null` (released) |

---

## 5. Post-Shutdown Verification

| Check | Result |
|-------|--------|
| Instance `i-0055c22499e9b2853` state | **`stopped`** |
| Running instances with `Environment=spe-01` | **None** (`[]`) |
| `terraform destroy` | **Not run** |
| EC2 / SG / SSM / key pair deleted | **No** |
| Application or Terraform code modified | **No** |

---

## 6. Success Criteria

| Criterion | Status |
|-----------|--------|
| AWS identity confirmed | **Pass** |
| SPE-01 instance located | **Pass** |
| Current state recorded | **Pass** |
| Instance stopped | **Pass** |
| Stopped state verified | **Pass** |
| No destroy performed | **Pass** |
| Report created | **Pass** |

---

## 7. Resume Instructions

1. **Start the instance:**
   ```powershell
   aws ec2 start-instances --profile nebula --region us-east-1 --instance-ids i-0055c22499e9b2853
   aws ec2 wait instance-running --profile nebula --region us-east-1 --instance-ids i-0055c22499e9b2853
   ```

2. **Get the new public IP** (may change after stop/start):
   ```powershell
   aws ec2 describe-instances --profile nebula --region us-east-1 --instance-ids i-0055c22499e9b2853 --query "Reservations[0].Instances[0].PublicIpAddress" --output text
   ```

3. **Verify the app** (after ~1–2 minutes for Docker/systemd):
   ```powershell
   curl http://<new-public-ip>/
   python scripts/pe01_validate.py http://<new-public-ip>
   ```

4. **Optional:** If the container did not auto-start, SSH in and run:
   ```bash
   sudo systemctl status financial-app
   sudo systemctl restart financial-app
   ```

5. **Do not run `terraform destroy`** unless explicitly approved for full cleanup (`terraform/spe-01/CLEANUP.md`).

**Note:** EBS volume and `/opt/financial-app` data persist on the stopped instance; Receipt Intelligence v2 image and data should remain unless the instance is replaced.

---

## Scope Compliance

- [x] Shutdown only
- [x] No destroy
- [x] No code or Terraform changes
- [x] Stop point: EC2 verified stopped

---

*End of ACI-PE-08 shutdown report.*
