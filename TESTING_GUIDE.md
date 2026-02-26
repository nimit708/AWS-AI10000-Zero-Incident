# Testing Guide for AWS Incident Management System

## Overview

This guide covers testing all 6 incident types supported by the system:
1. EC2 CPU/Memory Spike
2. Lambda Timeout
3. SSL Certificate Error
4. Network Timeout
5. Deployment Failure
6. Service Unhealthy/Crash

## Prerequisites

### 1. Enable Bedrock Models
Follow the [BEDROCK_SETUP_GUIDE.md](BEDROCK_SETUP_GUIDE.md) to enable required models.

### 2. Deploy Infrastructure
```bash
# Deploy using CDK
cdk deploy

# Or deploy using CloudFormation
aws cloudformation deploy \
  --template-file cloudformation-template.yaml \
  --stack-name incident-management-system \
  --capabilities CAPABILITY_IAM
```

### 3. Generate Test Payloads
```bash
python generate_test_payloads.py
```

This creates `test_payloads/` directory with JSON files for each incident type.

## Test Payloads

### 1. EC2 CPU Spike (`ec2_cpu_spike.json`)
Tests automatic scaling of EC2 instances when CPU exceeds threshold.

**Expected Behavior:**
- Low confidence: Routes to structured path → Pattern matcher identifies "EC2 CPU/Memory Spike" → Remediation Lambda scales instance
- High confidence: Routes to fast path → AI Agent executes scaling directly

**Resource Requirements:**
- EC2 instance: `i-1234567890abcdef0` (or update payload with real instance ID)
- IAM permissions: `ec2:DescribeInstances`, `ec2:ModifyInstanceAttribute`, `ec2:StopInstances`, `ec2:StartInstances`

### 2. Lambda Timeout (`lambda_timeout.json`)
Tests automatic timeout adjustment for Lambda functions.

**Expected Behavior:**
- Identifies Lambda function from alarm
- Analyzes execution duration history
- Updates function timeout configuration

**Resource Requirements:**
- Lambda function: `MyProcessingFunction` (or update payload)
- IAM permissions: `lambda:GetFunction`, `lambda:UpdateFunctionConfiguration`

### 3. SSL Certificate Error (`ssl_certificate_error.json`)
Tests certificate renewal and expiration handling.

**Expected Behavior:**
- Identifies certificate ARN
- Checks expiration date
- Triggers ACM renewal if needed

**Resource Requirements:**
- ACM certificate ARN (update in payload)
- IAM permissions: `acm:DescribeCertificate`, `acm:RenewCertificate`

### 4. Network Timeout (`network_timeout.json`)
Tests network connectivity issue remediation.

**Expected Behavior:**
- Identifies source and destination resources
- Checks security groups, NACLs, route tables
- Applies corrective changes

**Resource Requirements:**
- Security groups: `sg-source123`, `sg-dest456` (or update payload)
- IAM permissions: `ec2:DescribeSecurityGroups`, `ec2:AuthorizeSecurityGroupIngress`, `ec2:DescribeNetworkAcls`

### 5. Deployment Failure (`deployment_failure.json`)
Tests deployment rollback and retry logic.

**Expected Behavior:**
- Identifies failed deployment
- Determines rollback vs retry strategy
- Executes rollback via CodeDeploy

**Resource Requirements:**
- CodeDeploy deployment group (update in payload)
- IAM permissions: `codedeploy:GetDeployment`, `codedeploy:StopDeployment`

### 6. Service Unhealthy/Crash (`service_unhealthy.json`)
Tests service restart and replacement logic.

**Expected Behavior:**
- Identifies unhealthy ECS service
- Determines restart vs replace strategy
- Executes service update

**Resource Requirements:**
- ECS cluster and service (update in payload)
- IAM permissions: `ecs:DescribeServices`, `ecs:UpdateService`, `ecs:DescribeTasks`

## Testing Methods

### Method 1: AWS Lambda Invoke (Deployed System)

```bash
# Get Lambda function name from stack outputs
FUNCTION_NAME=$(aws cloudformation describe-stacks \
  --stack-name incident-management-system \
  --query 'Stacks[0].Outputs[?OutputKey==`IngestionLambdaArn`].OutputValue' \
  --output text | cut -d':' -f7)

# Test EC2 CPU Spike
aws lambda invoke \
  --function-name $FUNCTION_NAME \
  --payload file://test_payloads/ec2_cpu_spike.json \
  --cli-binary-format raw-in-base64-out \
  response.json

# View response
cat response.json | jq .

# Test all incident types
for payload in test_payloads/*.json; do
  echo "Testing $(basename $payload)"
  aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --payload file://$payload \
    --cli-binary-format raw-in-base64-out \
    response_$(basename $payload)
  echo "---"
done
```

### Method 2: Local Testing (Unit Tests)

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific incident type tests
pytest tests/unit/test_ec2_remediation.py -v
pytest tests/unit/test_lambda_remediation.py -v
pytest tests/unit/test_ssl_certificate_remediation.py -v
pytest tests/unit/test_network_timeout_remediation.py -v
pytest tests/unit/test_deployment_failure_remediation.py -v
pytest tests/unit/test_service_health_remediation.py -v
```

### Method 3: Integration Tests

```bash
# Run end-to-end integration tests
pytest tests/integration/test_end_to_end.py -v

# Run with coverage
pytest tests/integration/ --cov=src --cov-report=html
```

### Method 4: Manual Testing with Python

```python
import json
from lambda_handler import lambda_handler

# Load test payload
with open('test_payloads/ec2_cpu_spike.json') as f:
    event = json.load(f)

# Mock Lambda context
class Context:
    aws_request_id = 'test-request-123'

# Invoke handler
result = lambda_handler(event, Context())
print(json.dumps(result, indent=2))
```

## Verifying Results

### 1. Check DynamoDB Records

```bash
# Get table name
TABLE_NAME=$(aws cloudformation describe-stacks \
  --stack-name incident-management-system \
  --query 'Stacks[0].Outputs[?OutputKey==`IncidentTableName`].OutputValue' \
  --output text)

# Query recent incidents
aws dynamodb scan \
  --table-name $TABLE_NAME \
  --limit 10 \
  --output table
```

### 2. Check SNS Notifications

```bash
# Check your email for notifications
# Summary notifications: incident-summary-topic
# Urgent alerts: incident-urgent-topic
```

### 3. Check CloudWatch Logs

```bash
# Get log group name
LOG_GROUP="/aws/lambda/incident-management-system-IngestionLambda"

# View recent logs
aws logs tail $LOG_GROUP --follow

# Search for specific incident
aws logs filter-log-events \
  --log-group-name $LOG_GROUP \
  --filter-pattern "incident_id"
```

### 4. Check Knowledge Base (S3)

```bash
# Get bucket name
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name incident-management-system \
  --query 'Stacks[0].Outputs[?OutputKey==`KnowledgeBaseBucketName`].OutputValue' \
  --output text)

# List stored incidents
aws s3 ls s3://$BUCKET_NAME/incidents/ --recursive
```

### 5. Check Step Functions Executions

```bash
# Get state machine ARN
STATE_MACHINE_ARN=$(aws cloudformation describe-stacks \
  --stack-name incident-management-system \
  --query 'Stacks[0].Outputs[?OutputKey==`StateMachineArn`].OutputValue' \
  --output text)

# List recent executions
aws stepfunctions list-executions \
  --state-machine-arn $STATE_MACHINE_ARN \
  --max-results 10

# Get execution details
aws stepfunctions describe-execution \
  --execution-arn <EXECUTION_ARN>
```

## Test Scenarios

### Scenario 1: Fast Path (High Confidence)
1. Manually add a similar incident to Knowledge Base
2. Send test payload
3. Verify AI Agent routes to fast path
4. Verify remediation executes without Step Functions

### Scenario 2: Structured Path (Low Confidence)
1. Send test payload for new incident type
2. Verify routes to Step Functions
3. Verify pattern matcher identifies correct type
4. Verify appropriate remediation Lambda invoked

### Scenario 3: Escalation (Unknown Incident)
1. Send payload with unknown incident type
2. Verify pattern matcher returns no match
3. Verify urgent SNS alert sent
4. Verify incident marked as "escalated" in DynamoDB

### Scenario 4: Graceful Degradation
1. Temporarily disable Bedrock model access
2. Send test payload
3. Verify system routes to Step Functions instead of failing
4. Verify incident still processed successfully

### Scenario 5: Failed Remediation Retry
1. Send test payload
2. Mock remediation failure
3. Verify system retries with structured path
4. Verify escalation after max retries

## Troubleshooting

### Issue: "Model not found" error
**Solution:** Enable Bedrock models following [BEDROCK_SETUP_GUIDE.md](BEDROCK_SETUP_GUIDE.md)

### Issue: "Access denied" for AWS resources
**Solution:** Verify Lambda execution role has required IAM permissions

### Issue: No SNS notifications received
**Solution:** 
1. Check SNS topic subscriptions are confirmed
2. Check spam folder for confirmation emails
3. Verify email address in infrastructure stack

### Issue: DynamoDB write failures
**Solution:** 
1. Check table exists and is active
2. Verify Lambda has DynamoDB permissions
3. Check CloudWatch Logs for detailed errors

### Issue: Pattern matcher not identifying incidents
**Solution:**
1. Verify payload structure matches expected format
2. Check pattern definitions in `src/services/pattern_matcher.py`
3. Add logging to pattern matcher for debugging

## Performance Benchmarks

Expected processing times:
- Fast path (high confidence): 2-5 seconds
- Structured path (pattern match): 10-30 seconds
- Escalation: 5-10 seconds

Monitor these metrics in CloudWatch:
- `IncidentManagement/ProcessingLatency`
- `IncidentManagement/RemediationSuccessRate`
- `IncidentManagement/EscalationRate`

## Next Steps

After successful testing:
1. Set up CloudWatch alarms for production monitoring
2. Configure real AWS resources in test payloads
3. Create runbooks for escalated incidents
4. Train team on incident response procedures
5. Schedule regular testing of all incident types
