"""
Proper EC2 remediation test with correct event format.
"""
import json
import boto3
from datetime import datetime
import time

def test_ec2_with_manual_source():
    """Test EC2 remediation using manual source to bypass CloudWatch normalization."""
    
    lambda_client = boto3.client('lambda', region_name='eu-west-2')
    
    # Use "api_gateway" source with direct incident data
    test_event = {
        "source": "api_gateway",  # <-- Use api_gateway to bypass CloudWatch normalization
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "raw_payload": {
            "body": {
                "incident_id": f"test-ec2-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
                "event_type": "EC2 CPU Spike",  # <-- This will be preserved
                "severity": "high",
                "resource_id": "i-1234567890abcdef0",
                "affected_resources": ["i-1234567890abcdef0"],
                "description": "CPU utilization exceeded 90% threshold for 5 minutes",
                "metadata": {
                    "cpu_utilization": 95.5,
                    "instance_type": "t3.medium",
                    "region": "eu-west-2",
                    "availability_zone": "eu-west-2a",
                    "threshold": 90.0,
                    "duration_minutes": 5
                }
            }
        }
    }
    
    print("="*80)
    print("Testing EC2 CPU Spike Remediation (Proper Format)")
    print("="*80)
    print(f"\n📋 Test Event:")
    print(json.dumps(test_event, indent=2))
    
    print(f"\n📤 Invoking IngestionLambda...")
    
    try:
        response = lambda_client.invoke(
            FunctionName='IngestionLambda',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        status_code = response['StatusCode']
        payload = json.loads(response['Payload'].read())
        
        print(f"\n📥 Lambda Response:")
        print(f"Status Code: {status_code}")
        
        # Parse response body
        if status_code == 200:
            body = json.loads(payload.get('body', '{}'))
            
            print(f"\n📊 Processing Results:")
            print(f"  ✅ Success: {body.get('success')}")
            print(f"  🆔 Incident ID: {body.get('incident_id')}")
            print(f"  🛣️  Routing Path: {body.get('routing_path')}")
            print(f"  📝 Routing Reason: {body.get('routing_reason')}")
            print(f"  📈 Confidence: {body.get('confidence')}")
            print(f"  🔧 Remediation Success: {body.get('remediation_success')}")
            print(f"  ⏱️  Processing Time: {body.get('processing_time_seconds')}s")
            
            incident_id = body.get('incident_id')
            
            if body.get('success'):
                print(f"\n✅ Lambda invocation successful!")
                
                # Wait a moment for logs to propagate
                print(f"\n⏳ Waiting 3 seconds for logs to propagate...")
                time.sleep(3)
                
                # Check CloudWatch logs
                print(f"\n🔍 Checking IngestionLambda logs...")
                print(f"   Looking for pattern matching result...")
                
                # Instructions for checking EC2 remediation
                if body.get('routing_path') == 'structured_path':
                    print(f"\n📋 Next Steps:")
                    print(f"   1. Check if pattern matched EC2:")
                    print(f"      python check_logs.py | findstr \"pattern\"")
                    print(f"")
                    print(f"   2. Check EC2RemediationLambda logs:")
                    print(f"      aws logs tail /aws/lambda/EC2RemediationLambda --region eu-west-2")
                    print(f"")
                    print(f"   3. Check DynamoDB record:")
                    print(f"      aws dynamodb get-item --table-name incident-tracking-table --region eu-west-2 --key '{{\"incident_id\":{{\"S\":\"{incident_id}\"}}}}'")
                    print(f"")
                    print(f"   4. Check your email (sharmanimit18@outlook.com) for SNS notification")
                
                # Save response
                with open('ec2_proper_test_response.json', 'w') as f:
                    json.dump(payload, f, indent=2)
                
                print(f"\n💾 Response saved to: ec2_proper_test_response.json")
                
                return incident_id
            else:
                print(f"\n⚠️  Test completed with errors")
                print(f"   Error: {body.get('error')}")
                print(f"   Details: {body.get('details')}")
                return None
        else:
            print(f"\n❌ Lambda invocation failed with status {status_code}")
            print(json.dumps(payload, indent=2))
            return None
        
    except Exception as e:
        print(f"\n❌ Error invoking Lambda: {e}")
        raise

def check_pattern_in_logs(incident_id):
    """Check CloudWatch logs for pattern matching result."""
    
    logs_client = boto3.client('logs', region_name='eu-west-2')
    log_group = '/aws/lambda/IngestionLambda'
    
    print(f"\n🔍 Checking logs for incident {incident_id}...")
    
    try:
        # Get recent log streams
        streams = logs_client.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=1
        )
        
        if not streams['logStreams']:
            print("No log streams found")
            return
        
        stream_name = streams['logStreams'][0]['logStreamName']
        
        # Get recent events
        events = logs_client.get_log_events(
            logGroupName=log_group,
            logStreamName=stream_name,
            limit=50
        )
        
        # Look for pattern matching logs
        pattern_logs = [e for e in events['events'] if 'pattern' in e['message'].lower() or 'identified' in e['message'].lower()]
        
        if pattern_logs:
            print(f"\n📋 Pattern Matching Logs:")
            for log in pattern_logs:
                print(f"   {log['message']}")
        else:
            print("No pattern matching logs found yet")
        
    except Exception as e:
        print(f"Error checking logs: {e}")

if __name__ == "__main__":
    print("\n🧪 EC2 Remediation Test - Proper Format\n")
    
    incident_id = test_ec2_with_manual_source()
    
    if incident_id:
        check_pattern_in_logs(incident_id)
    
    print("\n" + "="*80)
    print("Test Complete!")
    print("="*80)
    print("\n📧 If remediation succeeded, check your email for SNS notification!")
    print("   Email: sharmanimit18@outlook.com")
    print("   Subject: Incident Summary: [incident_id]")
