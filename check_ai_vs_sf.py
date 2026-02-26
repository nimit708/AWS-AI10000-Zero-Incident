"""
Check if AI (fast path) or Step Functions (structured path) was used for SSL remediation.
"""
import boto3
import json
from datetime import datetime, timedelta

logs = boto3.client('logs', region_name='eu-west-2')
dynamodb = boto3.client('dynamodb', region_name='eu-west-2')

print("="*80)
print("Checking AI vs Step Functions Usage for SSL Test")
print("="*80)

# Check recent SSL incidents in DynamoDB
print("\n1. Checking DynamoDB for SSL incidents...")
try:
    response = dynamodb.scan(
        TableName='incident-tracking-table',
        FilterExpression='contains(event_type, :ssl)',
        ExpressionAttributeValues={
            ':ssl': {'S': 'SSL'}
        },
        Limit=5
    )
    
    if response['Items']:
        print(f"\n✓ Found {len(response['Items'])} SSL incidents")
        
        for i, item in enumerate(response['Items'], 1):
            incident_id = item.get('incident_id', {}).get('S', 'N/A')
            routing_path = item.get('routing_path', {}).get('S', 'N/A')
            confidence = item.get('confidence', {}).get('N', 'N/A')
            status = item.get('status', {}).get('S', 'N/A')
            created_at = item.get('created_at', {}).get('S', 'N/A')
            
            print(f"\n{i}. Incident: {incident_id}")
            print(f"   Routing Path: {routing_path}")
            print(f"   Confidence: {confidence}")
            print(f"   Status: {status}")
            print(f"   Created: {created_at}")
            
            if routing_path == 'fast':
                print(f"   🤖 AI FAST PATH - Bedrock AI Agent executed remediation")
            elif routing_path == 'structured':
                print(f"   🔄 STRUCTURED PATH - Step Functions executed remediation")
            elif routing_path == 'escalation':
                print(f"   ⚠️  ESCALATION PATH - Manual intervention required")
                
except Exception as e:
    print(f"\n✗ Error: {e}")

# Check Bedrock AI Agent logs
print("\n\n2. Checking Bedrock AI Agent Usage...")
try:
    # Get recent logs from IngestionLambda
    response = logs.filter_log_events(
        logGroupName='/aws/lambda/IngestionLambda',
        startTime=int((datetime.utcnow() - timedelta(minutes=10)).timestamp() * 1000),
        filterPattern='Bedrock'
    )
    
    bedrock_calls = 0
    for event in response.get('events', []):
        message = event['message']
        if 'Querying Bedrock AI Agent' in message:
            bedrock_calls += 1
            print(f"\n✓ Bedrock AI Agent was queried")
            print(f"  Timestamp: {datetime.fromtimestamp(event['timestamp']/1000)}")
        elif 'Agent response' in message:
            print(f"  {message.strip()}")
            
    if bedrock_calls > 0:
        print(f"\n✓ Total Bedrock AI calls: {bedrock_calls}")
    else:
        print(f"\n⚠ No Bedrock AI calls found in recent logs")
        
except Exception as e:
    print(f"\n✗ Error checking logs: {e}")

# Check Step Functions executions
print("\n\n3. Checking Step Functions Executions...")
try:
    sfn = boto3.client('stepfunctions', region_name='eu-west-2')
    
    response = sfn.list_executions(
        stateMachineArn='arn:aws:states:eu-west-2:923906573163:stateMachine:RemediationStateMachine',
        maxResults=5
    )
    
    recent_executions = []
    cutoff = datetime.utcnow() - timedelta(minutes=10)
    
    for execution in response.get('executions', []):
        if execution['startDate'].replace(tzinfo=None) > cutoff:
            recent_executions.append(execution)
    
    if recent_executions:
        print(f"\n✓ Found {len(recent_executions)} recent Step Functions executions")
        
        for i, execution in enumerate(recent_executions, 1):
            print(f"\n{i}. Execution: {execution['name']}")
            print(f"   Status: {execution['status']}")
            print(f"   Started: {execution['startDate']}")
            
            # Get execution details
            details = sfn.describe_execution(executionArn=execution['executionArn'])
            input_data = json.loads(details.get('input', '{}'))
            
            if 'incident' in input_data:
                incident = input_data['incident']
                print(f"   Event Type: {incident.get('event_type', 'N/A')}")
                print(f"   🔄 STEP FUNCTIONS was used for this incident")
    else:
        print(f"\n⚠ No recent Step Functions executions found")
        
except Exception as e:
    print(f"\n✗ Error: {e}")

# Summary
print("\n\n" + "="*80)
print("SUMMARY")
print("="*80)
print("""
The system has TWO remediation paths:

1. 🤖 AI FAST PATH (routing_path='fast'):
   - High confidence match (>= 0.85)
   - Bedrock AI Agent generates remediation steps
   - AI Agent Executor runs the steps directly
   - No Step Functions involved
   - Faster execution

2. 🔄 STRUCTURED PATH (routing_path='structured'):
   - Lower confidence or no match
   - Uses Step Functions state machine
   - Pattern matcher identifies the issue type
   - Specific remediation Lambda is invoked
   - More structured, auditable process

Check the 'Routing Path' field above to see which was used for your SSL test.
""")
print("="*80)
