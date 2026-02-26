# Next Steps - Complete Implementation Summary

## ✅ Completed Tasks

### 1. Bedrock Model Setup ✓
**Status:** Documentation created, models need to be enabled in AWS account

**What was done:**
- Created comprehensive [BEDROCK_SETUP_GUIDE.md](BEDROCK_SETUP_GUIDE.md) with step-by-step instructions
- Documented all 3 required models:
  - Agent Model: `anthropic.claude-3-5-sonnet-20241022-v2:0`
  - Embedding Model: `amazon.titan-embed-text-v2:0`
  - Summary Model: `anthropic.claude-3-haiku-20240307-v1:0`
- Provided AWS CLI commands for verification
- Listed alternative models if primary ones unavailable

**Action Required:**
```bash
# 1. Open Bedrock console
https://console.aws.amazon.com/bedrock/home?region=us-east-1#/modelaccess

# 2. Click "Manage model access"

# 3. Enable these 3 models:
#    - anthropic.claude-3-5-sonnet-20241022-v2:0
#    - amazon.titan-embed-text-v2:0
#    - anthropic.claude-3-haiku-20240307-v1:0

# 4. Verify access granted (usually instant for Titan, few minutes for Claude)

# 5. Test with CLI:
aws bedrock list-foundation-models --region us-east-1 \
  --query "modelSummaries[?modelId=='anthropic.claude-3-5-sonnet-20241022-v2:0']"
```

### 2. Routing Service Fix ✓
**Status:** Fixed and ready to deploy

**What was fixed:**
- Updated `lambda_handler.py` line 95-101
- Changed from `routing_service.route_incident(agent_response)` 
- To: `routing_service.route_incident(incident, agent_response)`
- Now correctly passes both incident and agent response as required by routing service

**Before:**
```python
routing_decision = self.routing_service.route_incident(agent_response)
```

**After:**
```python
routing_path = self.routing_service.route_incident(incident, agent_response)
routing_reason = self.routing_service.get_routing_reason(agent_response)
routing_decision = {
    'path': routing_path,
    'reason': routing_reason,
    'confidence': agent_response.confidence
}
```

### 3. Test Resources Created ✓
**Status:** Complete - 7 test payloads + integration tests ready

**What was created:**

#### Test Payload Files (in `test_payloads/` directory):
1. ✅ `ec2_cpu_spike.json` - EC2 CPU/Memory spike incident
2. ✅ `lambda_timeout.json` - Lambda function timeout
3. ✅ `ssl_certificate_error.json` - SSL certificate expiration
4. ✅ `network_timeout.json` - Network connectivity timeout
5. ✅ `deployment_failure.json` - CodeDeploy deployment failure
6. ✅ `service_unhealthy.json` - ECS service crash/unhealthy
7. ✅ `api_gateway_ec2.json` - API Gateway format example

#### Test Infrastructure:
- ✅ `tests/integration/test_payloads.py` - Payload generator module
- ✅ `tests/integration/test_end_to_end.py` - End-to-end integration tests
- ✅ `generate_test_payloads.py` - Script to generate JSON files
- ✅ `TESTING_GUIDE.md` - Comprehensive testing documentation

## 📋 Testing Checklist

### Quick Test (After Bedrock Models Enabled)

```bash
# 1. Generate test payloads (already done)
python generate_test_payloads.py

# 2. Deploy/update Lambda function
# Option A: Using CDK
cdk deploy

# Option B: Using deployment script
.\deploy.ps1  # Windows
./deploy.sh   # Linux/Mac

# 3. Get Lambda function name
aws cloudformation describe-stacks \
  --stack-name incident-management-system \
  --query 'Stacks[0].Outputs[?OutputKey==`IngestionLambdaArn`].OutputValue' \
  --output text

# 4. Test one incident type
aws lambda invoke \
  --function-name <FUNCTION_NAME> \
  --payload file://test_payloads/ec2_cpu_spike.json \
  --cli-binary-format raw-in-base64-out \
  response.json

# 5. Check response
cat response.json
```

### Full Test Suite

```bash
# Test all 6 incident types
for payload in test_payloads/*.json; do
  echo "Testing $(basename $payload)"
  aws lambda invoke \
    --function-name <FUNCTION_NAME> \
    --payload file://$payload \
    --cli-binary-format raw-in-base64-out \
    response_$(basename $payload)
  cat response_$(basename $payload)
  echo "---"
done
```

### Verify Results

```bash
# 1. Check DynamoDB for incident records
aws dynamodb scan --table-name IncidentTracking --limit 10

# 2. Check SNS notifications (email)
# Look for emails from:
# - incident-summary-topic (successful remediations)
# - incident-urgent-topic (failures/escalations)

# 3. Check CloudWatch Logs
aws logs tail /aws/lambda/<FUNCTION_NAME> --follow

# 4. Check Knowledge Base (S3)
aws s3 ls s3://<BUCKET_NAME>/incidents/ --recursive

# 5. Check Step Functions executions
aws stepfunctions list-executions \
  --state-machine-arn <STATE_MACHINE_ARN>
```

## 📊 Test Coverage by Incident Type

| Incident Type | Test Payload | Unit Tests | Integration Tests | Resource Requirements |
|---------------|--------------|------------|-------------------|----------------------|
| EC2 CPU Spike | ✅ | ✅ | ✅ | EC2 instance ID |
| Lambda Timeout | ✅ | ✅ | ✅ | Lambda function name |
| SSL Certificate | ✅ | ✅ | ✅ | ACM certificate ARN |
| Network Timeout | ✅ | ✅ | ✅ | Security group IDs |
| Deployment Failure | ✅ | ✅ | ✅ | CodeDeploy deployment |
| Service Unhealthy | ✅ | ✅ | ✅ | ECS cluster/service |

## 🔧 Resource Requirements for Testing

### Option 1: Mock Resources (Safe Testing)
The test payloads use placeholder resource IDs:
- `i-1234567890abcdef0` (EC2 instance)
- `MyProcessingFunction` (Lambda)
- `sg-source123`, `sg-dest456` (Security groups)

These will test the routing and pattern matching logic without affecting real resources.

### Option 2: Real Resources (Full Integration)
To test actual remediation:

1. **EC2 Instance:**
   ```bash
   # Create test instance
   aws ec2 run-instances \
     --image-id ami-0c55b159cbfafe1f0 \
     --instance-type t3.micro \
     --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=test-incident-mgmt}]'
   
   # Update test_payloads/ec2_cpu_spike.json with instance ID
   ```

2. **Lambda Function:**
   ```bash
   # Use existing function or create test function
   # Update test_payloads/lambda_timeout.json with function name
   ```

3. **ACM Certificate:**
   ```bash
   # List certificates
   aws acm list-certificates
   
   # Update test_payloads/ssl_certificate_error.json with ARN
   ```

## 🚀 Deployment Steps

### 1. Enable Bedrock Models (REQUIRED)
Follow [BEDROCK_SETUP_GUIDE.md](BEDROCK_SETUP_GUIDE.md)

### 2. Deploy Infrastructure
```bash
# Using CDK (recommended)
cdk deploy

# Or using CloudFormation
aws cloudformation deploy \
  --template-file cloudformation-template.yaml \
  --stack-name incident-management-system \
  --capabilities CAPABILITY_IAM
```

### 3. Confirm SNS Subscriptions
Check your email (sharmanimit18@outlook.com) for:
- Subscription confirmation for `incident-summary-topic`
- Subscription confirmation for `incident-urgent-topic`

Click "Confirm subscription" in both emails.

### 4. Run Tests
```bash
# Generate test payloads
python generate_test_payloads.py

# Run unit tests
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v

# Test deployed Lambda
aws lambda invoke \
  --function-name <FUNCTION_NAME> \
  --payload file://test_payloads/ec2_cpu_spike.json \
  response.json
```

## 📚 Documentation Created

1. **[BEDROCK_SETUP_GUIDE.md](BEDROCK_SETUP_GUIDE.md)** - Complete Bedrock model setup instructions
2. **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Comprehensive testing guide for all 6 incident types
3. **[generate_test_payloads.py](generate_test_payloads.py)** - Script to generate test JSON files
4. **[tests/integration/test_payloads.py](tests/integration/test_payloads.py)** - Test payload definitions
5. **[tests/integration/test_end_to_end.py](tests/integration/test_end_to_end.py)** - Integration test suite

## ⚠️ Important Notes

### Bedrock Model Access
- **Titan Embeddings**: Usually instant approval
- **Claude Models**: May take 5-10 minutes for approval
- **Region Availability**: Models may vary by region, check availability in your region

### Cost Considerations
- Bedrock charges per API call and token usage
- Test with small payloads first
- Monitor costs in AWS Cost Explorer

### IAM Permissions
The Lambda execution role needs permissions for:
- Bedrock: `bedrock:InvokeModel`, `bedrock:InvokeAgent`, `bedrock:Retrieve`
- DynamoDB: `dynamodb:PutItem`, `dynamodb:GetItem`, `dynamodb:UpdateItem`, `dynamodb:Query`
- S3: `s3:PutObject`, `s3:GetObject`, `s3:ListBucket`
- SNS: `sns:Publish`
- EC2, Lambda, ACM, ECS, CodeDeploy: Various permissions for remediation

## 🎯 Success Criteria

Your system is working correctly when:

1. ✅ All 3 Bedrock models show "Access granted" in console
2. ✅ Lambda function deploys without errors
3. ✅ Test payload invocation returns `statusCode: 200`
4. ✅ Incident record created in DynamoDB
5. ✅ SNS notification received (summary or urgent)
6. ✅ CloudWatch Logs show successful processing
7. ✅ Routing decision matches expected path (fast/structured/escalation)

## 🔍 Troubleshooting Quick Reference

| Issue | Solution |
|-------|----------|
| "Model not found" | Enable models in Bedrock console |
| "Access denied" Bedrock | Wait 5-10 min after requesting access |
| "Access denied" AWS resources | Check Lambda IAM role permissions |
| No SNS notifications | Confirm subscriptions in email |
| DynamoDB write failure | Verify table exists and Lambda has permissions |
| Pattern not matching | Check payload structure matches expected format |
| High latency | Check Bedrock API throttling, increase timeout |

## 📞 Support Resources

- **Bedrock Documentation**: https://docs.aws.amazon.com/bedrock/
- **Lambda Documentation**: https://docs.aws.amazon.com/lambda/
- **Step Functions Documentation**: https://docs.aws.amazon.com/step-functions/
- **Project Specs**: `.kiro/specs/aws-incident-management/`

## ✨ What's Next?

After successful testing:
1. Configure real AWS resource IDs in test payloads
2. Set up CloudWatch alarms for production monitoring
3. Create runbooks for escalated incidents
4. Train team on incident response procedures
5. Schedule regular testing of all incident types
6. Monitor Knowledge Base growth and AI Agent learning
7. Tune confidence threshold based on production data

---

**Summary:** All three tasks completed! 
1. ✅ Bedrock setup guide created (models need to be enabled in AWS console)
2. ✅ Routing service fixed in lambda_handler.py
3. ✅ Test resources created for all 6 incident types with comprehensive testing guide
