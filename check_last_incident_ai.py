#!/usr/bin/env python3
"""
Check if the last incident used AI (Bedrock) for remediation.
"""
import boto3
from datetime import datetime, timezone
import json

def check_last_incident():
    """Check the most recent incident and verify AI usage."""
    
    region = 'eu-west-2'
    table_name = 'incident-tracking-table'
    
    # Initialize clients
    dynamodb = boto3.client('dynamodb', region_name=region)
    logs = boto3.client('logs', region_name=region)
    
    print("=" * 60)
    print("Checking Last Incident for AI Usage")
    print("=" * 60)
    
    try:
        # Scan DynamoDB for most recent incident
        print("\n1. Querying DynamoDB for latest incident...")
        response = dynamodb.scan(
            TableName=table_name,
            Limit=50
        )
        
        if not response.get('Items'):
            print("✗ No incidents found in DynamoDB")
            return
        
        # Sort by timestamp to get most recent
        items = response['Items']
        items.sort(key=lambda x: int(x['timestamp']['N']), reverse=True)
        
        latest = items[0]
        incident_id = latest['incident_id']['S']
        timestamp = int(latest['timestamp']['N'])
        status = latest.get('status', {}).get('S', 'unknown')
        event_type = latest.get('event_type', {}).get('S', 'unknown')
        
        print(f"\n✓ Latest Incident Found:")
        print(f"  Incident ID: {incident_id}")
        print(f"  Event Type: {event_type}")
        print(f"  Status: {status}")
        print(f"  Timestamp: {timestamp}")
        
        # Check for AI indicators in DynamoDB
        print("\n2. Checking DynamoDB for AI indicators...")
        
        ai_indicators = []
        
        # Check routing_path
        if 'routing_path' in latest:
            routing_path = latest['routing_path']['S']
            print(f"  Routing Path: {routing_path}")
            if routing_path == 'fast':
                ai_indicators.append("✓ Routing path is 'fast' (AI-powered)")
        
        # Check confidence score
        if 'confidence_score' in latest:
            confidence = float(latest['confidence_score']['N'])
            print(f"  Confidence Score: {confidence}")
            if confidence > 0:
                ai_indicators.append(f"✓ AI confidence score: {confidence}")
        
        # Check resolution steps
        if 'resolution_steps' in latest:
            steps = latest['resolution_steps']['L']
            print(f"  Resolution Steps: {len(steps)} steps")
            if len(steps) > 0:
                ai_indicators.append(f"✓ {len(steps)} resolution steps executed")
        
        # 3. Check CloudWatch Logs for Bedrock API calls
        print("\n3. Checking CloudWatch Logs for Bedrock API calls...")
        
        log_group = '/aws/lambda/IngestionLambda'
        
        # Search for Bedrock invocations around the incident time
        start_time = timestamp - 300  # 5 minutes before
        end_time = timestamp + 600    # 10 minutes after
        
        # Convert to milliseconds
        start_time_ms = start_time * 1000
        end_time_ms = end_time * 1000
        
        # Search for Bedrock-related log entries
        bedrock_queries = [
            'bedrock-agent-runtime',
            'InvokeAgent',
            'Bedrock AI Agent',
            'query_ai_agent'
        ]
        
        bedrock_calls = []
        
        for query in bedrock_queries:
            try:
                response = logs.filter_log_events(
                    logGroupName=log_group,
                    startTime=start_time_ms,
                    endTime=end_time_ms,
                    filterPattern=query
                )
                
                if response.get('events'):
                    for event in response['events']:
                        message = event['message']
                        if 'bedrock' in message.lower() or 'agent' in message.lower():
                            bedrock_calls.append(message[:200])
            except Exception as e:
                if 'ResourceNotFoundException' not in str(e):
                    print(f"  Warning: {e}")
        
        if bedrock_calls:
            print(f"\n✓ Found {len(bedrock_calls)} Bedrock-related log entries:")
            for i, call in enumerate(bedrock_calls[:5], 1):
                print(f"  {i}. {call}")
            ai_indicators.append(f"✓ {len(bedrock_calls)} Bedrock API calls in logs")
        else:
            print("  ⚠ No Bedrock API calls found in logs (may be outside time window)")
        
        # 4. Summary
        print("\n" + "=" * 60)
        print("AI USAGE VERIFICATION SUMMARY")
        print("=" * 60)
        
        if ai_indicators:
            print(f"\n✓ AI WAS USED - Found {len(ai_indicators)} indicators:")
            for indicator in ai_indicators:
                print(f"  {indicator}")
            
            print(f"\n✓ CONFIRMED: Incident {incident_id} used Bedrock AI for remediation")
        else:
            print("\n✗ No clear AI indicators found")
            print("  This incident may have used Step Functions or escalation path")
        
        # Additional details
        print("\n" + "=" * 60)
        print("Full Incident Details")
        print("=" * 60)
        
        for key, value in latest.items():
            if key not in ['incident_id', 'timestamp', 'status', 'event_type']:
                # Format the value
                if 'S' in value:
                    print(f"  {key}: {value['S']}")
                elif 'N' in value:
                    print(f"  {key}: {value['N']}")
                elif 'L' in value:
                    print(f"  {key}: {len(value['L'])} items")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_last_incident()
