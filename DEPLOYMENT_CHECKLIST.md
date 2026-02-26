# Deployment Checklist

Use this checklist to ensure successful deployment of the AWS Incident Management System.

## Pre-Deployment

- [ ] AWS CLI configured with correct credentials
- [ ] Account ID: 923906573163
- [ ] Region: us-east-1
- [ ] Email address ready: sharmanimit18@outlook.com
- [ ] All files present:
  - [ ] cloudformation-template.yaml
  - [ ] package-lambda.ps1 or package-lambda.sh
  - [ ] CLOUDFORMATION_DEPLOYMENT.md
  - [ ] QUICK_START.md

## Step 1: Package Lambda Code

- [ ] Run packaging script:
  - Windows: `.\package-lambda.ps1`
  - Linux/Mac: `./package-lambda.sh`
- [ ] Verify `lambda-package.zip` created
- [ ] Check file size (should be 5-10 MB)

## Step 2: Deploy CloudFormation Stack

- [ ] Open AWS CloudFormation Console
- [ ] Verify region is us-east-1
- [ ] Click "Create stack" → "With new resources"
- [ ] Upload cloudformation-template.yaml
- [ ] Enter stack name: IncidentManagementStack
- [ ] Enter parameters:
  - [ ] NotificationEmail: sharmanimit18@outlook.com
  - [ ] BedrockAgentModel: anthropic.claude-3-5-sonnet-20241022-v2:0
  - [ ] BedrockEmbeddingModel: amazon.titan-embed-text-v2:0
  - [ ] BedrockSummaryModel: anthropic.claude-3-haiku-20240307-v1:0
- [ ] Acknowledge IAM resource creation
- [ ] Click "Submit"
- [ ] Wait for CREATE_COMPLETE status (5-10 minutes)
- [ ] Check for any errors in Events tab

## Step 3: Confirm Email Subscriptions

- [ ] Check email inbox
- [ ] Find SNS subscription email #1 (Summary Notifications)
- [ ] Click "Confirm subscription"
- [ ] Find SNS subscription email #2 (Urgent Alerts)
- [ ] Click "Confirm subscription"
- [ ] Verify both subscriptions confirmed

## Step 4: Update IngestionLambda Environment Variable

- [ ] Run update script:
  - Linux/Mac: `./update-ingestion-lambda.sh`
  - Windows: `.\update-ingestion-lambda.ps1`
- [ ] Verify update successful
- [ ] Or manually run the command from stack outputs

## Step 5: Update Lambda Functions

Choose one method:

### Method A: AWS Console (Manual)
- [ ] Go to AWS Lambda Console
- [ ] Update IngestionLambda
- [ ] Update DLQProcessorLambda
- [ ] Update PatternMatcherLambda
- [ ] Update EC2RemediationLambda
- [ ] Update LambdaRemediationLambda
- [ ] Update SSLRemediationLambda
- [ ] Update NetworkRemediationLambda
- [ ] Update DeploymentRemediationLambda
- [ ] Update ServiceRemediationLambda

### Method B: AWS CLI (Automated)
- [ ] Run update commands for all 9 functions
- [ ] Verify all updates successful

## Step 6: Verify Deployment

- [ ] Get stack outputs:
  ```bash
  aws cloudformation describe-stacks --stack-name IncidentManagementStack --query 'Stacks[0].Outputs'
  ```
- [ ] Verify all outputs present:
  - [ ] IncidentTableName
  - [ ] ResourceLockTableName
  - [ ] KnowledgeBaseBucketName
  - [ ] IngestionLambdaArn
  - [ ] StateMachineArn
  - [ ] SummaryTopicArn
  - [ ] UrgentTopicArn
  - [ ] DLQUrl

## Step 7: Test the System

- [ ] Test ingestion Lambda:
  ```bash
  aws lambda invoke --function-name IngestionLambda --payload '{"test":"event"}' response.json
  ```
- [ ] Check response.json for success
- [ ] Verify CloudWatch Logs created:
  - [ ] /aws/lambda/IngestionLambda
  - [ ] /aws/lambda/PatternMatcherLambda
- [ ] Check DynamoDB tables exist:
  - [ ] incident-tracking-table
  - [ ] resource-lock-table
- [ ] Verify S3 bucket created
- [ ] Check Step Functions state machine exists

## Step 8: Monitor

- [ ] Check CloudWatch Alarms created (5 total)
- [ ] Verify CloudWatch Logs retention set to 7 days
- [ ] Test SNS notifications working
- [ ] Monitor first few incident executions

## Post-Deployment

- [ ] Document stack outputs for reference
- [ ] Save lambda-package.zip for future updates
- [ ] Set up monitoring dashboard (optional)
- [ ] Configure additional alarms if needed (optional)
- [ ] Test each remediation pattern (optional)

## Troubleshooting Checklist

If something goes wrong:

- [ ] Check CloudFormation Events tab for errors
- [ ] Review CloudWatch Logs for Lambda errors
- [ ] Verify IAM role permissions
- [ ] Confirm Bedrock models available in region
- [ ] Check SNS subscription status
- [ ] Verify Lambda environment variables set correctly
- [ ] Test Lambda functions individually
- [ ] Check Step Functions execution history

## Rollback Plan

If deployment fails:

- [ ] Note the error from CloudFormation Events
- [ ] Delete the stack:
  ```bash
  aws cloudformation delete-stack --stack-name IncidentManagementStack
  ```
- [ ] Wait for deletion to complete
- [ ] Fix the issue
- [ ] Retry deployment

## Success Criteria

Deployment is complete when:

- [x] CloudFormation stack status: CREATE_COMPLETE
- [x] All 9 Lambda functions have actual code (not placeholder)
- [x] Both SNS subscriptions confirmed
- [x] Test Lambda invocation successful
- [x] CloudWatch Logs showing executions
- [x] DynamoDB tables accessible
- [x] S3 bucket created
- [x] Step Functions state machine ready
- [x] CloudWatch Alarms active

## Estimated Time

- Package code: 2 minutes
- Deploy stack: 5-10 minutes
- Confirm emails: 2 minutes
- Update Lambda code: 5-10 minutes
- Verify and test: 5 minutes

**Total: 20-30 minutes**

## Notes

- Keep lambda-package.zip for future updates
- Document any custom changes made
- Save stack outputs for reference
- Monitor costs in AWS Cost Explorer
- Set up billing alerts if needed

## Next Steps After Deployment

1. Test each incident pattern
2. Monitor CloudWatch metrics
3. Review and adjust alarm thresholds
4. Add custom remediation logic as needed
5. Integrate with existing monitoring systems
6. Document operational procedures
7. Train team on system usage

---

**Ready to deploy? Start with Step 1!**
