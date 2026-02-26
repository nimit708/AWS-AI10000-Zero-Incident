"""
Check if the knowledge base was updated with the SSL certificate incident.
"""
import boto3
import json
from datetime import datetime, timedelta

s3 = boto3.client('s3', region_name='eu-west-2')
dynamodb = boto3.client('dynamodb', region_name='eu-west-2')

# Knowledge base bucket name
KB_BUCKET = 'incident-kb-923906573163'
INCIDENTS_TABLE = 'incident-tracking-table'

print("="*80)
print("Checking Knowledge Base Updates")
print("="*80)

# Check S3 bucket for recent uploads
print("\n1. Checking S3 Knowledge Base Bucket...")
try:
    response = s3.list_objects_v2(
        Bucket=KB_BUCKET,
        Prefix='incidents/',
        MaxKeys=10
    )
    
    if 'Contents' in response:
        print(f"\n✓ Found {len(response['Contents'])} incident files in knowledge base")
        
        # Sort by last modified
        files = sorted(response['Contents'], key=lambda x: x['LastModified'], reverse=True)
        
        print("\nMost recent incidents:")
        for i, obj in enumerate(files[:5], 1):
            print(f"\n{i}. {obj['Key']}")
            print(f"   Size: {obj['Size']} bytes")
            print(f"   Last Modified: {obj['LastModified']}")
            
            # Check if it's recent (last 5 minutes)
            if (datetime.now(obj['LastModified'].tzinfo) - obj['LastModified']).total_seconds() < 300:
                print(f"   🆕 RECENT UPDATE!")
                
                # Download and show content
                try:
                    file_obj = s3.get_object(Bucket=KB_BUCKET, Key=obj['Key'])
                    content = file_obj['Body'].read().decode('utf-8')
                    data = json.loads(content)
                    
                    print(f"\n   Content Preview:")
                    print(f"   - Incident ID: {data.get('incident_id', 'N/A')}")
                    print(f"   - Event Type: {data.get('event_type', 'N/A')}")
                    print(f"   - Status: {data.get('status', 'N/A')}")
                    print(f"   - Resolution: {data.get('resolution_summary', 'N/A')[:100]}")
                except Exception as e:
                    print(f"   Error reading file: {e}")
    else:
        print("\n⚠ No incident files found in knowledge base")
        
except Exception as e:
    print(f"\n✗ Error accessing S3: {str(e)}")

# Check DynamoDB for SSL certificate incidents
print("\n\n2. Checking DynamoDB for SSL Certificate Incidents...")
try:
    # Scan for SSL certificate incidents
    response = dynamodb.scan(
        TableName=INCIDENTS_TABLE,
        FilterExpression='contains(event_type, :ssl)',
        ExpressionAttributeValues={
            ':ssl': {'S': 'SSL'}
        },
        Limit=10
    )
    
    if response['Items']:
        print(f"\n✓ Found {len(response['Items'])} SSL certificate incidents")
        
        for i, item in enumerate(response['Items'], 1):
            incident_id = item.get('incident_id', {}).get('S', 'N/A')
            event_type = item.get('event_type', {}).get('S', 'N/A')
            status = item.get('status', {}).get('S', 'N/A')
            created_at = item.get('created_at', {}).get('S', 'N/A')
            
            print(f"\n{i}. Incident: {incident_id}")
            print(f"   Event Type: {event_type}")
            print(f"   Status: {status}")
            print(f"   Created: {created_at}")
            
            # Check if it's our test incident
            if 'ssl-test' in incident_id.lower():
                print(f"   🎯 TEST INCIDENT FOUND!")
                
                # Show more details
                if 'resolution_summary' in item:
                    print(f"   Resolution: {item['resolution_summary'].get('S', 'N/A')[:100]}")
                if 'actions_performed' in item:
                    print(f"   Actions: {item['actions_performed'].get('S', 'N/A')[:100]}")
    else:
        print("\n⚠ No SSL certificate incidents found in DynamoDB")
        
except Exception as e:
    print(f"\n✗ Error accessing DynamoDB: {str(e)}")

# Check for recent incidents (last 10 minutes)
print("\n\n3. Checking Recent Incidents (Last 10 minutes)...")
try:
    cutoff_time = (datetime.utcnow() - timedelta(minutes=10)).isoformat()
    
    response = dynamodb.scan(
        TableName=INCIDENTS_TABLE,
        FilterExpression='created_at > :cutoff',
        ExpressionAttributeValues={
            ':cutoff': {'S': cutoff_time}
        },
        Limit=20
    )
    
    if response['Items']:
        print(f"\n✓ Found {len(response['Items'])} recent incidents")
        
        for i, item in enumerate(response['Items'], 1):
            incident_id = item.get('incident_id', {}).get('S', 'N/A')
            event_type = item.get('event_type', {}).get('S', 'N/A')
            status = item.get('status', {}).get('S', 'N/A')
            routing_path = item.get('routing_path', {}).get('S', 'N/A')
            
            print(f"\n{i}. {incident_id}")
            print(f"   Type: {event_type}")
            print(f"   Status: {status}")
            print(f"   Routing: {routing_path}")
            
            # Check if knowledge base was updated
            if 'kb_updated' in item:
                kb_status = item['kb_updated'].get('BOOL', False)
                print(f"   KB Updated: {'✓ YES' if kb_status else '✗ NO'}")
    else:
        print("\n⚠ No recent incidents found")
        
except Exception as e:
    print(f"\n✗ Error: {str(e)}")

print("\n" + "="*80)
print("Check Complete")
print("="*80)
