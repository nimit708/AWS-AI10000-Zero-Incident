# Quick Start Guide - CloudFormation Deployment

## TL;DR - Deploy in 5 Steps

### 1. Package Lambda Code

**Windows (PowerShell):**
```powershell
.\package-lambda.ps1
```

**Linux/Mac:**
```bash
chmod +x package-lambda.sh
./package-lambda.sh
```

This creates `lambda-package.zip` (~5-10 MB)

### 2. Deploy CloudFormation Stack

1. Go to: https://console.aws.amazon.com/cloudformation
2. Click "Create stack" → "With new resources"
3. Upload `cloudformation-template.yaml`
4. Stack name: `IncidentManagementStack`
5. Email: `sharmanimit18@outlook.com`
6. Click through and "Submit"
7. Wait 5-10 minutes for "CREATE_COMPLETE"

### 3. Confirm Email Subscriptions

Check your email and confirm 2 SNS subscriptions

### 4. Update IngestionLambda Environment

```bash
# Run the update script
./update-ingestion-lambda.sh   # Linux/Mac
.\update-ingestion-lambda.ps1  # Windows
```

### 5. Update Lambda Code

**Option A - Via AWS Console:**
- Go to Lambda Console
- For each function, upload `lambda-package.zip`

**Option B - Via AWS CLI:**
```bash
# Update all 9 Lambda functions
for func in IngestionLambda DLQProcessorLambda PatternMatcherLambda EC2RemediationLambda LambdaRemediationLambda SSLRemediationLambda NetworkRemediationLambda DeploymentRemediationLambda ServiceRemediationLambda; do
    aws lambda update-function-code --function-name $func --zip-file fileb://lambda-package.zip
done
```

### 5. Test the System

```bash
aws lambda invoke \
  --function-name IngestionLambda \
  --payload '{"incident_id":"test-001","event_type":"EC2 CPU Spike","severity":"high"}' \
  response.json
```

## What Gets Created

- 2 DynamoDB tables (incident tracking + resource locks)
- 1 S3 bucket (knowledge base)
- 2 SNS topics (summary + urgent alerts)
- 1 SQS queue (dead letter queue)
- 9 Lambda functions (ingestion + remediation)
- 1 Step Functions state machine
- 5 CloudWatch alarms
- 2 IAM roles

## Stack Outputs

After deployment, get important ARNs:

```bash
aws cloudformation describe-stacks \
  --stack-name IncidentManagementStack \
  --query 'Stacks[0].Outputs'
```

## Cleanup

```bash
aws cloudformation delete-stack --stack-name IncidentManagementStack
```

## Need More Details?

See `CLOUDFORMATION_DEPLOYMENT.md` for comprehensive instructions.

## Troubleshooting

**Stack creation fails:**
- Check CloudFormation Events tab
- Verify IAM permissions
- Ensure you're in us-east-1 region

**Lambda not working:**
- Check CloudWatch Logs: `/aws/lambda/<FunctionName>`
- Verify code was uploaded
- Check environment variables

**No email notifications:**
- Confirm SNS subscriptions in email
- Check spam folder

## Cost Estimate

~$27-102/month depending on usage

## Support

For issues, check:
1. CloudFormation Events tab
2. CloudWatch Logs
3. Lambda function configuration
4. IAM role permissions
