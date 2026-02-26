# Task 29: Deploy Infrastructure with CDK - COMPLETE

## Overview
Created comprehensive AWS CDK infrastructure for deploying the entire AWS Incident Management System, including all Lambda functions, DynamoDB tables, S3 buckets, SNS topics, Step Functions state machine, CloudWatch alarms, and IAM roles.

## Infrastructure Components Created

### 1. DynamoDB Tables
- **IncidentTrackingTable**
  - Partition key: `incident_id`
  - Sort key: `timestamp`
  - GSI: StatusIndex (status + timestamp)
  - GSI: EventTypeIndex (event_type + timestamp)
  - TTL enabled
  - Point-in-time recovery enabled
  - Pay-per-request billing

- **ResourceLockTable**
  - Partition key: `resource_id`
  - TTL enabled for automatic lock expiry
  - Pay-per-request billing

### 2. S3 Buckets
- **KnowledgeBaseBucket**
  - Versioning enabled
  - S3-managed encryption
  - Auto-delete objects on stack deletion (for testing)

### 3. SNS Topics
- **IncidentSummaryTopic**: Summary notifications
- **IncidentUrgentTopic**: Urgent alerts and escalations
- Email subscriptions configured

### 4. SQS Queue
- **IncidentDLQ**: Dead Letter Queue for failed incidents
  - 14-day retention period
  - 5-minute visibility timeout

### 5. Lambda Functions

#### Main Functions
- **IngestionLambda**
  - Handler: `lambda_handler.handler`
  - Runtime: Python 3.11
  - Timeout: 5 minutes
  - Memory: 512 MB
  - Entry point for all incidents

- **DLQProcessorLambda**
  - Handler: `src.services.graceful_degradation.process_dlq_message`
  - Processes failed incidents from DLQ
  - SQS event source mapping

#### Remediation Functions
- **EC2RemediationLambda**: Handles EC2 CPU/Memory spikes
- **LambdaRemediationLambda**: Handles Lambda timeouts
- **SSLRemediationLambda**: Handles SSL certificate errors
- **NetworkRemediationLambda**: Handles network timeouts
- **DeploymentRemediationLambda**: Handles deployment failures
- **ServiceRemediationLambda**: Handles service health issues

#### Supporting Functions
- **PatternMatcherLambda**: Evaluates incident patterns for routing

### 6. Step Functions State Machine
- **RemediationStateMachine**
  - Pattern-based routing to appropriate remediation Lambda
  - Choice state for 6 incident types
  - Escalation path for unknown patterns
  - Success notifications via SNS
  - 15-minute timeout
  - CloudWatch Logs integration

### 7. CloudWatch Alarms
- **HighRemediationFailureRate**: >50% failure rate
- **HighDLQMessageCount**: >10 messages in DLQ
- **IngestionLambdaErrors**: >5 errors in 5 minutes
- **HighProcessingLatency**: >30 seconds average
- **HighEscalationRate**: >30% escalation rate

All alarms send notifications to UrgentTopic

### 8. IAM Roles
- **LambdaExecutionRole** with permissions for:
  - CloudWatch Logs (basic execution)
  - DynamoDB (read/write on both tables)
  - S3 (read/write on knowledge base bucket)
  - SNS (publish to both topics)
  - Bedrock (invoke models, agents, retrieve)
  - EC2 (describe, stop, start, modify instances)
  - Auto Scaling (set desired capacity)
  - Lambda (get function, update configuration)
  - ACM (describe, renew certificates)
  - ECS (describe services/tasks, update service)
  - CodeDeploy (get/stop deployment)
  - Step Functions (start execution)

### 9. CloudFormation Outputs
- IncidentTableName
- ResourceLockTableName
- KnowledgeBaseBucketName
- IngestionLambdaArn
- StateMachineArn
- SummaryTopicArn
- UrgentTopicArn

## Deployment Scripts Created

### 1. deploy.sh (Linux/Mac)
- Checks AWS CLI configuration
- Installs Python and CDK dependencies
- Bootstraps CDK
- Synthesizes and deploys stack
- Provides post-deployment instructions

### 2. deploy.ps1 (Windows PowerShell)
- Same functionality as deploy.sh
- PowerShell-native implementation
- Color-coded output

### 3. destroy.sh
- Confirmation prompt
- Destroys entire stack
- Cleans up all resources

### 4. DEPLOYMENT.md
Comprehensive deployment guide including:
- Prerequisites
- Quick start instructions
- Manual deployment steps
- Post-deployment configuration
- Infrastructure component details
- Environment variables
- Monitoring setup
- Cost optimization tips
- Troubleshooting guide
- Security best practices

## Configuration Files

### 1. cdk-requirements.txt
- aws-cdk-lib>=2.100.0
- constructs>=10.0.0

### 2. package.json
- aws-cdk-lib dependency

### 3. app.py
- CDK application entry point
- Environment configuration
- Stack instantiation

## Environment Variables

All Lambda functions configured with:
- `INCIDENT_TABLE_NAME`
- `RESOURCE_LOCK_TABLE_NAME`
- `KNOWLEDGE_BASE_BUCKET`
- `SUMMARY_TOPIC_ARN`
- `URGENT_TOPIC_ARN`
- `DLQ_URL`
- `STATE_MACHINE_ARN`
- `BEDROCK_AGENT_MODEL`
- `BEDROCK_EMBEDDING_MODEL`
- `BEDROCK_SUMMARY_MODEL`
- `AWS_REGION`

## Key Features

### 1. Scalability
- Pay-per-request DynamoDB billing
- Auto-scaling Lambda functions
- Distributed locking for concurrent processing

### 2. Reliability
- Dead Letter Queue for failed incidents
- Retry logic with exponential backoff
- Point-in-time recovery for DynamoDB
- S3 versioning for knowledge base

### 3. Observability
- CloudWatch Logs (7-day retention)
- Custom metrics namespace
- Comprehensive alarms
- Step Functions execution history

### 4. Security
- IAM least privilege principles
- S3 encryption at rest
- VPC-ready architecture
- CloudTrail integration ready

### 5. Cost Optimization
- Pay-per-request billing
- Configurable Lambda memory/timeout
- S3 lifecycle policies ready
- TTL for automatic data cleanup

## Deployment Process

1. **Prerequisites Check**: AWS CLI, Node.js, Python
2. **Dependency Installation**: Python packages, CDK packages
3. **CDK Bootstrap**: One-time setup per account/region
4. **Synthesis**: Generate CloudFormation template
5. **Deployment**: Create all resources
6. **Post-Configuration**: SNS confirmations, Bedrock setup

## Testing Deployment

```bash
# Deploy
./deploy.sh

# Test ingestion
aws lambda invoke \
  --function-name IncidentManagementStack-IngestionLambda* \
  --payload file://test_event.json \
  response.json

# Check logs
aws logs tail /aws/lambda/IncidentManagementStack-IngestionLambda* --follow

# Destroy
./destroy.sh
```

## Requirements Satisfied
- **All infrastructure requirements**: DynamoDB, S3, SNS, Lambda, Step Functions, IAM, CloudWatch
- **Deployment automation**: Scripts for Linux, Mac, Windows
- **Monitoring**: Alarms and metrics
- **Documentation**: Comprehensive deployment guide

## Files Created/Modified
- `infrastructure/incident_management_stack.py` (enhanced)
- `deploy.sh` (new)
- `deploy.ps1` (new)
- `destroy.sh` (new)
- `cdk-requirements.txt` (new)
- `DEPLOYMENT.md` (new)
- `TASK_29_COMPLETE.md` (new)

## Next Steps
Task 29 is complete. The infrastructure is ready for deployment. Next task is Task 30: Create CloudWatch dashboards and alarms (additional monitoring beyond the basic alarms already created).

## Notes
- The infrastructure uses RemovalPolicy.DESTROY for easy cleanup during development
- For production, change to RemovalPolicy.RETAIN for critical resources
- Bedrock AI Agent and Knowledge Base require manual configuration in AWS Console
- SNS email subscriptions require manual confirmation
- Lambda layer for dependencies needs to be created separately (lambda_layer directory)
