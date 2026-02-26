# AWS Incident Management System - Deployment Guide

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** configured with credentials
3. **Node.js** (v18 or later) and npm
4. **Python** (3.11 or later)
5. **AWS CDK** CLI installed globally: `npm install -g aws-cdk`

## Quick Start

### Linux/Mac

```bash
# Make scripts executable
chmod +x deploy.sh destroy.sh

# Deploy the stack
./deploy.sh
```

### Windows (PowerShell)

```powershell
# Deploy the stack
.\deploy.ps1
```

## Manual Deployment Steps

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt
pip install -r cdk-requirements.txt

# Install CDK dependencies
npm install
```

### 2. Configure AWS Credentials

```bash
aws configure
```

Set your:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., us-east-1)
- Output format (json)

### 3. Bootstrap CDK

First-time setup for your AWS account/region:

```bash
cdk bootstrap
```

### 4. Review Infrastructure

Synthesize and review the CloudFormation template:

```bash
cdk synth
```

### 5. Deploy

Deploy the stack to AWS:

```bash
cdk deploy
```

Or with auto-approval:

```bash
cdk deploy --require-approval never
```

## Post-Deployment Configuration

### 1. Confirm SNS Subscriptions

Check your email for SNS subscription confirmation emails and click the confirmation links for:
- Incident Summary Topic
- Incident Urgent Alerts Topic

### 2. Configure Bedrock AI Agent (Optional)

The system uses Bedrock models directly. To set up a full Bedrock Agent with Knowledge Base:

1. Go to AWS Bedrock Console
2. Create a Knowledge Base:
   - Data source: S3 bucket (created by CDK)
   - Embedding model: Amazon Titan Embed Text v2
3. Create an Agent:
   - Model: Claude 3.5 Sonnet
   - Link to Knowledge Base
4. Update Lambda environment variables with Agent ID

### 3. Test the System

Send a test incident:

```bash
aws lambda invoke \
  --function-name IncidentManagementStack-IngestionLambda* \
  --payload file://test_event.json \
  response.json
```

Example test_event.json:

```json
{
  "source": "cloudwatch",
  "raw_payload": {
    "AlarmName": "EC2-CPU-High",
    "NewStateValue": "ALARM",
    "StateChangeTime": "2024-01-01T12:00:00.000Z",
    "Trigger": {
      "MetricName": "CPUUtilization",
      "Dimensions": [
        {
          "name": "InstanceId",
          "value": "i-1234567890abcdef0"
        }
      ]
    }
  }
}
```

## Infrastructure Components

The deployment creates:

### DynamoDB Tables
- **IncidentTrackingTable**: Stores incident records with GSIs for status and event type queries
- **ResourceLockTable**: Manages resource locks for concurrent incident processing

### S3 Buckets
- **KnowledgeBaseBucket**: Stores historical incident documents with versioning enabled

### SNS Topics
- **IncidentSummaryTopic**: Summary notifications for successful remediations
- **IncidentUrgentTopic**: Urgent alerts for escalations and failures

### Lambda Functions
- **IngestionLambda**: Main entry point for incident processing
- **DLQProcessorLambda**: Processes failed incidents from Dead Letter Queue
- **PatternMatcherLambda**: Evaluates incident patterns
- **EC2RemediationLambda**: Handles EC2 CPU/Memory spike incidents
- **LambdaRemediationLambda**: Handles Lambda timeout incidents
- **SSLRemediationLambda**: Handles SSL certificate errors
- **NetworkRemediationLambda**: Handles network timeout issues
- **DeploymentRemediationLambda**: Handles deployment failures
- **ServiceRemediationLambda**: Handles service health issues

### Step Functions
- **RemediationStateMachine**: Orchestrates structured remediation path with pattern-based routing

### CloudWatch Alarms
- High remediation failure rate (>50%)
- High DLQ message count (>10 messages)
- Lambda errors (>5 errors in 5 minutes)
- High processing latency (>30 seconds)
- High escalation rate (>30%)

### IAM Roles
- Lambda execution role with permissions for:
  - DynamoDB read/write
  - S3 read/write
  - SNS publish
  - Bedrock model invocation
  - EC2, Lambda, ACM, ECS operations for remediation

## Environment Variables

The Lambda functions use these environment variables (automatically configured):

- `INCIDENT_TABLE_NAME`: DynamoDB incident tracking table
- `RESOURCE_LOCK_TABLE_NAME`: DynamoDB resource lock table
- `KNOWLEDGE_BASE_BUCKET`: S3 bucket for knowledge base
- `SUMMARY_TOPIC_ARN`: SNS topic for summaries
- `URGENT_TOPIC_ARN`: SNS topic for urgent alerts
- `DLQ_URL`: SQS Dead Letter Queue URL
- `STATE_MACHINE_ARN`: Step Functions state machine ARN
- `BEDROCK_AGENT_MODEL`: Bedrock model for AI agent
- `BEDROCK_EMBEDDING_MODEL`: Bedrock model for embeddings
- `BEDROCK_SUMMARY_MODEL`: Bedrock model for summaries
- `AWS_REGION`: AWS region

## Monitoring

### CloudWatch Dashboards

Create custom dashboards to monitor:
- Incident ingestion rate
- Remediation success/failure rates
- Processing latency
- Bedrock availability
- Escalation rate

### CloudWatch Logs

Lambda function logs are retained for 7 days:
- `/aws/lambda/IncidentManagementStack-IngestionLambda*`
- `/aws/lambda/IncidentManagementStack-*RemediationLambda*`
- `/aws/stepfunctions/IncidentManagementStack-RemediationStateMachine*`

### Metrics

Custom metrics in `IncidentManagement` namespace:
- `IngestionRate`
- `RemediationSuccessRate`
- `RemediationFailureRate`
- `ProcessingLatency`
- `BedrockAvailability`
- `EscalationRate`

## Cost Optimization

### Development Environment
- Use `RemovalPolicy.DESTROY` for easy cleanup
- Enable auto-delete for S3 buckets
- Use PAY_PER_REQUEST billing for DynamoDB

### Production Environment
- Consider provisioned capacity for DynamoDB if traffic is predictable
- Enable S3 lifecycle policies for old incident documents
- Use Reserved Capacity for Lambda if usage is consistent
- Set appropriate TTL on DynamoDB items

## Troubleshooting

### Deployment Fails

1. Check AWS credentials: `aws sts get-caller-identity`
2. Verify CDK bootstrap: `cdk bootstrap`
3. Check CloudFormation events in AWS Console
4. Review CDK diff: `cdk diff`

### Lambda Errors

1. Check CloudWatch Logs
2. Verify IAM permissions
3. Check environment variables
4. Test locally with sam local or lambda invoke

### No Notifications

1. Confirm SNS subscriptions in email
2. Check SNS topic permissions
3. Verify Lambda has SNS publish permissions
4. Check CloudWatch Logs for errors

### High Costs

1. Review CloudWatch metrics for usage patterns
2. Check DynamoDB read/write capacity
3. Review Lambda invocation counts and duration
4. Check S3 storage and requests
5. Monitor Bedrock API calls

## Cleanup

To remove all resources:

### Linux/Mac
```bash
./destroy.sh
```

### Windows (PowerShell)
```powershell
cdk destroy --force
```

### Manual Cleanup
```bash
# Delete the stack
cdk destroy

# Clean up CDK bootstrap (optional, only if no other CDK apps)
# aws cloudformation delete-stack --stack-name CDKToolkit
```

## Security Best Practices

1. **Least Privilege**: Review and restrict IAM permissions
2. **Encryption**: Enable encryption at rest for DynamoDB and S3
3. **VPC**: Consider deploying Lambda functions in VPC
4. **Secrets**: Use AWS Secrets Manager for sensitive configuration
5. **Logging**: Enable CloudTrail for audit logging
6. **Monitoring**: Set up CloudWatch alarms for security events

## Support

For issues or questions:
1. Check CloudWatch Logs
2. Review CloudFormation events
3. Consult AWS documentation
4. Check project README.md

## Next Steps

After deployment:
1. Configure CloudWatch dashboards
2. Set up additional alarms
3. Integrate with existing monitoring systems
4. Train the AI model with historical incidents
5. Document runbooks for manual intervention
6. Set up backup and disaster recovery
