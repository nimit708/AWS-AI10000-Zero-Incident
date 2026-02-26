# Bedrock SNS Summarization Investigation

## Issue
User reported that SNS notifications are not using Bedrock for AI-generated summaries.

## Investigation Findings

### 1. Environment Configuration ✅
- `BEDROCK_SUMMARY_MODEL` environment variable IS correctly set in Lambda:
  - Value: `anthropic.claude-3-haiku-20240307-v1:0`
  - Confirmed in Lambda configuration
- SNS Service IS initialized with `summary_model` parameter in `lambda_handler.py` line 78-82

### 2. Code Implementation ✅
- `SNSService` class HAS Bedrock summarization code:
  - `_generate_bedrock_summary()` method exists (lines 90-150)
  - `_generate_simple_summary()` fallback exists
  - Bedrock client is initialized when `summary_model` is provided

### 3. Root Cause Analysis ❌

**The Bedrock summarization code is NEVER being called because:**

1. **Fast Path (AI-Powered) Remediation is FAILING**
   - All recent Lambda Timeout incidents go through fast_path (confidence 0.85-0.90)
   - AI Agent remediation fails with error: "Operation GetFunction not found on lambda"
   - When remediation fails, `send_urgent_alert()` is called instead of `send_summary_notification()`

2. **Urgent Alerts Don't Use Bedrock**
   - `send_urgent_alert()` method does NOT call `_generate_bedrock_summary()`
   - Only `send_summary_notification()` uses Bedrock summarization
   - All notifications are going to the URGENT topic, not SUMMARY topic

3. **Structured Path Doesn't Send Notifications from Ingestion Lambda**
   - When incidents go through structured_path (Step Functions), the ingestion Lambda doesn't send notifications
   - Step Functions handles notifications after remediation completes
   - But recent tests show "unknown" pattern which just escalates

### 4. Evidence from Logs

**Test Run: a189a9c0-3a6a-4b0a-a370-be78e55ed266 (2026-02-24 22:37:54)**
```
Created incident: a189a9c0-3a6a-4b0a-a370-be78e55ed266, type: Lambda Timeout
Routing incident to fast path (confidence: 0.90)
Executing fast path - AI Agent remediation
Remediation failure: "Operation GetFunction not found on lambda"
Fast path remediation result: Success=False
Published notification to incident-urgent-topic (MessageId: 56571033-1422-5aba-a7b9-722b3ea8d566)
```

**Key Observation:** NO log entry for "Generated Bedrock summary" - confirming Bedrock is not being called.

## Solutions

### Option 1: Fix AI Agent Remediation (Recommended)
Fix the AI Agent so it generates correct AWS API calls, allowing fast_path remediation to succeed. This will trigger `send_summary_notification()` which uses Bedrock.

### Option 2: Add Bedrock to Urgent Alerts
Update `send_urgent_alert()` to also use Bedrock for generating human-readable failure summaries.

### Option 3: Force Structured Path for Testing
Lower the confidence threshold temporarily to force incidents through structured_path, which should trigger Lambda remediation handlers that send summary notifications.

### Option 4: Add Bedrock to Both Notification Types (Best Long-term)
Update both `send_summary_notification()` and `send_urgent_alert()` to use Bedrock summarization, ensuring all notifications benefit from AI-generated summaries.

## Recommendation

**Implement Option 4** - Add Bedrock summarization to BOTH notification types:
1. Keep existing Bedrock summarization in `send_summary_notification()` for successful remediations
2. Add Bedrock summarization to `send_urgent_alert()` for failures and escalations
3. This ensures ALL SNS notifications use AI-generated summaries regardless of remediation outcome

This provides the best user experience and fully utilizes the Bedrock investment.

## Next Steps

1. Update `send_urgent_alert()` method to call `_generate_bedrock_summary()`
2. Create a new Bedrock prompt template for failure/escalation scenarios
3. Test with both successful and failed remediation scenarios
4. Verify Bedrock is being called in CloudWatch logs ("Generated Bedrock summary")
5. Confirm email notifications contain AI-generated summaries

## Status
- Investigation: COMPLETE
- Root cause: IDENTIFIED
- Solution: PROPOSED
- Implementation: PENDING USER APPROVAL
