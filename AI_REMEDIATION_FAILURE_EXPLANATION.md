# AI Remediation Failure - Detailed Explanation

## Test Event Structure

The test JSON we used:
```json
{
  "source": "aws.cloudwatch",
  "detail-type": "CloudWatch Alarm State Change",
  "timestamp": "2026-02-24T22:48:36.233674Z",
  "time": "2026-02-24T22:48:36.233674Z",
  "raw_payload": {
    "detail": {
      "alarmName": "Lambda-Timeout-IncidentDemo-TimeoutTest",
      "state": {
        "value": "ALARM",
        "reason": "Threshold Crossed: Lambda function exceeded timeout threshold"
      },
      "configuration": {
        "metrics": [{
          "metricStat": {
            "metric": {
              "name": "Duration",
              "namespace": "AWS/Lambda",
              "dimensions": {
                "FunctionName": "IncidentDemo-TimeoutTest"
              }
            }
          }
        }]
      }
    }
  }
}
```

## What Happens Step-by-Step

### Step 1: Event Normalization ✅
The event is normalized to:
- **Event Type**: "Lambda Timeout" (extracted from alarm name)
- **Affected Resource**: "IncidentDemo-TimeoutTest"
- **Severity**: "medium"
- **Source**: "cloudwatch"

### Step 2: Bedrock AI Agent Query ✅
```
Querying Bedrock AI Agent for similar incidents
Agent response - Match: True, Confidence: 0.9
```

The Bedrock AI Agent:
1. Searches the knowledge base for similar Lambda Timeout incidents
2. Finds a match with 90% confidence
3. Returns remediation steps that were previously successful

### Step 3: Routing Decision ✅
```
Routing incident to fast path (confidence: 0.90)
Routing decision: fast_path, Reason: High confidence match (0.90 >= 0.85)
```

Since confidence (0.90) >= threshold (0.85), it goes to **fast_path** (AI-powered remediation).

### Step 4: AI Agent Remediation Execution ❌
```
Executing fast path - AI Agent remediation
Executing 5 steps for incident 78738c38-8a6c-4424-944f-6e3f2b54c920
Executing step 1/5: aws_api_call
Remediation failure: {
  "incident_id": "78738c38-8a6c-4424-944f-6e3f2b54c920",
  "step_number": 1,
  "action": "aws_api_call",
  "error": "Operation GetFunction not found on lambda",
  "agent_confidence": 0.9
}
```

## Why It Failed

### The Root Cause: Bedrock AI Agent Returns Incorrect Step Format

The Bedrock AI Agent is querying the knowledge base and returning remediation steps, but the `target` field format doesn't match what the executor expects.

**ResolutionStep Model Structure:**
```python
class ResolutionStep(BaseModel):
    step_number: int
    action: Literal['invoke_lambda', 'aws_api_call', 'wait', 'conditional']
    target: str  # ⚠️ This is the problem field
    parameters: Dict[str, Any]
    description: str
```

**What the Bedrock AI Agent Returns (from knowledge base):**
```json
{
  "step_number": 1,
  "action": "aws_api_call",
  "target": "GetFunction",  // ❌ Missing service prefix
  "parameters": {
    "FunctionName": "IncidentDemo-TimeoutTest"
  },
  "description": "Get Lambda function configuration"
}
```

**What the AI Agent Executor Expects:**
```python
# From invoke_aws_api() method:
if ':' not in step.target:
    return {
        'success': False,
        'error': 'Target must be in format "service:operation"'
    }

service, operation = step.target.split(':', 1)  # Expects "lambda:GetFunction"
```

**The Correct Format Should Be:**
```json
{
  "step_number": 1,
  "action": "aws_api_call",
  "target": "lambda:GetFunction",  // ✅ Correct format
  "parameters": {
    "FunctionName": "IncidentDemo-TimeoutTest"
  },
  "description": "Get Lambda function configuration"
}
```

### The Error Flow

1. **Bedrock AI Agent** queries knowledge base → finds similar Lambda Timeout incident
2. **Returns 5 remediation steps** with confidence 0.9
3. **AI Agent Executor** tries to execute step 1:
   ```python
   if ':' not in step.target:  # "GetFunction" doesn't contain ':'
       return {'error': 'Target must be in format "service:operation"'}
   ```
4. **First check fails** → Returns error immediately
5. **Never actually calls AWS API** → The error happens before boto3 is even invoked

### Why "Operation GetFunction not found on lambda"?

Looking at the code more carefully:
```python
# After splitting "lambda:GetFunction"
service, operation = step.target.split(':', 1)

# Check if the operation exists on the boto3 client
if not hasattr(client, operation):
    return {
        'error': f"Operation {operation} not found on {service}"
    }
```

So the error message "Operation GetFunction not found on lambda" suggests:
1. The `target` field actually WAS in the correct format: "lambda:GetFunction"
2. But boto3's Lambda client doesn't have a method called `GetFunction`
3. **The correct boto3 method name is `get_function` (lowercase with underscore)**

### The Real Problem: Method Name Mismatch

AWS API operation names (PascalCase) ≠ boto3 method names (snake_case)

| AWS API Operation | boto3 Method Name |
|-------------------|-------------------|
| GetFunction | `get_function` |
| UpdateFunctionConfiguration | `update_function_configuration` |
| ListFunctions | `list_functions` |

**What Bedrock Returns:**
```json
{
  "target": "lambda:GetFunction"  // ❌ AWS API name (PascalCase)
}
```

**What boto3 Expects:**
```python
client.get_function(FunctionName='...')  # ✅ Python method (snake_case)
```

## The Complete Failure Chain

```
1. Test Event → Lambda Timeout for "IncidentDemo-TimeoutTest"
                ↓
2. Bedrock AI Agent → Queries knowledge base
                ↓
3. Knowledge Base → Returns similar incident with 0.9 confidence
                ↓
4. Resolution Steps → [
                        {
                          "action": "aws_api_call",
                          "target": "lambda:GetFunction",  // AWS API name
                          "parameters": {"FunctionName": "..."}
                        },
                        ...
                      ]
                ↓
5. AI Agent Executor → Tries to execute step 1
                ↓
6. invoke_aws_api() → Splits "lambda:GetFunction"
                ↓
7. boto3 client → client = boto3.client('lambda')
                ↓
8. hasattr check → hasattr(client, 'GetFunction')  // False!
                ↓
9. Error → "Operation GetFunction not found on lambda"
                ↓
10. Remediation → FAILED at step 1/5
                ↓
11. Status Update → incident.status = 'failed'
                ↓
12. Bedrock Summary → Generates failure summary
                ↓
13. SNS Alert → Sends urgent notification
```

## Why This Happens

### Knowledge Base Data Issue

The knowledge base contains historical incidents with remediation steps that use AWS API operation names (PascalCase) instead of boto3 method names (snake_case).

**Possible Causes:**
1. Knowledge base was populated with AWS CloudFormation/API documentation format
2. Previous successful remediations used a different executor that converted names
3. The Bedrock AI Agent is generating steps based on AWS documentation, not boto3 docs

## How to Fix This

### Option 1: Convert in AI Agent Executor (Recommended)
Add a conversion function to translate AWS API names to boto3 method names:

```python
def _convert_api_name_to_boto3(self, operation: str) -> str:
    """Convert AWS API operation name (PascalCase) to boto3 method (snake_case)"""
    # GetFunction → get_function
    # UpdateFunctionConfiguration → update_function_configuration
    import re
    return re.sub(r'(?<!^)(?=[A-Z])', '_', operation).lower()
```

### Option 2: Update Knowledge Base
Re-populate the knowledge base with correct boto3 method names.

### Option 3: Use AWS SDK's invoke_api
Instead of using `getattr(client, operation)`, use the lower-level API:
```python
# This accepts AWS API operation names directly
response = client._make_api_call(operation, parameters)
```

## Summary

**Test JSON**: ✅ Correct format
**Event Normalization**: ✅ Working
**Bedrock AI Agent**: ✅ Working (found match with 0.9 confidence)
**Routing Decision**: ✅ Working (fast_path selected)
**AI Agent Executor**: ❌ Failed due to method name mismatch
**Root Cause**: Knowledge base contains AWS API names (GetFunction) but boto3 expects Python method names (get_function)

The system is working as designed, but the knowledge base data needs to be updated with correct boto3 method names, OR the executor needs to convert AWS API names to boto3 format.


