# AI Remediation Failure - Quick Summary

## TL;DR
The AI remediation failed because the knowledge base contains AWS API operation names in PascalCase (e.g., `GetFunction`), but boto3 expects Python method names in snake_case (e.g., `get_function`).

## Visual Flow

```
┌─────────────────────────────────────────────────────────────┐
│ TEST EVENT: Lambda Timeout for IncidentDemo-TimeoutTest    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ ✅ Normalization: Event Type = "Lambda Timeout"            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ ✅ Bedrock AI Agent: Queries knowledge base                │
│    Result: Match found with 0.9 confidence                  │
│    Returns: 5 remediation steps                             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ ✅ Routing: fast_path (0.9 >= 0.85 threshold)              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ ❌ AI Agent Executor: Step 1/5 FAILED                      │
│                                                              │
│    Step from Knowledge Base:                                │
│    {                                                         │
│      "action": "aws_api_call",                              │
│      "target": "lambda:GetFunction",  ← AWS API name        │
│      "parameters": {"FunctionName": "..."}                  │
│    }                                                         │
│                                                              │
│    Executor tries:                                           │
│    client = boto3.client('lambda')                          │
│    hasattr(client, 'GetFunction')  → False ❌               │
│                                                              │
│    boto3 expects:                                            │
│    client.get_function(...)  ← Python method name           │
│                                                              │
│    Error: "Operation GetFunction not found on lambda"       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ ✅ Failure Handling:                                        │
│    - Update DynamoDB: status = 'failed'                     │
│    - Generate Bedrock failure summary                        │
│    - Send SNS urgent alert                                   │
└─────────────────────────────────────────────────────────────┘
```

## The Problem

### AWS API Names vs boto3 Method Names

| AWS API Operation | boto3 Method | Status |
|-------------------|--------------|--------|
| GetFunction | get_function | ❌ Mismatch |
| UpdateFunctionConfiguration | update_function_configuration | ❌ Mismatch |
| ListFunctions | list_functions | ❌ Mismatch |
| DescribeInstances | describe_instances | ❌ Mismatch |

### Code Location

**File**: `src/services/ai_agent_executor.py`
**Method**: `invoke_aws_api()`
**Line**: ~225

```python
# This check fails because boto3 uses snake_case
if not hasattr(client, operation):  # operation = "GetFunction"
    return {
        'error': f"Operation {operation} not found on {service}"
    }
```

## Why Your Test JSON is Correct

Your test event is perfectly formatted:
- ✅ Has required fields: `timestamp`, `raw_payload`
- ✅ Alarm name contains "Lambda" and "Timeout"
- ✅ Metric name is "Duration"
- ✅ Function name is in dimensions

The issue is NOT with your test - it's with the knowledge base data format.

## What's Working

1. ✅ Event validation and normalization
2. ✅ Bedrock AI Agent query (finds match with 0.9 confidence)
3. ✅ Routing decision (correctly chooses fast_path)
4. ✅ DynamoDB incident logging
5. ✅ Bedrock failure summary generation
6. ✅ SNS urgent alert notification

## What's Not Working

1. ❌ AI Agent Executor can't execute AWS API calls
   - Reason: Method name format mismatch
   - Impact: All fast_path remediations fail at step 1

## Solutions

### Quick Fix (Recommended)
Add name conversion in `ai_agent_executor.py`:

```python
def _convert_to_boto3_method(self, operation: str) -> str:
    """Convert PascalCase to snake_case"""
    import re
    return re.sub(r'(?<!^)(?=[A-Z])', '_', operation).lower()

# Then in invoke_aws_api():
operation_method_name = self._convert_to_boto3_method(operation)
if not hasattr(client, operation_method_name):
    return {'error': f"Operation {operation} not found"}
operation_method = getattr(client, operation_method_name)
```

### Long-term Fix
Update knowledge base with correct boto3 method names:
- `GetFunction` → `get_function`
- `UpdateFunctionConfiguration` → `update_function_configuration`

## Impact

Currently, ALL fast_path (AI-powered) remediations will fail at the first AWS API call step. The system falls back to:
1. Marking incident as failed
2. Generating Bedrock failure summary
3. Sending urgent alert to on-call engineers

This is actually good failure handling - the system doesn't silently fail, it properly escalates!
