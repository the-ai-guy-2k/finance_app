# SPE-01 Validation Checklist

Post-apply validation for AIQ-PE-01 / SPE-01. Complete after DWN TVR approval and successful `terraform apply`.

## Pre-Validation

- [ ] Terraform apply completed without errors
- [ ] `terraform output app_url` returns an HTTP URL
- [ ] `OPENAI_API_KEY` was provided at apply time **or** set manually in `/opt/financial-app/env` on the instance

Record outputs:

```
Instance ID: ____________________
Public IP:     ____________________
App URL:       ____________________
Date/Time:     ____________________
Operator:      ____________________
```

## 1. Infrastructure — Terraform Plan Success

- [ ] `terraform plan -var-file=terraform.tfvars` shows no unexpected changes (or only expected drift)
- [ ] Only expected resources exist: 1 EC2 instance, 1 security group
- [ ] No RDS, ALB, Route 53, CloudFront, ECS, EKS, NAT Gateway, or other disallowed resources were created

Verify in AWS Console or CLI:

```powershell
aws ec2 describe-instances --profile nebula --region us-east-1 --filters "Name=tag:Environment,Values=spe-01"
```

## 2. Network Access — HTTP

- [ ] Browser loads `http://<public_ip>` without connection timeout
- [ ] Financial App dashboard or home page renders (status 200)
- [ ] No HTTPS required for this PE (plain HTTP is expected)

## 3. Network Access — SSH

- [ ] SSH connects as `ec2-user`:

```powershell
ssh -i <your-key.pem> ec2-user@<public_ip>
```

- [ ] `sudo systemctl status financial-app` shows `active (running)`
- [ ] `sudo docker ps` shows `financial-app` container on `0.0.0.0:80->5000/tcp`

## 4. Docker Runtime

- [ ] Bootstrap log exists: `/var/log/financial-app-bootstrap.log`
- [ ] Docker image pulled: `taig2k/finance_app_for_aws:latest` (or configured tag)
- [ ] Container restarts on reboot (systemd enabled):

```bash
sudo systemctl is-enabled financial-app
```

## 5. OpenAI Integration

- [ ] `OPENAI_API_KEY` is set in container environment (do not print the value):

```bash
sudo docker inspect financial-app --format '{{range .Config.Env}}{{println .}}{{end}}' | grep OPENAI_API_KEY=
```

- [ ] Key is non-empty (output shows `OPENAI_API_KEY=sk-...` with value redacted in notes)

### Functional test — AI insight generation

1. Open the app in a browser (`terraform output app_url`)
2. Add at least one transaction (manual entry or CSV upload)
3. Navigate to insights / generate insights
4. Confirm AI-generated financial insight appears (not only heuristic fallback text)

Expected success indicators:

- Insight text references spending patterns or behavioral observations
- App logs show OpenAI usage (on instance):

```bash
sudo tail -20 /opt/financial-app/logs/app.log
```

Look for: `OpenAI API key loaded from OPENAI_API_KEY environment variable` and `Behavioral insights generated via OpenAI`

Expected failure (needs remediation):

- Insight shows only "heuristic" / "Full insights require OpenAI API access"
- Logs show `API_KEY_ERROR` or `OPENAI_API_ERROR`

## 6. Security — No Secrets Committed

- [ ] `terraform.tfvars` is not tracked in git
- [ ] No API keys in Terraform state committed to repository (state should remain local unless remote backend is configured separately)
- [ ] `/opt/financial-app/env` is mode `600` on the instance

## 7. Service Flow (End-to-End)

| Step | Verified |
|------|----------|
| User accesses app over internet | [ ] |
| User submits financial data | [ ] |
| App sends request to OpenAI | [ ] |
| OpenAI returns analysis | [ ] |
| App displays meaningful financial insight | [ ] |

## 8. Operability

- [ ] Instance can be stopped without data loss on EBS volumes
- [ ] Instance can be started again and app recovers
- [ ] Operator can view logs via SSH and `journalctl`

## Validation Result

| Outcome | Notes |
|---------|-------|
| PASS / FAIL | |

If **FAIL**, document:

- Failure step: ____________________
- Error message / symptom: ____________________
- Remediation taken: ____________________

## Sign-Off

| Role | Name | Date |
|------|------|------|
| Operator | | |
| DWN (optional) | | |

After validation, destroy or stop the PE per `CLEANUP.md` when no longer needed.
