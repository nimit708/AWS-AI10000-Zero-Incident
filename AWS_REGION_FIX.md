# AWS_REGION Reserved Variable Fix

## The Problem

When deploying the CloudFormation stack, you encountered this error:

```
Resource handler returned message: "Lambda was unable to configure your 
environment variables because the environment variables you have provided 
contains reserved keys that are currently not supported for modification"
```

## Root Cause

`AWS_REGION` is a **reserved Lambda environment variable** that is automatically set by AWS Lambda. You cannot manually set or override it in the Lambda function configuration.

AWS Lambda automatically provides these reserved environment variables:
- `AWS_REGION` - The AWS region where the Lambda function is running
- `AWS_EXECUTION_ENV` - The execution environment
- `AWS_LAMBDA_FUNCTION_NAME` - The function name
- `AWS_LAMBDA_FUNCTION_VERSION` - The function version
- And several others...

## The Solution

I removed `AWS_REGION` from all Lambda function environment variables in:

1. **cloudformation-template.yaml** - Removed from IngestionLambda environment
2. **update-ingestion-lambda.sh** - Removed from update script
3. **update-ingestion-lambda.ps1** - Removed from PowerShell update script
4. **infrastructure/incident_management_stack.py** - Removed from CDK stack

## How to Access the Region in Lambda Code

Your Lambda functions can still access the region through:

### Option 1: Use the AWS_REGION environment variable (read-only)
```python
import os
region = os.environ['AWS_REGION']  # Automatically set by Lambda
```

### Option 2: Use boto3
```python
import boto3
region = boto3.session.Session().region_name
```

### Option 3: Use the Lambda context
```python
def handler(event, context):
    # Extract from function ARN
    arn = context.invoked_function_arn
    region = arn.split(':')[3]
```

## Region Change to eu-west-2

I also updated all references from `us-east-1` to `eu-west-2` as requested:

### Files Updated
1. **app.py** - Default region changed to eu-west-2
2. **deploy-cdk.sh** - Bootstrap command updated
3. **deploy-cdk.ps1** - Bootstrap command updated
4. **CDK_MANUAL_DEPLOYMENT.md** - Documentation updated
5. **CDK_COMMANDS_QUICK_REFERENCE.md** - Commands updated
6. **CLOUDFORMATION_DEPLOYMENT.md** - Region reference updated

## Important Notes

### For CloudFormation Deployment
- Deploy the stack in the **eu-west-2** region
- The Lambda functions will automatically have `AWS_REGION=eu-west-2`
- No need to manually set this variable

### For CDK Deployment
- Bootstrap command: `cdk bootstrap aws://923906573163/eu-west-2`
- The CDK will automatically set the region based on your AWS CLI configuration or the environment specified in app.py

### Bedrock Model Availability
Make sure the Bedrock models are available in eu-west-2:
- `anthropic.claude-3-5-sonnet-20241022-v2:0`
- `amazon.titan-embed-text-v2:0`
- `anthropic.claude-3-haiku-20240307-v1:0`

If these models are not available in eu-west-2, you may need to:
1. Use different model versions available in that region
2. Or deploy to a region where these models are available (like us-east-1)

## Verification

After deployment, verify the region is set correctly:

```bash
# Check Lambda function configuration
aws lambda get-function-configuration \
  --function-name IngestionLambda \
  --region eu-west-2 \
  --query 'Environment.Variables'

# The output should NOT contain AWS_REGION
# Lambda will provide it automatically at runtime
```

## Testing

Test that your Lambda can access the region:

```bash
# Invoke the function
aws lambda invoke \
  --function-name IngestionLambda \
  --region eu-west-2 \
  --payload '{"test":"event"}' \
  response.json

# Check CloudWatch Logs to see if region is accessible
aws logs tail /aws/lambda/IngestionLambda --region eu-west-2 --follow
```

## Summary of Changes

### Removed
- ❌ `AWS_REGION` from Lambda environment variables (all functions)
- ❌ `AWS_REGION` from update scripts

### Changed
- ✅ Default region: `us-east-1` → `eu-west-2`
- ✅ Bootstrap commands updated to eu-west-2
- ✅ Documentation updated to reflect eu-west-2

### No Change Needed
- ✅ Lambda code can still access region via `os.environ['AWS_REGION']`
- ✅ AWS automatically provides this at runtime

---

**The template is now fixed and ready to deploy in eu-west-2!**
