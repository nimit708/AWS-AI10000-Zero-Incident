# CloudFormation Deployment Guide

## Overview

This guide explains how to deploy the AWS Incident Management System using the CloudFormation template directly via the AWS Console.

## Important Note About Lambda Code

The CloudFormation template includes placeholder code for all Lambda functions. For a production deployment, you'll need to:

1. Package your Lambda code
2. Upload it to S3
3. Update the Lambda function code after stack creation

## Deployment Steps

### Step 1: Prepare the Template

The CloudFormation template is located at: `cloudformation-template.yaml`

### Step 2: Deploy via AWS Console

1. **Open AWS CloudFormation Console**
   - Navigate to: https://console.aws.amazon.com/cloudformation
   - Ensure you're in the `eu-west-2` region (or your preferred region)

2. **Create Stack**
   - Click "Create stack" → "With new resources (standard)"
   - Choose "Upload a template file"
   - Click "Choose file" and select `cloudformation-template.yaml`
   - Click "Next"

3. **Specify Stack Details**
   - Stack name: `IncidentManagementStack`
   - Parameters:
     - NotificationEmail: `sharmanimit18@outlook.com` (or your email)
     - BedrockAgentModel: `anthropic.claude-3-5-sonnet-20241022-v2:0`
     - BedrockEmbeddingModel: `amazon.titan-embed-text-v2:0`
     - BedrockSummaryModel: `anthropic.claude-3-haiku-20240307-v1:0`
   - Click "Next"

4. **Configure Stack Options**
   - Tags (optional): Add any tags you want
   - Permissions: Leave as default (or specify an IAM role if required)
   - Stack failure options: "Roll back all stack resources"
   - Click "Next"

5. **Review**
   - Review all settings
   - Check the box: "I acknowledge that AWS CloudFormation might create IAM resources"
   - Click "Submit"

6. **Wait for Stack Creation**
   - The stack will take 5-10 minutes to create
   - Monitor the "Events" tab for progress
   - Wait until status shows "CREATE_COMPLETE"


### Step 3: Confirm SNS Email Subscriptions

After stack creation:

1. Check your email inbox for SNS subscription confirmation emails (2 emails)
2. Click "Confirm subscription" in each email
3. You should receive confirmations for:
   - Incident Summary Notifications
   - Incident Urgent Alerts

### Step 4: Update IngestionLambda Environment Variable

Due to circular dependency constraints, the IngestionLambda needs to be updated with the StateMachine ARN after deployment:

**Option A: Run the update script (Recommended)**

Linux/Mac:
```bash
chmod +x update-ingestion-lambda.sh
./update-ingestion-lambda.sh
```

Windows PowerShell:
```powershell
.\update-ingestion-lambda.ps1
```

**Option B: Manual update via AWS CLI**

Get the command from stack outputs:
```bash
aws cloudformation describe-stacks \
  --stack-name IncidentManagementStack \
  --query 'Stacks[0].Outputs[?OutputKey==`UpdateIngestionLambdaCommand`].OutputValue' \
  --output text
```

Then run the displayed command.

### Step 5: Update Lambda Function Code

The Lambda functions are created with placeholder code. To deploy actual code:

#### Option A: Manual Update via Console

1. **Prepare Lambda Package**
   ```bash
   # Create a deployment package
   zip -r lambda-package.zip . -x "tests/*" "*.md" "infrastructure/*" "node_modules/*" ".git/*" ".kiro/*" "cdk.out/*"
   ```

2. **Update Each Lambda Function**
   - Go to AWS Lambda Console
   - For each function (IngestionLambda, DLQProcessorLambda, etc.):
     - Click on the function name
     - Go to "Code" tab
     - Click "Upload from" → ".zip file"
     - Upload `lambda-package.zip`
     - Click "Save"

#### Option B: Update via AWS CLI

```bash
# Package the code
zip -r lambda-package.zip . -x "tests/*" "*.md" "infrastructure/*" "node_modules/*" ".git/*" ".kiro/*" "cdk.out/*"

# Update each Lambda function
aws lambda update-function-code --function-name IngestionLambda --zip-file fileb://lambda-package.zip
aws lambda update-function-code --function-name DLQProcessorLambda --zip-file fileb://lambda-package.zip
aws lambda update-function-code --function-name PatternMatcherLambda --zip-file fileb://lambda-package.zip
aws lambda update-function-code --function-name EC2RemediationLambda --zip-file fileb://lambda-package.zip
aws lambda update-function-code --function-name LambdaRemediationLambda --zip-file fileb://lambda-package.zip
aws lambda update-function-code --function-name SSLRemediationLambda --zip-file fileb://lambda-package.zip
aws lambda update-function-code --function-name NetworkRemediationLambda --zip-file fileb://lambda-package.zip
aws lambda update-function-code --function-name DeploymentRemediationLambda --zip-file fileb://lambda-package.zip
aws lambda update-function-code --function-name ServiceRemediationLambda --zip-file fileb://lambda-package.zip
```

#### Option C: Update via S3 (Recommended for Large Packages)

```bash
# Create S3 bucket for deployment
aws s3 mb s3://incident-management-deployment-923906573163

# Package and upload
zip -r lambda-package.zip . -x "tests/*" "*.md" "infrastructure/*" "node_modules/*" ".git/*" ".kiro/*" "cdk.out/*"
aws s3 cp lambda-package.zip s3://incident-management-deployment-923906573163/

# Update each Lambda function
aws lambda update-function-code --function-name IngestionLambda --s3-bucket incident-management-deployment-923906573163 --s3-key lambda-package.zip
aws lambda update-function-code --function-name DLQProcessorLambda --s3-bucket incident-management-deployment-923906573163 --s3-key lambda-package.zip
aws lambda update-function-code --function-name PatternMatcherLambda --s3-bucket incident-management-deployment-923906573163 --s3-key lambda-package.zip
aws lambda update-function-code --function-name EC2RemediationLambda --s3-bucket incident-management-deployment-923906573163 --s3-key lambda-package.zip
aws lambda update-function-code --function-name LambdaRemediationLambda --s3-bucket incident-management-deployment-923906573163 --s3-key lambda-package.zip
aws lambda update-function-code --function-name SSLRemediationLambda --s3-bucket incident-management-deployment-923906573163 --s3-key lambda-package.zip
aws lambda update-function-code --function-name NetworkRemediationLambda --s3-bucket incident-management-deployment-923906573163 --s3-key lambda-package.zip
aws lambda update-function-code --function-name DeploymentRemediationLambda --s3-bucket incident-management-deployment-923906573163 --s3-key lambda-package.zip
aws lambda update-function-code --function-name ServiceRemediationLambda --s3-bucket incident-management-deployment-923906573163 --s3-key lambda-package.zip
```


## Stack Resources Created

The CloudFormation stack creates the following resources:

### DynamoDB Tables
- **IncidentTrackingTable**: Stores incident records with GSIs for status and event_type
- **ResourceLockTable**: Manages resource locking for concurrent operations

### S3 Buckets
- **KnowledgeBaseBucket**: Stores historical incident data for AI knowledge base

### SNS Topics
- **IncidentSummaryTopic**: Summary notifications
- **IncidentUrgentTopic**: Urgent alerts

### SQS Queues
- **IncidentDLQ**: Dead letter queue for failed incidents

### Lambda Functions (9 total)
1. **IngestionLambda**: Main entry point for incident processing
2. **DLQProcessorLambda**: Processes failed incidents from DLQ
3. **PatternMatcherLambda**: Evaluates incident patterns
4. **EC2RemediationLambda**: Handles EC2 CPU/Memory spike incidents
5. **LambdaRemediationLambda**: Handles Lambda timeout incidents
6. **SSLRemediationLambda**: Handles SSL certificate errors
7. **NetworkRemediationLambda**: Handles network timeout incidents
8. **DeploymentRemediationLambda**: Handles deployment failures
9. **ServiceRemediationLambda**: Handles service health issues

### Step Functions
- **RemediationStateMachine**: Orchestrates pattern-based remediation workflow

### CloudWatch Alarms (5 total)
- High remediation failure rate
- High DLQ message count
- Lambda errors
- High processing latency
- High escalation rate

### IAM Roles
- **LambdaExecutionRole**: Execution role for all Lambda functions
- **StepFunctionsExecutionRole**: Execution role for Step Functions

## Verification Steps

After deployment and code update:

1. **Check Stack Outputs**
   ```bash
   aws cloudformation describe-stacks --stack-name IncidentManagementStack --query 'Stacks[0].Outputs'
   ```

2. **Test Ingestion Lambda**
   ```bash
   aws lambda invoke --function-name IngestionLambda --payload '{"test": "event"}' response.json
   cat response.json
   ```

3. **Check DynamoDB Tables**
   ```bash
   aws dynamodb describe-table --table-name incident-tracking-table
   aws dynamodb describe-table --table-name resource-lock-table
   ```

4. **Verify Step Functions**
   ```bash
   aws stepfunctions describe-state-machine --state-machine-arn <StateMachineArn>
   ```

5. **Check CloudWatch Logs**
   - Navigate to CloudWatch Logs in AWS Console
   - Look for log groups: `/aws/lambda/*` and `/aws/states/RemediationStateMachine`

## Testing the System

### Test Incident Ingestion

Create a test incident event:

```bash
aws lambda invoke \
  --function-name IngestionLambda \
  --payload '{
    "incident_id": "test-001",
    "event_type": "EC2 CPU Spike",
    "severity": "high",
    "resource_id": "i-1234567890abcdef0",
    "description": "EC2 instance CPU usage exceeded 90%",
    "timestamp": 1234567890
  }' \
  response.json

cat response.json
```

### Monitor Execution

1. Check Step Functions execution in AWS Console
2. Monitor CloudWatch Logs for each Lambda function
3. Check SNS notifications in your email
4. Verify DynamoDB records

## Cleanup

To delete all resources:

```bash
# Delete the CloudFormation stack
aws cloudformation delete-stack --stack-name IncidentManagementStack

# Wait for deletion to complete
aws cloudformation wait stack-delete-complete --stack-name IncidentManagementStack

# If you created a deployment bucket, delete it
aws s3 rb s3://incident-management-deployment-923906573163 --force
```

## Troubleshooting

### Stack Creation Fails

- Check CloudFormation Events tab for error messages
- Verify IAM permissions
- Ensure Bedrock models are available in your region

### Lambda Functions Not Working

- Verify code was uploaded correctly
- Check CloudWatch Logs for errors
- Verify environment variables are set correctly
- Ensure IAM role has necessary permissions

### SNS Notifications Not Received

- Confirm email subscriptions
- Check SNS topic permissions
- Verify Lambda has permission to publish to SNS

### Step Functions Execution Fails

- Check CloudWatch Logs for state machine
- Verify Lambda functions are working
- Check IAM role permissions for Step Functions

## Cost Estimation

Approximate monthly costs (assuming moderate usage):

- DynamoDB: $5-20 (pay per request)
- Lambda: $10-50 (based on invocations)
- Step Functions: $5-15 (based on state transitions)
- S3: $1-5 (storage and requests)
- CloudWatch: $5-10 (logs and metrics)
- SNS: $1-2 (notifications)

**Total estimated cost: $27-102/month**

Note: Actual costs depend on usage patterns and data volume.
