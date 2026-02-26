# Knowledge Base Architecture Explained

## Overview

Your incident management system uses a **two-phase knowledge base approach**:

1. **Query Phase**: Bedrock AI Agent queries historical incidents
2. **Learning Phase**: Successful resolutions are added back to the knowledge base

## Current State: Empty S3 Bucket

The S3 bucket (`incident-kb-923906573163`) is **empty** because:

- ✓ This is a **new system** with no historical incidents yet
- ✓ Knowledge base is populated **after successful resolutions**
- ✓ Test incidents **failed** (certificate doesn't exist), so they weren't added
- ✓ The system needs **successful resolutions** to learn from

## How Knowledge Base Works

### Phase 1: Query (What's Happening Now)

When an incident arrives:

```
Incident → Bedrock AI Agent → Query Knowledge Base
                ↓
         DynamoDB (Historical Incidents)
                ↓
         Find Similar Incidents
                ↓
         Generate Remediation Steps
```

**Current Behavior:**
- Bedrock AI Agent is queried ✓
- It searches for similar incidents in the knowledge base
- **Knowledge base is empty**, so AI generates steps from its training
- AI still works! It uses its base knowledge to suggest remediation

### Phase 2: Learning (What Should Happen)

After successful remediation:

```
Successful Resolution → Update DynamoDB → Export to S3
                                              ↓
                                    Knowledge Base (S3)
                                              ↓
                                    Bedrock Indexes It
                                              ↓
                              Future Incidents Can Learn From It
```

**Why It's Not Happening:**
- Test incidents are **failing** (certificate doesn't exist)
- Only **successful resolutions** are added to knowledge base
- Failed incidents are logged but not used for learning

## Where Is the Knowledge Base?

### 1. DynamoDB Table (`incident-tracking-table`)

**Purpose**: Real-time incident tracking and history

**Contains:**
- All incidents (successful and failed)
- Incident status, actions performed, timestamps
- Resolution summaries and error messages

**Current State**: ✓ Has incidents (including your SSL tests)

### 2. S3 Bucket (`incident-kb-923906573163`)

**Purpose**: Long-term knowledge base for Bedrock

**Contains:**
- Successful incident resolutions
- Remediation patterns that worked
- Structured data for AI learning

**Current State**: ✗ Empty (no successful resolutions yet)

### 3. Bedrock Knowledge Base

**Purpose**: AI-powered similarity search

**How It Works:**
- Indexes documents from S3
- Uses embeddings for semantic search
- Finds similar past incidents
- Provides context to AI Agent

**Current State**: ⚠️ Configured but no data indexed

## Why AI Still Works Without Knowledge Base

Bedrock AI Agent has **two sources of knowledge**:

### 1. Base Model Knowledge (Currently Using)
- Pre-trained on AWS best practices
- Understands common incident patterns
- Can generate remediation steps from scratch
- **This is what's being used now**

### 2. Custom Knowledge Base (Empty)
- Historical incidents from your system
- Your specific environment patterns
- Proven remediation strategies
- **Will be used once populated**

## How to Populate the Knowledge Base

### Option 1: Create Successful Test Incidents

Create incidents that can actually be resolved:

```python
# Example: Lambda timeout with real function
{
    "event_type": "Lambda Timeout",
    "resource_id": "IngestionLambda",  # Real function
    "severity": "medium"
}
```

### Option 2: Manually Add Sample Incidents

Upload sample incident resolutions to S3:

```bash
# Create sample incident
cat > sample_incident.json << EOF
{
  "incident_id": "sample-001",
  "event_type": "EC2 CPU Spike",
  "resolution_summary": "Increased instance size from t2.micro to t2.small",
  "actions_performed": [
    "Stopped EC2 instance",
    "Modified instance type",
    "Started EC2 instance",
    "Verified CPU metrics"
  ],
  "success": true,
  "resolution_time": 300
}
EOF

# Upload to S3
aws s3 cp sample_incident.json s3://incident-kb-923906573163/incidents/sample-001.json
```

### Option 3: Run Demo Scenarios

Use the demo scenarios that create real resources:

```bash
python demo_scenarios.py
```

## Knowledge Base Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                    INCIDENT OCCURS                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  Bedrock AI Agent Queries Knowledge Base                    │
│  - Searches S3 for similar incidents                        │
│  - If empty: Uses base model knowledge                      │
│  - If populated: Uses historical patterns                   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  AI Generates Remediation Steps                             │
│  - Based on similar incidents OR base knowledge             │
│  - Confidence score assigned                                │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  Remediation Executed                                        │
│  - Success: Add to knowledge base                           │
│  - Failure: Log but don't add                               │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼ (if successful)
┌─────────────────────────────────────────────────────────────┐
│  Update Knowledge Base                                       │
│  1. Save to DynamoDB (status = resolved)                    │
│  2. Export to S3 (structured JSON)                          │
│  3. Bedrock indexes the document                            │
│  4. Future incidents can learn from it                      │
└─────────────────────────────────────────────────────────────┘
```

## Current Test Results Explained

### SSL Certificate Test

**What Happened:**
1. ✓ Incident created in DynamoDB
2. ✓ Bedrock AI Agent queried (used base knowledge)
3. ✓ AI generated remediation steps
4. ✗ Remediation failed (certificate doesn't exist)
5. ✗ NOT added to knowledge base (failed resolution)

**Why Knowledge Base Is Empty:**
- The incident **failed**, so it's not a good learning example
- Only **successful** resolutions are added to knowledge base
- Failed incidents are tracked in DynamoDB but not used for AI learning

## Summary

| Component | Status | Purpose |
|-----------|--------|---------|
| DynamoDB | ✓ Has Data | Real-time incident tracking |
| S3 Bucket | ✗ Empty | Long-term knowledge base |
| Bedrock KB | ⚠️ No Data | AI-powered search |
| AI Agent | ✓ Working | Uses base model knowledge |

**The system is working correctly!** The AI is using its base knowledge to handle incidents. Once you have successful resolutions, they'll be added to the knowledge base and the AI will learn from your specific environment.

## Next Steps to Populate Knowledge Base

1. **Create real test resources** (EC2 instances, Lambda functions)
2. **Trigger incidents** that can actually be resolved
3. **Verify successful remediation**
4. **Check S3 bucket** - should have incident files
5. **Future incidents** will benefit from this knowledge

The empty S3 bucket is expected for a new system. It will populate over time as incidents are successfully resolved!
