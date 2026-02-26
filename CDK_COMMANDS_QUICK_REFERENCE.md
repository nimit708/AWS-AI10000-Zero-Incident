# CDK Commands - Quick Reference

## Essential Commands (In Order)

### 1. Verify Setup
```bash
aws sts get-caller-identity
python --version
cdk --version
```

### 2. Install Dependencies
```bash
pip install -r cdk-requirements.txt
pip install -r requirements.txt
```

### 3. Bootstrap CDK (First Time Only)
```bash
cdk bootstrap aws://923906573163/eu-west-2
```

### 4. Synthesize Template
```bash
cdk synth
```

### 5. Preview Changes
```bash
cdk diff
```

### 6. Deploy Stack
```bash
cdk deploy
```

Or with auto-approval:
```bash
cdk deploy --require-approval never
```

### 7. Get Stack Outputs
```bash
aws cloudformation describe-stacks \
  --stack-name IncidentManagementStack \
  --query 'Stacks[0].Outputs'
```

### 8. Test Deployment
```bash
aws lambda invoke \
  --function-name IngestionLambda \
  --payload '{"test":"event"}' \
  response.json
```

## One-Line Deployment

```bash
# Linux/Mac
./deploy-cdk.sh

# Windows PowerShell
.\deploy-cdk.ps1
```

## Useful Commands

### List Stacks
```bash
cdk list
```

### Watch Deployment Progress
```bash
# In another terminal
aws cloudformation describe-stack-events \
  --stack-name IncidentManagementStack \
  --max-items 10
```

### View Synthesized Template
```bash
cdk synth > template.yaml
cat template.yaml
```

### Update Existing Stack
```bash
cdk diff
cdk deploy
```

### Destroy Stack
```bash
cdk destroy
```

Or with auto-approval:
```bash
cdk destroy --force
```

## Troubleshooting Commands

### Clear CDK Cache
```bash
rm -rf cdk.out
cdk synth
```

### Verbose Output
```bash
cdk synth --verbose
cdk deploy --verbose
```

### Check Bootstrap Status
```bash
aws cloudformation describe-stacks \
  --stack-name CDKToolkit
```

### View Lambda Functions
```bash
aws lambda list-functions \
  --query 'Functions[*].FunctionName'
```

### View DynamoDB Tables
```bash
aws dynamodb list-tables
```

### View S3 Buckets
```bash
aws s3 ls | grep incident
```

### View Step Functions
```bash
aws stepfunctions list-state-machines
```

### Check CloudWatch Logs
```bash
aws logs describe-log-groups \
  --log-group-name-prefix /aws/lambda/
```

## Windows PowerShell Equivalents

### Deploy
```powershell
cdk deploy --require-approval never
```

### Get Outputs
```powershell
aws cloudformation describe-stacks `
  --stack-name IncidentManagementStack `
  --query 'Stacks[0].Outputs'
```

### Test Lambda
```powershell
aws lambda invoke `
  --function-name IngestionLambda `
  --payload '{\"test\":\"event\"}' `
  response.json
```

## Environment Variables (Optional)

Set these if needed:

```bash
export CDK_DEFAULT_ACCOUNT=923906573163
export CDK_DEFAULT_REGION=eu-west-2
export AWS_REGION=eu-west-2
```

Windows PowerShell:
```powershell
$env:CDK_DEFAULT_ACCOUNT="923906573163"
$env:CDK_DEFAULT_REGION="eu-west-2"
$env:AWS_REGION="eu-west-2"
```

## Common Issues & Solutions

### Issue: `cdk synth` hangs
**Solution:**
```bash
# Remove lock file
rm cdk.out/synth.lock
# Try again
cdk synth
```

### Issue: Bootstrap error
**Solution:**
```bash
# Re-bootstrap
cdk bootstrap aws://923906573163/eu-west-2 --force
```

### Issue: Deployment fails
**Solution:**
```bash
# Check CloudFormation events
aws cloudformation describe-stack-events \
  --stack-name IncidentManagementStack \
  --max-items 20
```

### Issue: Lambda code not updated
**Solution:**
CDK automatically packages code. If you make changes:
```bash
cdk deploy
```

## Deployment Timeline

- Bootstrap: 2-3 minutes (first time only)
- Synth: 30 seconds - 2 minutes
- Deploy: 10-15 minutes
- **Total: 12-20 minutes**

## Post-Deployment Checklist

- [ ] Confirm SNS email subscriptions (2 emails)
- [ ] Test ingestion Lambda
- [ ] Check CloudWatch Logs
- [ ] Verify DynamoDB tables created
- [ ] Verify S3 bucket created
- [ ] Test Step Functions execution

## Cost Estimate

~$27-102/month depending on usage

## Support Files

- `CDK_MANUAL_DEPLOYMENT.md` - Detailed guide
- `deploy-cdk.sh` - Automated deployment (Linux/Mac)
- `deploy-cdk.ps1` - Automated deployment (Windows)
- `DEPLOYMENT.md` - Original deployment guide
- `.cdkignore` - Files excluded from Lambda packages

---

**Ready to deploy? Run: `./deploy-cdk.sh` or `.\deploy-cdk.ps1`**
