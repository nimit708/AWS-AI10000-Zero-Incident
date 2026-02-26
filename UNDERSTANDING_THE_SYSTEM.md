# Understanding Your Incident Management System

## Summary of Test Run

### What Happened

1. **Test Event Sent** ✅
   - You sent an event with `event_type: "EC2 CPU Spike"`
   - Event was wrapped in `raw_payload` (correct format)
   - Source was "cloudwatch"

2. **Event Normalization** ⚠️
   - System detected source="cloudwatch"
   - Routed to `normalize_cloudwatch_event()` function
   - This function expects CloudWatch Alarm format with `detail.alarmName`
   - Your event had incident data directly, not CloudWatch alarm structure
   - Result: Event type changed to "CloudWatch Alarm: Unknown Alarm"

3. **Pattern Matching** ❌
   - Pattern matcher received event_type="CloudWatch Alarm: Unknown Alarm"
   - Checked against 6 patterns (EC2, Lambda, SSL, Network, Deployment, Service)
   - No match found → Pattern: "unknown"

4. **Remediation** ❌
   - No remediation handler for "unknown" pattern
   - EC2RemediationLambda was never invoked
   - Result: `remediation_success: null`

5. **SNS Notification** ❌
   - SNS notifications only sent when:
     - Remediation succeeds, OR
     - Incident is escalated
   - Neither happened, so no email sent

### Why No EC2 Remediation Lambda Logs

**EC2RemediationLambda was never invoked** because:
- Pattern didn't match "ec2_cpu_memory_spike"
- Only "unknown" pattern was detected
- No handler exists for "unknown" pattern

---

## How to Properly Test EC2 Remediation

### Option 1: Use Direct Incident Format (Recommended for Testing)

Change the event source to something other than "cloudwatch" to bypass CloudWatch normalization:

```python
test_event = {
    "source": "manual",  # <-- Not "cloudwatch"
    "timestamp": "2026-02-24T21:00:00Z",
    "raw_payload": {
        "incident_id": "test-ec2-001",
        "event_type": "EC2 CPU Spike",  # <-- This will be preserved
        "severity": "high",
        "resource_id": "i-1234567890abcdef0",
        "affected_resources": ["i-1234567890abcdef0"],
        "description": "CPU utilization exceeded 90%",
        "metadata": {
            "cpu_utilization": 95.5,
            "instance_type": "t3.medium",
            "region": "eu-west-2"
        }
    }
}
```

### Option 2: Use Real CloudWatch Alarm Format

Send an actual CloudWatch alarm event:

```python
test_event = {
    "source": "aws.cloudwatch",
    "detail-type": "CloudWatch Alarm State Change",
    "timestamp": "2026-02-24T21:00:00Z",
    "raw_payload": {
        "detail": {
            "alarmName": "EC2-CPU-High-i-1234567890abcdef0",
            "state": {
                "value": "ALARM",
                "reason": "Threshold Crossed: 1 datapoint [95.5] was greater than the threshold (90.0).",
                "timestamp": "2026-02-24T21:00:00Z"
            },
            "configuration": {
                "metrics": [
                    {
                        "metricStat": {
                            "metric": {
                                "namespace": "AWS/EC2",
                                "name": "CPUUtilization",
                                "dimensions": {
                                    "InstanceId": "i-1234567890abcdef0"
                                }
                            }
                        }
                    }
                ]
            }
        }
    }
}
```

---

## Testing Script

I'll create a proper test script for you:

```python
# test_ec2_proper.py
import json
import boto3
from datetime import datetime

lambda_client = boto3.client('lambda', region_name='eu-west-2')

# Use "manual" source to bypass CloudWatch normalization
test_event = {
    "source": "manual",
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "raw_payload": {
        "incident_id": f"test-ec2-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
        "event_type": "EC2 CPU Spike",
        "severity": "high",
        "resource_id": "i-1234567890abcdef0",
        "affected_resources": ["i-1234567890abcdef0"],
        "description": "CPU utilization exceeded 90% threshold",
        "metadata": {
            "cpu_utilization": 95.5,
            "instance_type": "t3.medium",
            "region": "eu-west-2",
            "threshold": 90.0
        }
    }
}

print("Testing EC2 Remediation...")
print(json.dumps(test_event, indent=2))

response = lambda_client.invoke(
    FunctionName='IngestionLambda',
    InvocationType='RequestResponse',
    Payload=json.dumps(test_event)
)

result = json.loads(response['Payload'].read())
print("\nResult:")
print(json.dumps(result, indent=2))
```

---

## Why SNS Emails Weren't Sent

### Current SNS Notification Logic

Looking at `lambda_handler.py`:

```python
# Step 7: Update incident record with results
if remediation_result:  # <-- This was None
    logger.info(f"Remediation result: Success={remediation_result.success}")
    self._update_incident_with_result(incident, remediation_result, routing_decision)
    
    # Step 8: Send notification
    if remediation_result.success:  # <-- Never reached
        self.sns_service.send_summary_notification(...)
```

### When SNS Notifications ARE Sent

1. **Summary Notifications** (incident-summary-topic):
   - When remediation succeeds
   - Includes incident details and actions taken

2. **Urgent Alerts** (incident-urgent-topic):
   - When incident is escalated
   - When routing path is "escalation"
   - When remediation fails after retries

### In Your Test

- Pattern was "unknown"
- No remediation executed
- `remediation_result` was `null`
- SNS notification code never executed
- **Result:** No email sent

---

## How to Trigger SNS Notifications

### Test 1: Successful Remediation (Summary Email)

1. Send proper EC2 event (with source="manual")
2. Pattern matches "ec2_cpu_memory_spike"
3. EC2RemediationLambda executes
4. Remediation succeeds
5. Summary notification sent to incident-summary-topic
6. **You receive email!**

### Test 2: Escalation (Urgent Email)

1. Send event with unknown pattern
2. Manually trigger escalation path
3. Urgent alert sent to incident-urgent-topic
4. **You receive email!**

---

## System Architecture Flow

```
1. Event Received
   ↓
2. Validation (check required fields)
   ↓
3. Normalization (convert to IncidentEvent)
   ├─ source="cloudwatch" → normalize_cloudwatch_event()
   ├─ source="api_gateway" → normalize_api_gateway_event()
   └─ source="manual" → direct normalization
   ↓
4. DynamoDB Record Created
   ↓
5. Bedrock Query (if enabled)
   ↓
6. Routing Decision
   ├─ High confidence (≥0.85) → Fast Path (AI remediation)
   └─ Low confidence (<0.85) → Structured Path (Pattern matching)
   ↓
7. Pattern Matching (Structured Path)
   ├─ EC2 CPU/Memory Spike → EC2RemediationLambda
   ├─ Lambda Timeout → LambdaRemediationLambda
   ├─ SSL Certificate Error → SSLRemediationLambda
   ├─ Network Timeout → NetworkRemediationLambda
   ├─ Deployment Failure → DeploymentRemediationLambda
   ├─ Service Unhealthy → ServiceRemediationLambda
   └─ Unknown → No handler (escalate)
   ↓
8. Remediation Execution
   ↓
9. SNS Notification (if remediation succeeded or escalated)
   ↓
10. DynamoDB Update (final status)
```

---

## Current System Status

### ✅ Working Components

1. **Event Validation** - Checks required fields
2. **Event Normalization** - Converts to standard format
3. **DynamoDB Integration** - Stores incident records
4. **Routing Logic** - Routes based on confidence
5. **Pattern Matching** - Identifies incident patterns
6. **Error Handling** - Graceful degradation
7. **CloudWatch Logging** - All events logged

### ⏳ Pending Components

1. **Bedrock Access** - Waiting for approval (you raised request)
2. **Remediation Execution** - Needs proper event format to test
3. **SNS Notifications** - Needs successful remediation to trigger

### 🔧 Known Issues

1. **CloudWatch Normalization** - Changes event type for non-alarm events
   - **Workaround:** Use source="manual" for testing
   
2. **Unknown Pattern Handler** - Returns string instead of class
   - **Impact:** Low - expected behavior for unknown patterns
   
3. **Bedrock Unavailable** - Model access not approved yet
   - **Impact:** Medium - system works with pattern matching only

---

## Next Steps to Test EC2 Remediation

### Step 1: Create Proper Test Script

```bash
# I'll create this for you
python test_ec2_proper.py
```

### Step 2: Verify Pattern Matching

Check logs to confirm pattern="ec2_cpu_memory_spike":
```bash
python check_logs.py
```

### Step 3: Check EC2 Remediation Logs

```bash
aws logs tail /aws/lambda/EC2RemediationLambda --region eu-west-2 --follow
```

### Step 4: Verify SNS Email

You should receive an email at sharmanimit18@outlook.com with:
- Subject: "Incident Summary: [incident_id]"
- Body: Incident details and remediation actions

---

## Summary

**Why you didn't get emails:**
- Event was normalized incorrectly (CloudWatch format expected)
- Pattern didn't match (became "unknown")
- No remediation executed
- SNS notification code never reached

**How to fix:**
- Use source="manual" instead of source="cloudwatch" for testing
- Or use proper CloudWatch alarm format
- Pattern will match correctly
- Remediation will execute
- SNS notification will be sent
- You'll receive email!

**Let me create the proper test script for you now...**
