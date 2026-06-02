# SPE-01 Cleanup Guide

Instructions to stop or destroy the SPE-01 Production Environment after validation or when the demo is complete.

## Option A — Stop Instance (Preserve Data, Reduce Cost)

Stops EC2 billing for compute while keeping the EBS volume and configuration. Useful for pausing between demo sessions.

```powershell
cd terraform/spe-01

# Get instance ID
terraform output instance_id

# Stop via AWS CLI
aws ec2 stop-instances --profile nebula --region us-east-1 --instance-ids <instance-id>
```

To restart:

```powershell
aws ec2 start-instances --profile nebula --region us-east-1 --instance-ids <instance-id>
```

Wait for the instance to reach `running`, then verify the app:

```powershell
terraform output app_url
```

Note: Public IP may change after stop/start unless you attach an Elastic IP (not provisioned by this artifact — intentional).

## Option B — Destroy All SPE-01 Resources (Recommended when done)

Removes the EC2 instance, security group, and EBS volume created by this Terraform package.

```powershell
cd terraform/spe-01

# Ensure the same variables used at apply time
$env:TF_VAR_openai_api_key = "sk-your-key-here"   # if originally passed via env var
terraform destroy -var-file=terraform.tfvars
```

Or without re-supplying the API key (destroy does not need a valid key unless user_data triggers replacement):

```powershell
terraform destroy -var-file=terraform.tfvars
```

Confirm the prompt. Expected destroyed resources:

- `aws_instance.spe01`
- `aws_security_group.spe01`

## Post-Destroy Verification

- [ ] `terraform show` reports no managed resources (or run `terraform state list` — empty)
- [ ] EC2 console shows no instance tagged `Environment = spe-01`
- [ ] Security group `financial-app-spe-01-sg` (or similar) is removed
- [ ] No orphaned EBS volumes from this PE (check EC2 → Volumes, filter by tag)

```powershell
aws ec2 describe-instances --profile nebula --region us-east-1 --filters "Name=tag:Environment,Values=spe-01" "Name=instance-state-name,Values=running,pending,stopping,stopped"
```

Should return no instances.

## Local Cleanup

Remove Terraform working files if desired (optional):

```powershell
Remove-Item -Recurse -Force .terraform -ErrorAction SilentlyContinue
Remove-Item terraform.tfstate* -ErrorAction SilentlyContinue
Remove-Item terraform.tfvars -ErrorAction SilentlyContinue
```

**Do not commit** `terraform.tfvars`, `*.tfstate`, or `.terraform/` to source control.

## Secrets After Teardown

- Rotate or revoke the OpenAI API key if it was exposed during testing on a shared PE
- Clear shell history if the key was passed via `-var` on a shared machine:

```powershell
# PowerShell: review and clear if needed
Get-History
```

## Cost Confirmation

After destroy:

- [ ] No running EC2 instances for SPE-01
- [ ] No attached EBS volumes incurring storage charges from this PE
- [ ] No NAT Gateway or other disallowed paid resources remain

## Emergency Manual Cleanup

If Terraform state is lost but the instance still exists:

```powershell
# Find the instance
aws ec2 describe-instances --profile nebula --region us-east-1 --filters "Name=tag:Environment,Values=spe-01"

# Terminate (replace i-xxxxxxxx)
aws ec2 terminate-instances --profile nebula --region us-east-1 --instance-ids i-xxxxxxxx

# Delete security group after instance terminates
aws ec2 delete-security-group --profile nebula --region us-east-1 --group-id sg-xxxxxxxx
```

Document any manual cleanup in the operator log for DWN review.
