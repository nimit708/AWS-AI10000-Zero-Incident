# Demo Resources Created ✅

## Resources Successfully Created

### 1. EC2 Instance
- **Instance ID**: `i-0d06ecfa96b6b56f7`
- **Name**: IncidentDemo-EC2
- **Type**: t2.micro (Free tier eligible)
- **Status**: Running
- **Purpose**: Test EC2 CPU spike incidents
- **Region**: eu-west-2

### 2. Lambda Function
- **Function Name**: `IncidentDemo-TimeoutTest`
- **Runtime**: Python 3.11
- **Timeout**: 3 seconds
- **Memory**: 128 MB
- **Purpose**: Test Lambda timeout/error incidents
- **Region**: eu-west-2

### 3. IAM Role
- **Role Name**: IncidentDemoLambdaRole
- **Purpose**: Execution role for demo Lambda function

### 4. CloudWatch Alarms
- EC2 CPU utilization alarm (triggers at >80%)
- Lambda errors alarm (triggers on any error)

---

## How to Use for Demo

### Option 1: Simulated Incidents (Recommended) ⭐

Use the demo script to simulate all 6 incident types:

```bash
python demo_test.py
```

**Advantages:**
- Fast (completes in ~10 seconds)
- Reliable (100% success rate)
- No AWS resource manipulation needed
- Tests all 6 scenarios

**Output:**
```
✅ PASS - EC2 CPU Spike
✅ PASS - Lambda Timeout
✅ PASS - SSL Certificate Error
✅ PASS - Network Timeout
✅ PASS - Deployment Failure
✅ PASS - Service Unhealthy

🎉 All tests passed! System is fully operational!
```

---

### Option 2: Real AWS Resource Incidents

#### Test 1: EC2 CPU Spike

**Method A: Stress Test (Requires SSH)**
```bash
# Get instance details
aws ec2 describe-instances \
  --instance-ids i-0d06ecfa96b6b56f7 \
  --region eu-west-2 \
  --query "Reservations[0].Instances[0].PublicIpAddress"

# SSH into instance (need key pair)
ssh -i your-key.pem ec2-user@<PUBLIC_IP>

# Install and run stress tool
sudo amazon-linux-extras install epel -y
sudo yum install stress -y
stress --cpu 2 --timeout 60s
```

**Method B: CloudWatch Alarm (Simpler)**
```bash
# Manually set alarm to ALARM state
aws cloudwatch set-alarm-state \
  --alarm-name "IncidentDemo-EC2-CPU-i-0d06ecfa96b6b56f7" \
  --state-value ALARM \
  --state-reason "Testing incident management" \
  --region eu-west-2
```

#### Test 2: Lambda Timeout/Error

**Invoke the function:**
```bash
aws lambda invoke \
  --function-name IncidentDemo-TimeoutTest \
  --region eu-west-2 \
  response.json

cat response.json
```

**To trigger timeout:**
```bash
# Update function timeout to 1 second
aws lambda update-function-configuration \
  --function-name IncidentDemo-TimeoutTest \
  --timeout 1 \
  --region eu-west-2

# Then invoke (will timeout)
aws lambda invoke \
  --function-name IncidentDemo-TimeoutTest \
  --region eu-west-2 \
  response.json
```

#### Test 3-6: Other Scenarios

For SSL Certificate, Network Timeout, Deployment Failure, and Service Unhealthy:
- Use `python demo_test.py` (recommended)
- These don't require specific AWS resources
- Simulated incidents work perfectly for demo

---

## Viewing Demo Results

### Check DynamoDB Records
```bash
# View all incidents
aws dynamodb scan \
  --table-name incident-tracking-table \
  --region eu-west-2 \
  --max-items 10

# View specific incident
aws dynamodb get-item \
  --table-name incident-tracking-table \
  --region eu-west-2 \
  --key '{"incident_id":{"S":"<INCIDENT_ID>"}}'
```

### Check CloudWatch Logs
```bash
# View IngestionLambda logs
python check_logs.py

# Or use AWS CLI
aws logs tail /aws/lambda/IngestionLambda --region eu-west-2 --follow
```

### Check Email Notifications
- Email: sharmanimit18@outlook.com
- Check for SNS notifications (sent when remediation succeeds)

---

## Cost Estimate

### Monthly Costs (if kept running)
- **EC2 t2.micro**: Free tier eligible (750 hours/month free)
- **Lambda**: Free tier eligible (1M requests/month free)
- **CloudWatch Alarms**: $0.10/alarm/month × 2 = $0.20/month
- **DynamoDB**: On-demand pricing (minimal for demo)
- **SNS**: $0.50 per 1M requests (minimal for demo)

**Total**: ~$0.20-0.50/month (mostly within free tier)

### One-Time Demo Costs
- **EC2 running for 1 hour**: $0.01
- **Lambda invocations**: $0.00 (free tier)
- **DynamoDB**: $0.00 (free tier)

**Total for demo**: < $0.01

---

## Cleanup After Demo

### Quick Cleanup
```bash
python cleanup_demo_resources.py
```

This will remove:
- EC2 instance (i-0d06ecfa96b6b56f7)
- Lambda function (IncidentDemo-TimeoutTest)
- IAM role (IncidentDemoLambdaRole)
- CloudWatch alarms

### Manual Cleanup (if script fails)

**Terminate EC2:**
```bash
aws ec2 terminate-instances \
  --instance-ids i-0d06ecfa96b6b56f7 \
  --region eu-west-2
```

**Delete Lambda:**
```bash
aws lambda delete-function \
  --function-name IncidentDemo-TimeoutTest \
  --region eu-west-2
```

**Delete CloudWatch Alarms:**
```bash
aws cloudwatch delete-alarms \
  --alarm-names IncidentDemo-EC2-CPU-i-0d06ecfa96b6b56f7 \
  --region eu-west-2
```

**Delete IAM Role:**
```bash
# Detach policies first
aws iam detach-role-policy \
  --role-name IncidentDemoLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Delete role
aws iam delete-role --role-name IncidentDemoLambdaRole
```

---

## Demo Flow Recommendation

### For Best Demo Experience:

1. **Show Infrastructure** (2 minutes)
   - AWS Console → EC2 (show running instance)
   - AWS Console → Lambda (show demo function)
   - AWS Console → DynamoDB (show tables)
   - AWS Console → SNS (show confirmed subscriptions)

2. **Run Demo Script** (1 minute)
   ```bash
   python demo_test.py
   ```
   - Shows all 6 incident types processing
   - 100% success rate
   - Fast and reliable

3. **Show Results** (2 minutes)
   - Check DynamoDB for incident records
   - Check CloudWatch Logs for processing details
   - Show pattern matching in logs

4. **Explain Architecture** (3 minutes)
   - Event ingestion → Validation → Normalization
   - Bedrock AI analysis (when approved)
   - Pattern matching → Routing
   - Specialized remediation handlers
   - SNS notifications

5. **Show Monitoring** (2 minutes)
   - CloudWatch Logs
   - CloudWatch Alarms
   - DynamoDB records
   - Step Functions (if triggered)

**Total Demo Time**: ~10 minutes

---

## Troubleshooting

### EC2 Instance Not Responding
```bash
# Check instance status
aws ec2 describe-instance-status \
  --instance-ids i-0d06ecfa96b6b56f7 \
  --region eu-west-2
```

### Lambda Function Errors
```bash
# Check function logs
aws logs tail /aws/lambda/IncidentDemo-TimeoutTest \
  --region eu-west-2 \
  --follow
```

### Demo Script Fails
- Check AWS credentials: `aws sts get-caller-identity`
- Check region: Should be eu-west-2
- Check Lambda permissions: Should have invoke permissions

---

## Notes

- All resources are tagged with `Purpose: IncidentManagementDemo`
- Resources are minimal and cost-effective
- Can be safely deleted after demo
- EC2 instance is in default VPC
- Lambda function has basic execution role only

---

## Quick Reference

**EC2 Instance ID**: `i-0d06ecfa96b6b56f7`  
**Lambda Function**: `IncidentDemo-TimeoutTest`  
**Region**: `eu-west-2`  
**Account**: `923906573163`

**Demo Command**: `python demo_test.py`  
**Cleanup Command**: `python cleanup_demo_resources.py`

---

**Status**: ✅ Ready for Demo  
**Resources**: ✅ Created  
**Cost**: ✅ Minimal (< $0.50/month)

**You're all set for your demo! 🚀**
