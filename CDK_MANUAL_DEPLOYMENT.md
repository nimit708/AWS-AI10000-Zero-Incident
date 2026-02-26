# CDK Manual Deployment Guide

## Prerequisites

Ensure you have:
- AWS CLI configured (Account: 923906573163, Region: us-east-1)
- Python 3.11+ installed
- Node.js and npm installed
- CDK CLI installed globally

## Step-by-Step Commands

### 1. Verify Prerequisites

```bash
# Check AWS CLI configuration
aws sts get-caller-identity

# Check Python version
python --version

# Check Node.js version
node --version

# Check CDK version
cdk --version
```

Expected output:
- AWS Account: 923906573163
- Python: 3.11 or higher
- Node.js: 18+ or higher
- CDK: 2.100.0 or higher

### 2. Install Python Dependencies

```bash
# Install CDK requirements
pip install -r cdk-requirements.txt

# Install application requirements (needed for Lambda packaging)
pip install -r requirements.txt
```

### 3. Bootstrap CDK (First Time Only)

If you haven't used CDK in this account/region before:

```bash
cdk bootstrap aws://923906573163/eu-west-2
```

This creates an S3 bucket and other resources needed for CDK deployments.

### 4. Synthesize CloudFormation Template

```bash
# Generate CloudFormation template
cdk synth

# This creates the template in cdk.out/ directory
# You should see output showing the CloudFormation template
```

If this hangs, press Ctrl+C and try:

```bash
# Alternative: Use Python directly
python app.py
```

### 5. Review What Will Be Deployed

```bash
# See what changes will be made
cdk diff
```

This shows you all resources that will be created.

### 6. Deploy the Stack

```bash
# Deploy everything
cdk deploy

# Or with auto-approval (no confirmation prompts)
cdk deploy --require-approval never
```

During deployment:
- CDK will package Lambda code automatically
- Upload assets to S3
- Create all infrastructure resources
- This takes 10-15 minutes

### 7. Confirm SNS Email Subscriptions

After deployment completes:
1. Check your email (sharmanimit18@outlook.com)
2. You'll receive 2 subscription confirmation emails
3. Click "Confirm subscription" in each email

### 8. Get Stack Outputs

```bash
# View all stack outputs
cdk deploy --outputs-file outputs.json

# Or use AWS CLI
aws cloudformation describe-stacks \
  --stack-name IncidentManagementStack \
  --query 'Stacks[0].Outputs'
```

### 9. Test the Deployment

```bash
# Get the Lambda function name from outputs
LAMBDA_ARN=$(aws cloudformation describe-stacks \
  --stack-name IncidentManagementStack \
  --query 'Stacks[0].Outputs[?OutputKey==`IngestionLambdaArn`].OutputValue' \
  --output text)

# Test the ingestion Lambda
aws lambda invoke \
  --function-name IngestionLambda \
  --payload '{"incident_id":"test-001","event_type":"EC2 CPU Spike","severity":"high","resource_id":"i-test123","description":"Test incident","timestamp":1234567890}' \
  response.json

# Check the response
cat response.json
```

## Alternative Commands (If Main Commands Fail)

### If `cdk synth` hangs:

```bash
# Try with verbose output
cdk synth --verbose

# Or use Python directly
python app.py > /dev/null 2>&1 &

# Check if cdk.out directory is created
ls -la cdk.out/
```

### If `cdk deploy` hangs:

```bash
# Try deploying with CloudFormation directly
cdk synth > template.yaml
aws cloudformation create-stack \
  --stack-name IncidentManagementStack \
  --template-body file://template.yaml \
  --capabilities CAPABILITY_NAMED_IAM
```

### If Lambda packaging is slow:

The `.cdkignore` file should exclude unnecessary files. Verify it exists:

```bash
cat .cdkignore
```

## Troubleshooting Commands

### Check CDK Context

```bash
# View CDK context
cdk context

# Clear CDK context if needed
cdk context --clear
```

### Check for Existing Stacks

```bash
# List all CDK stacks
cdk list

# Check if stack already exists
aws cloudformation describe-stacks --stack-name IncidentManagementStack
```

### View CloudFormation Events

```bash
# Monitor stack creation in real-time
aws cloudformation describe-stack-events \
  --stack-name IncidentManagementStack \
  --max-items 20
```

### Check Lambda Functions

```bash
# List all Lambda functions
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `Incident`) || starts_with(FunctionName, `Ingestion`) || starts_with(FunctionName, `DLQ`) || starts_with(FunctionName, `Pattern`) || starts_with(FunctionName, `EC2`) || starts_with(FunctionName, `Lambda`) || starts_with(FunctionName, `SSL`) || starts_with(FunctionName, `Network`) || starts_with(FunctionName, `Deployment`) || starts_with(FunctionName, `Service`)].FunctionName'
```

### Check DynamoDB Tables

```bash
# List tables
aws dynamodb list-tables

# Describe incident table
aws dynamodb describe-table --table-name incident-tracking-table
```

### Check S3 Buckets

```bash
# List buckets (look for incident-kb-*)
aws s3 ls | grep incident
```

### Check Step Functions

```bash
# List state machines
aws stepfunctions list-state-machines
```

## Update Existing Stack

If you need to update the stack after making changes:

```bash
# See what will change
cdk diff

# Deploy updates
cdk deploy
```

## Destroy Stack

To remove all resources:

```bash
# Destroy the stack
cdk destroy

# Or with auto-approval
cdk destroy --force
```

## Complete Deployment Script

Here's a complete script you can run:

```bash
#!/bin/bash

echo "Starting CDK deployment..."

# 1. Verify prerequisites
echo "Checking prerequisites..."
aws sts get-caller-identity || exit 1
python --version || exit 1
cdk --version || exit 1

# 2. Install dependencies
echo "Installing dependencies..."
pip install -r cdk-requirements.txt
pip install -r requirements.txt

# 3. Bootstrap (if needed)
echo "Bootstrapping CDK..."
cdk bootstrap aws://923906573163/us-east-1

# 4. Synthesize
echo "Synthesizing CloudFormation template..."
cdk synth

# 5. Deploy
echo "Deploying stack..."
cdk deploy --require-approval never

# 6. Get outputs
echo "Getting stack outputs..."
aws cloudformation describe-stacks \
  --stack-name IncidentManagementStack \
  --query 'Stacks[0].Outputs'

echo "Deployment complete!"
echo "Don't forget to confirm SNS email subscriptions!"
```

Save this as `deploy-cdk.sh` and run:

```bash
chmod +x deploy-cdk.sh
./deploy-cdk.sh
```

## Windows PowerShell Version

```powershell
# deploy-cdk.ps1

Write-Host "Starting CDK deployment..." -ForegroundColor Green

# 1. Verify prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow
aws sts get-caller-identity
if ($LASTEXITCODE -ne 0) { exit 1 }

python --version
cdk --version

# 2. Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r cdk-requirements.txt
pip install -r requirements.txt

# 3. Bootstrap (if needed)
Write-Host "Bootstrapping CDK..." -ForegroundColor Yellow
cdk bootstrap aws://923906573163/us-east-1

# 4. Synthesize
Write-Host "Synthesizing CloudFormation template..." -ForegroundColor Yellow
cdk synth

# 5. Deploy
Write-Host "Deploying stack..." -ForegroundColor Yellow
cdk deploy --require-approval never

# 6. Get outputs
Write-Host "Getting stack outputs..." -ForegroundColor Yellow
aws cloudformation describe-stacks `
  --stack-name IncidentManagementStack `
  --query 'Stacks[0].Outputs'

Write-Host "Deployment complete!" -ForegroundColor Green
Write-Host "Don't forget to confirm SNS email subscriptions!" -ForegroundColor Cyan
```

## Key Points

1. **CDK automatically packages Lambda code** - No need to manually zip files
2. **`.cdkignore` excludes unnecessary files** - Tests, docs, etc. are not included
3. **Bootstrap only needed once** - Per account/region combination
4. **Deployment takes 10-15 minutes** - Be patient
5. **Email confirmation required** - Check your inbox after deployment

## Expected Output

Successful deployment will show:

```
✅  IncidentManagementStack

Outputs:
IncidentManagementStack.IncidentTableName = incident-tracking-table
IncidentManagementStack.ResourceLockTableName = resource-lock-table
IncidentManagementStack.KnowledgeBaseBucketName = incident-kb-923906573163
IncidentManagementStack.IngestionLambdaArn = arn:aws:lambda:us-east-1:923906573163:function:IngestionLambda
IncidentManagementStack.StateMachineArn = arn:aws:states:us-east-1:923906573163:stateMachine:RemediationStateMachine
IncidentManagementStack.SummaryTopicArn = arn:aws:sns:us-east-1:923906573163:incident-summary-topic
IncidentManagementStack.UrgentTopicArn = arn:aws:sns:us-east-1:923906573163:incident-urgent-topic

Stack ARN:
arn:aws:cloudformation:us-east-1:923906573163:stack/IncidentManagementStack/...
```

## Next Steps After Deployment

1. Confirm SNS email subscriptions
2. Test the ingestion Lambda
3. Monitor CloudWatch Logs
4. Verify DynamoDB tables
5. Test Step Functions execution

Good luck with your deployment!
