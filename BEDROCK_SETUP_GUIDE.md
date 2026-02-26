# Bedrock Model Setup Guide

## Overview
Your infrastructure stack references 3 Bedrock models that need to be enabled in your AWS account:

1. **Agent Model**: `anthropic.claude-3-5-sonnet-20241022-v2:0`
2. **Embedding Model**: `amazon.titan-embed-text-v2:0`
3. **Summary Model**: `anthropic.claude-3-haiku-20240307-v1:0`

## Steps to Enable Bedrock Models

### 1. Access Bedrock Console
```bash
# Open AWS Console and navigate to:
# Services > Amazon Bedrock > Model access
```

Or use this direct link (replace REGION with your region):
```
https://console.aws.amazon.com/bedrock/home?region=REGION#/modelaccess
```

### 2. Request Model Access

Click "Manage model access" or "Enable specific models" and enable:

#### Claude 3.5 Sonnet (Agent Model)
- Model ID: `anthropic.claude-3-5-sonnet-20241022-v2:0`
- Provider: Anthropic
- Use case: AI Agent for incident analysis and remediation orchestration
- Status: Should show "Access granted" after approval

#### Titan Embeddings V2 (Embedding Model)
- Model ID: `amazon.titan-embed-text-v2:0`
- Provider: Amazon
- Use case: Generate vector embeddings for semantic search in Knowledge Base
- Status: Usually instant approval

#### Claude 3 Haiku (Summary Model)
- Model ID: `anthropic.claude-3-haiku-20240307-v1:0`
- Provider: Anthropic
- Use case: Generate human-readable summaries for notifications
- Status: Should show "Access granted" after approval

### 3. Verify Model Access

Run this AWS CLI command to verify:
```bash
aws bedrock list-foundation-models --region us-east-1 --query "modelSummaries[?modelId=='anthropic.claude-3-5-sonnet-20241022-v2:0' || modelId=='amazon.titan-embed-text-v2:0' || modelId=='anthropic.claude-3-haiku-20240307-v1:0']"
```

### 4. Test Model Invocation

Test the agent model:
```bash
aws bedrock-runtime invoke-model \
  --model-id anthropic.claude-3-5-sonnet-20241022-v2:0 \
  --region us-east-1 \
  --body '{"anthropic_version":"bedrock-2023-05-31","max_tokens":100,"messages":[{"role":"user","content":"Hello"}]}' \
  output.json
```

Test the embedding model:
```bash
aws bedrock-runtime invoke-model \
  --model-id amazon.titan-embed-text-v2:0 \
  --region us-east-1 \
  --body '{"inputText":"Test embedding"}' \
  embedding-output.json
```

## Alternative Models (If Above Not Available)

If the specified models are not available in your region, you can use these alternatives:

### Agent Model Alternatives:
- `anthropic.claude-3-sonnet-20240229-v1:0` (Claude 3 Sonnet)
- `anthropic.claude-v2:1` (Claude 2.1)

### Embedding Model Alternatives:
- `amazon.titan-embed-text-v1` (Titan Embeddings V1)
- `cohere.embed-english-v3` (Cohere Embeddings)

### Summary Model Alternatives:
- `anthropic.claude-instant-v1` (Claude Instant)
- `amazon.titan-text-lite-v1` (Titan Text Lite)

## Update Infrastructure Stack

If you need to use alternative models, update `infrastructure/incident_management_stack.py`:

```python
# Line 33-35
self.bedrock_agent_model = "YOUR_AGENT_MODEL_ID"
self.bedrock_embedding_model = "YOUR_EMBEDDING_MODEL_ID"
self.bedrock_summary_model = "YOUR_SUMMARY_MODEL_ID"
```

Then redeploy:
```bash
cdk deploy
```

## Troubleshooting

### Error: "Model not found"
- Verify the model ID is correct for your region
- Check model availability: `aws bedrock list-foundation-models --region YOUR_REGION`

### Error: "Access denied"
- Ensure you've requested and received model access in Bedrock console
- Wait 5-10 minutes after requesting access
- Check IAM permissions include `bedrock:InvokeModel`

### Error: "Throttling"
- Bedrock has rate limits per model
- Implement exponential backoff in your code
- Request quota increase if needed

## Next Steps

After enabling models:
1. Verify all 3 models show "Access granted" in Bedrock console
2. Test model invocation using CLI commands above
3. Deploy or update your CDK stack
4. Test the incident management system with sample payloads
