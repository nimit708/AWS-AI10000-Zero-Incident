"""
Final E2E Test: Complete workflow with Knowledge Base update
This test simulates a successful remediation to demonstrate KB population.
"""
import boto3
import json
import time
from datetime import datetime

lambda_client = boto3.client('lambda', region_name='eu-west-2')
dynamodb = boto3.client('dynamodb', region_name='eu-west-2')
s3 = boto3.client('s3', region_name='eu-west-2')

INGESTION_LAMBDA = 'IngestionLambda'
KB_BUCKET = 'incident-kb-923906573163'

print("="*80)
print("FINAL E2E TEST: AI Remediation with Knowledge Base Update")
print("="*80)
print("\nThis test will:")
print("1. Trigger a Lambda timeout incident")
print("2. AI analyzes and generates remediation steps")
print("3. Remediation executes (simulated success)")
print("4. DynamoDB status updated to 'resolved'")
print("5. Knowledge base (S3) updated with successful resolution")
print("="*80)

# Create a test incident that will succeed
test_incident = {
    "source": "final-e2e-test",
    "timestamp": datetime.utcnow().isoformat() + 'Z',
    "raw_payload": {
        "event_type": "Lambda Timeout",
        "severity": "medium",
        "resource_id": "IngestionLambda",  # Real function that exists
        "description": "Lambda function timeout - E2E test for KB update",
        "affected_resources": ["IngestionLambda"],
        "timeout_value": 3,
        "execution_time": 5
    }
}

print("\n" + "="*80)
print("Step 1: Triggering Incident")
print("="*80)
print(f"Event Type: Lambda Timeout")
print(f"Resource: IngestionLambda")
print(f"Description: Simulated timeout for E2E test")

try:
    response = lambda_client.invoke(
        FunctionName=INGESTION_LAMBDA,
        InvocationType='RequestResponse',
        Payload=json.dumps(test_incident)
    )
    
    result = json.loads(response['Payload'].read())
    
    if response['StatusCode'] == 200 and result.get('statusCode') == 200:
        body = json.loads(result['body'])
        incident_id = body.get('incident_id')
        routing_path = body.get('routing_path')
        confidence = body.get('confidence', 'N/A')
        
        print(f"\n✓ Incident processed successfully!")
        print(f"  Incident ID: {incident_id}")
        print(f"  Routing Path: {routing_path}")
        print(f"  AI Confidence: {confidence}")
        
        if routing_path == 'fast':
            print(f"\n🤖 AI FAST PATH - Bedrock AI generated remediation steps")
        
    else:
        print(f"\n✗ Error processing incident")
        print(f"  Response: {json.dumps(result, indent=2)}")
        exit(1)
        
except Exception as e:
    print(f"\n✗ Error: {e}")
    exit(1)

# Wait for processing
print("\n" + "="*80)
print("Step 2: Monitoring Incident Status")
print("="*80)
print("Waiting for AI remediation to complete...")

time.sleep(5)

# Check DynamoDB for status
print("\nChecking DynamoDB...")
try:
    response = dynamodb.query(
        TableName='incident-tracking-table',
        KeyConditionExpression='incident_id = :id',
        ExpressionAttributeValues={
            ':id': {'S': incident_id}
        },
        ScanIndexForward=False,
        Limit=1
    )
    
    if response['Items']:
        item = response['Items'][0]
        status = item.get('status', {}).get('S', 'unknown')
        event_type = item.get('event_type', {}).get('S', 'N/A')
        routing_path = item.get('routing_path', {}).get('S', 'N/A')
        
        print(f"\n✓ Incident found in DynamoDB")
        print(f"  Status: {status}")
        print(f"  Event Type: {event_type}")
        print(f"  Routing Path: {routing_path}")
        
        if 'resolution_steps' in item:
            steps = item['resolution_steps'].get('L', [])
            print(f"  Resolution Steps: {len(steps)} steps executed")
            for i, step in enumerate(steps[:3], 1):
                print(f"    {i}. {step.get('S', 'N/A')[:80]}")
        
        if status == 'resolved':
            print(f"\n✓ STATUS: RESOLVED - Remediation successful!")
        elif status == 'failed':
            print(f"\n⚠ STATUS: FAILED - Remediation did not succeed")
            print(f"  (This is expected if the function doesn't actually have a timeout issue)")
        else:
            print(f"\n⏳ STATUS: {status} - Still processing...")
            
    else:
        print(f"\n✗ Incident not found in DynamoDB")
        
except Exception as e:
    print(f"\n✗ Error checking DynamoDB: {e}")

# Check S3 Knowledge Base
print("\n" + "="*80)
print("Step 3: Checking Knowledge Base (S3)")
print("="*80)
print(f"Bucket: {KB_BUCKET}")

time.sleep(2)

try:
    # List all objects in the incidents folder
    response = s3.list_objects_v2(
        Bucket=KB_BUCKET,
        Prefix='incidents/'
    )
    
    if 'Contents' in response and len(response['Contents']) > 0:
        print(f"\n✓ Knowledge Base has {len(response['Contents'])} incident(s)")
        
        # Sort by last modified
        files = sorted(response['Contents'], key=lambda x: x['LastModified'], reverse=True)
        
        print("\nMost recent incidents in knowledge base:")
        for i, obj in enumerate(files[:5], 1):
            print(f"\n{i}. {obj['Key']}")
            print(f"   Size: {obj['Size']} bytes")
            print(f"   Last Modified: {obj['LastModified']}")
            
            # Check if it's our test incident
            if incident_id in obj['Key']:
                print(f"   🎯 THIS IS OUR TEST INCIDENT!")
                
                # Download and show content
                try:
                    file_obj = s3.get_object(Bucket=KB_BUCKET, Key=obj['Key'])
                    content = file_obj['Body'].read().decode('utf-8')
                    data = json.loads(content)
                    
                    print(f"\n   📄 Knowledge Base Entry:")
                    print(f"   - Incident ID: {data.get('incident_id')}")
                    print(f"   - Event Type: {data.get('event_type')}")
                    print(f"   - Outcome: {data.get('outcome')}")
                    print(f"   - Confidence: {data.get('confidence_score')}")
                    print(f"   - Resolution Steps: {len(data.get('resolution_steps', []))} steps")
                    print(f"   - Resolution Time: {data.get('resolution_time')}s")
                    
                    print(f"\n   ✓ KNOWLEDGE BASE SUCCESSFULLY UPDATED!")
                    print(f"   ✓ Future incidents can now learn from this resolution!")
                    
                except Exception as e:
                    print(f"   Error reading file: {e}")
            else:
                # Check if it's recent (last 5 minutes)
                age_seconds = (datetime.now(obj['LastModified'].tzinfo) - obj['LastModified']).total_seconds()
                if age_seconds < 300:
                    print(f"   🆕 Recent update ({int(age_seconds)}s ago)")
        
    else:
        print(f"\n⚠ Knowledge Base is still empty")
        print(f"  This means either:")
        print(f"  1. Remediation failed (status != 'resolved')")
        print(f"  2. KB update code needs to be deployed")
        print(f"  3. Processing is still in progress")
        
except Exception as e:
    print(f"\n✗ Error checking S3: {e}")

# Summary
print("\n\n" + "="*80)
print("TEST SUMMARY")
print("="*80)
print(f"""
Incident ID: {incident_id}

Expected Flow:
1. ✓ Incident triggered via IngestionLambda
2. ✓ Bedrock AI analyzed the incident
3. ✓ AI generated remediation steps
4. ✓ Remediation executed (may succeed or fail)
5. ✓ DynamoDB updated with status
6. ? Knowledge Base updated (if status = 'resolved')

Check the results above to see if all steps completed successfully!

If KB was updated:
- S3 bucket will have a new JSON file
- File contains the complete incident resolution
- Future AI queries will find this incident
- AI will learn from this successful pattern
""")
print("="*80)
