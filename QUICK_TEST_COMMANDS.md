# Quick Test Commands Reference

## 1. Enable Bedrock Models (One-Time Setup)

```bash
# Open Bedrock console
# https://console.aws.amazon.com/bedrock/home?region=us-east-1#/modelaccess

# Enable these 3 models:
# - anthropic.claude-3-5-sonnet-20241022-v2:0
# - amazon.titan-embed-text-v2:0  
# - anthropic.claude-3-haiku-20240307-v1:0

# Verify access
aws bedrock list-foundation-models --region us-east-1 \
  --query "modelSummaries[?contains(modelId, 'claude') || contains(modelId, 'titan-embed')].[modelId, modelArn]" \
  --output table
```

## 2. Deploy System

```bash
# Option A: CDK
cdk deploy

# Option B: PowerShell script (Windows)
.\deploy.ps1

# Option C: Bash script (Linux/Mac)
./deploy.sh
```

## 3. Get Function Name

```bash
# Get Lambda function ARN
aws cloudformation describe-stacks \
  --stack-name incident-management-system \
  --query 'Stacks[0].Outputs[?OutputKey==`IngestionLambdaArn`].OutputValue' \
  --output text

# Extract just the function name
FUNCTION_NAME=$(aws cloudformation describe-stacks \
  --stack-name incident-management-system \
  --query 'Stacks[0].Outputs[?OutputKey==`IngestionLambdaArn`].OutputValue' \
  --output text | cut -d':' -f7)

echo $FUNCTION_NAME
```

## 4. Test Single Incident

```bash
# Test EC2 CPU Spike
aws lambda invoke \
  --function-name $FUNCTION_NAME \
  --payload file://test_payloads/ec2_cpu_spike.json \
  --cli-binary-format raw-in-base64-out \
  response.json

# View response
cat response.json | jq .
```

## 5. Test All 6 Incident Types

```bash
# Windows PowerShell
Get-ChildItem test_payloads\*.json | ForEach-Object {
    Write-Host "Testing $($_.Name)"
    aws lambda invoke `
      --function-name $env:FUNCTION_NAME `
      --payload "file://$($_.FullName)" `
      --cli-binary-format raw-in-base64-out `
      "response_$($_.Name)"
    Get-Content "response_$($_.Name)" | ConvertFrom-Json | ConvertTo-Json
    Write-Host "---"
}

# Linux/Mac Bash
for payload in test_payloads/*.json; do
  echo "Testing $(basename $payload)"
  aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --payload file://$payload \
    --cli-binary-format raw-in-base64-out \
    response_$(basename $payload)
  cat response_$(basename $payload) | jq .
  echo "---"
done
```

## 6. Verify Results

### Check DynamoDB
```bash
# Get table name
TABLE_NAME=$(aws cloudformation describe-stacks \
  --stack-name incident-management-system \
  --query 'Stacks[0].Outputs[?OutputKey==`IncidentTableName`].OutputValue' \
  --output text)

# Scan recent incidents
aws dynamodb scan \
  --table-name $TABLE_NAME \
  --limit 10 \
  --output table

# Query by status
aws dynamodb query \
  --table-name $TABLE_NAME \
  --index-name StatusIndex \
  --key-condition-expression "#s = :status" \
  --expression-attribute-names '{"#s":"status"}' \
  --expression-attribute-values '{":status":{"S":"resolved"}}' \
  --output table
```

### Check CloudWatch Logs
```bash
# Tail logs in real-time
aws logs tail /aws/lambda/$FUNCTION_NAME --follow

# Search for specific incident
aws logs filter-log-events \
  --log-group-name /aws/lambda/$FUNCTION_NAME \
  --filter-pattern "incident_id" \
  --max-items 10
```

### Check S3 Knowledge Base
```bash
# Get bucket name
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name incident-management-system \
  --query 'Stacks[0].Outputs[?OutputKey==`KnowledgeBaseBucketName`].OutputValue' \
  --output text)

# List incidents
aws s3 ls s3://$BUCKET_NAME/incidents/ --recursive

# Download an incident
aws s3 cp s3://$BUCKET_NAME/incidents/2024/02/incident-123.json ./
```

### Check Step Functions
```bash
# Get state machine ARN
STATE_MACHINE_ARN=$(aws cloudformation describe-stacks \
  --stack-name incident-management-system \
  --query 'Stacks[0].Outputs[?OutputKey==`StateMachineArn`].OutputValue' \
  --output text)

# List executions
aws stepfunctions list-executions \
  --state-machine-arn $STATE_MACHINE_ARN \
  --max-results 10 \
  --output table

# Get execution details
aws stepfunctions describe-execution \
  --execution-arn <EXECUTION_ARN> \
  --output json | jq .
```

## 7. Monitor Metrics

```bash
# Get CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace IncidentManagement \
  --metric-name ProcessingLatency \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum \
  --output table

# Check remediation success rate
aws cloudwatch get-metric-statistics \
  --namespace IncidentManagement \
  --metric-name RemediationSuccessRate \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average \
  --output table
```

## 8. Run Unit Tests

```bash
# All unit tests
pytest tests/unit/ -v

# Specific incident type
pytest tests/unit/test_ec2_remediation.py -v
pytest tests/unit/test_lambda_remediation.py -v
pytest tests/unit/test_ssl_certificate_remediation.py -v
pytest tests/unit/test_network_timeout_remediation.py -v
pytest tests/unit/test_deployment_failure_remediation.py -v
pytest tests/unit/test_service_health_remediation.py -v

# With coverage
pytest tests/unit/ --cov=src --cov-report=html
```

## 9. Run Integration Tests

```bash
# All integration tests
pytest tests/integration/ -v

# End-to-end tests
pytest tests/integration/test_end_to_end.py -v

# Specific test class
pytest tests/integration/test_end_to_end.py::TestEC2CPUSpike -v
```

## 10. Cleanup (Optional)

```bash
# Delete test responses
rm response*.json

# Delete CloudFormation stack
aws cloudformation delete-stack \
  --stack-name incident-management-system

# Wait for deletion
aws cloudformation wait stack-delete-complete \
  --stack-name incident-management-system

# Or using CDK
cdk destroy
```

## Environment Variables (Optional)

```bash
# Set for easier testing
export FUNCTION_NAME="incident-management-system-IngestionLambda"
export TABLE_NAME="IncidentTracking"
export BUCKET_NAME="incident-management-system-knowledgebasebucket-xxx"
export STATE_MACHINE_ARN="arn:aws:states:us-east-1:123456789012:stateMachine:xxx"

# Windows PowerShell
$env:FUNCTION_NAME = "incident-management-system-IngestionLambda"
$env:TABLE_NAME = "IncidentTracking"
$env:BUCKET_NAME = "incident-management-system-knowledgebasebucket-xxx"
$env:STATE_MACHINE_ARN = "arn:aws:states:us-east-1:123456789012:stateMachine:xxx"
```

## Quick Validation Checklist

```bash
# 1. Bedrock models enabled?
aws bedrock list-foundation-models --region us-east-1 \
  --query "modelSummaries[?contains(modelId, 'claude-3-5-sonnet')].modelId"

# 2. Lambda deployed?
aws lambda get-function --function-name $FUNCTION_NAME

# 3. DynamoDB table exists?
aws dynamodb describe-table --table-name $TABLE_NAME

# 4. SNS topics exist?
aws sns list-topics | grep incident

# 5. S3 bucket exists?
aws s3 ls | grep knowledge

# 6. Step Functions state machine exists?
aws stepfunctions list-state-machines | grep Remediation
```

## Troubleshooting Commands

```bash
# Check Lambda errors
aws lambda get-function --function-name $FUNCTION_NAME \
  --query 'Configuration.[FunctionName,LastUpdateStatus,LastUpdateStatusReason]'

# Check recent Lambda invocations
aws lambda list-invocations \
  --function-name $FUNCTION_NAME \
  --max-items 10

# Check DLQ messages
aws sqs receive-message \
  --queue-url $(aws sqs get-queue-url --queue-name incident-dlq --query 'QueueUrl' --output text) \
  --max-number-of-messages 10

# Check CloudWatch alarms
aws cloudwatch describe-alarms \
  --alarm-name-prefix "incident-management" \
  --state-value ALARM
```

## One-Liner Test (After Setup)

```bash
# Complete test in one command
aws lambda invoke \
  --function-name $(aws cloudformation describe-stacks --stack-name incident-management-system --query 'Stacks[0].Outputs[?OutputKey==`IngestionLambdaArn`].OutputValue' --output text | cut -d':' -f7) \
  --payload file://test_payloads/ec2_cpu_spike.json \
  --cli-binary-format raw-in-base64-out \
  response.json && cat response.json | jq .
```
