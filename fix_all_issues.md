# Fixing All Three Issues

## Issue 1: IAM Policy ✅ FIXED
- Added `lambda:GetFunctionConfiguration` and `cloudwatch:GetMetricStatistics`
- Policy updated successfully
- Wait 10 seconds for propagation

## Issue 2: SNS Using Bedrock for Summarization

### Current State
- SNS service sends raw technical logs
- No Bedrock summarization being used
- Need to integrate Bedrock summary model

### What Needs to Change
1. Add Bedrock summarization to SNS service
2. Use BEDROCK_SUMMARY_MODEL to generate human-readable summaries
3. Update lambda_handler to use Bedrock-generated summaries

### Implementation Plan
1. Update SNS service to call Bedrock for summarization
2. Add `generate_incident_summary()` method
3. Update lambda_handler SNS calls to use Bedrock summaries

## Issue 3: Verify Bedrock Models Usage

### Current State from Logs
```
[INFO] Querying Bedrock AI Agent for similar incidents
[ERROR] Bedrock API error: AccessDeniedException - Model access is denied
[ERROR] Bedrock unavailable for incident - routing to structured path
```

### Analysis
✅ Bedrock IS being called
❌ Model access denied (AWS Marketplace subscription issue)
✅ System gracefully handles error and routes to structured path

### Models Configuration
From config.py:
- BEDROCK_AGENT_MODEL: anthropic.claude-3-sonnet-20240229-v1:0
- BEDROCK_EMBEDDING_MODEL: amazon.titan-embed-text-v1
- BEDROCK_SUMMARY_MODEL: anthropic.claude-3-haiku-20240307-v1:0

### Issue
The models require AWS Marketplace subscription which hasn't been completed yet.
The error message says: "try again after 2 minutes" - suggesting the subscription request is pending.

### Solution
1. Wait for Bedrock model access to be granted (you mentioned you requested it)
2. Once granted, test again to verify Bedrock works
3. Add Bedrock summarization to SNS notifications

## Next Steps

1. ✅ IAM policy fixed - test Lambda timeout remediation
2. 🔄 Add Bedrock summarization to SNS service
3. ⏳ Wait for Bedrock model access approval
4. 🧪 Test complete E2E with Bedrock working
