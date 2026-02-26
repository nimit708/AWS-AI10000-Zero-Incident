# Test Run Explanation

## What Happened in the Test

### Test Event Sent
```json
{
  "source": "cloudwatch",
  "timestamp": "2026-02-24T20:39:09Z",
  "raw_payload": {
    "incident_id": "test-20260224-203909",
    "event_type": "EC2 CPU Spike",
    "severity": "high",
    "resource_id": "i-test123456",
    "description": "CPU usage exceeded 90% for 5 minutes"
  }
}
```

### Processing Flow

#### Step 1: Event Validation ✅
- Event was validated successfully
- Normalized to IncidentEvent
- Incident ID created: `e36417e5-0a05-4fd7-a68b-6b1ae98d61bc`

#### Step 2: DynamoDB Record Created ✅
- Incident record stored in `incident-tracking-table`
- Status: "received"
- You can verify this with:
```bash
aws dynamodb get-item \
  --table-name incident-tracking-table \
  --region eu-west-2 \
  --key '{"incident_id":{"S":"e36417e5-0a05-4fd7-a68b-6b1ae98d61bc"}}'
```

#### Step 3: Bedrock Query Attempted ⚠️
- Tried to query Bedrock AI Agent
- **Failed:** "Model use case details have not been submitted"
- **Fallback:** Returned default response (no match, confidence 0.0)
- **Impact:** System continued processing (graceful degradation working!)

#### Step 4: Routing Decision ✅
- Confidence: 0.0 (because Bedrock unavailable)
- Decision: **structured_path** (pattern matching)
- Reason: "No similar incident found in knowledge base"

#### Step 5: Pattern Matching ✅
- Pattern matcher evaluated the incident
- Result: **"unknown"** pattern
- **Why?** The test event didn't match any of the 6 defined patterns

#### Step 6: Remediation Attempt ❌
- Tried to get remediation handler for "unknown" pattern
- **Failed:** No handler exists for unknown patterns (expected behavior)
- **Result:** `remediation_success: null`

#### Step 7: Response Returned ✅
- StatusCode: 200 (success)
- Processing time: 0.18 seconds
- Incident recorded in DynamoDB

---

## Why You Didn't Receive Email

### Reason 1: No Remediation Executed
SNS notifications are only sent when:
1. Remediation is successfully executed, OR
2. Incident is escalated (urgent alert)

In this test:
- Pattern was "unknown" (no handler)
- No remediation was executed
- No escalation triggered
- Therefore, no SNS notification sent

### Reason 2: Code Path
Looking at the lambda_handler.py code:

```python
# Step 7: Update incident record with results
if remediation_result:  # <-- This was None/null
    logger.info(f"Remediation result: Success={remediation_result.success}")
    self._update_incident_with_result(incident, remediation_result, routing_decision)
    
    # Step 8: Send notification
    if remediation_result.success:  # <-- Never reached
        self.sns_service.send_summary_notification(...)
```

Since `remediation_result` was `null`, the SNS notification code was never executed.

---

## Why No EC2 Remediation Lambda Logs

### Reason: Pattern Didn't Match

The test event was classified as **"unknown"** pattern, not **"EC2 CPU Spike"**.

**Why?** Let's check the pattern matching logic:

#### What the Pattern Matcher Looks For

For EC2 CPU Spike pattern, the matcher checks:
1. Event type contains "EC2" or "CPU" or "Memory"
2. Severity is "high" or "critical"
3. Metadata contains CPU/Memory metrics
4. Resource ID starts with "i-" (EC2 instance)

#### What Our Test Event Had
```json
{
  "event_type": "EC2 CPU Spike",  // ✅ Has "EC2" and "CPU"
  "severity": "high",              // ✅ High severity
  "resource_id": "i-test123456",   // ✅ Starts with "i-"
  "metadata": {
    "region": "eu-west-2",
    "instance_type": "t3.medium",
    "cpu_utilization": 95.5        // ✅ Has CPU metric
  }
}
```

**This SHOULD have matched!** Let me check why it didn't...

---

## Issue Found: Event Normalization

The problem is in how the event was normalized. Let me check the logs again:

```
Created incident: e36417e5-0a05-4fd7-a68b-6b1ae98d61bc, 
type: CloudWatch Alarm: Unknown Alarm
```

The event type was changed to **"CloudWatch Alarm: Unknown Alarm"** during normalization!

This is because the normalization logic detected it came from CloudWatch but couldn't identify the specific alarm type.

---

## How to Trigger EC2 Remediation

### Option 1: Use Correct CloudWatch Event Format

```json
{
  "source": "aws.cloudwatch",
  "detail-type": "CloudWatch Alarm State Change",
  "detail": {
    "alarmName": "EC2-CPU-High",
    "state": {
      "value": "ALARM"
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
```

### Option 2: Use Direct Incident Format

```json
{
  "incident_id": "test-ec2-direct-001",
  "event_type": "EC2 CPU Spike",
  "severity": "high",
  "source": "manual",
  "timestamp": "2026-02-24T20:00:00Z",
  "resource_id": "i-1234567890abcdef0",
  "affected_resources": ["i-1234567890abcdef0"],
  "description": "CPU utilization exceeded 90% threshold",
  "metadata": {
    "cpu_utilization": 95.5,
    "instance_type": "t3.medium",
    "region": "eu-west-2",
    "threshold": 90.0,
    "duration_minutes": 5
  }
}
```

---

## Let's Test EC2 Remediation Properly

I'll create a test script that sends the correct format:
