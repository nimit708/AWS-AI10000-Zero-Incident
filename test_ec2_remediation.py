"""
Test EC2 remediation with proper event format.
"""
import json
import boto3
from datetime import datetime

def test_ec2_remediation():
    """Test EC2 CPU Spike remediation."""
    
    lambda_client = boto3.client('lambda', region_name='eu-west-2')
    
    # Proper event format that will match EC2 pattern
    test_event = {
        "source": "cloudwatch",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "raw_payload": {
            "incident_id": f"test-ec2-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            "event_type": "EC2 CPU Spike",
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
                "duration_minutes": 5,
                "alarm_name": "EC2-CPU-High-i-1234567890abcdef0"
            }
        }
    }
    
    print("="*80)
    print("Testing EC2 CPU Spike Remediation")
    print("="*80)
    print(f"\nTest Event:")
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
        print(f"Response: {json.dumps(payload, indent=2)}")
        
        # Parse response body
        if status_code == 200:
            body = json.loads(payload.get('body', '{}'))
            
            print(f"\n📊 Processing Results:")
            print(f"  Success: {body.get('success')}")
            print(f"  Incident ID: {body.get('incident_id')}")
            print(f"  Routing Path: {body.get('routing_path')}")
            print(f"  Routing Reason: {body.get('routing_reason')}")
            print(f"  Confidence: {body.get('confidence')}")
            print(f"  Remediation Success: {body.get('remediation_success')}")
            print(f"  Processing Time: {body.get('processing_time_seconds')}s")
            
            if body.get('success'):
                print(f"\n✅ Test successful!")
                
                # Check if EC2 remediation was triggered
                if body.get('routing_path') == 'structured_path':
                    print(f"\n🔍 Checking EC2RemediationLambda logs...")
                    print(f"   Run: python check_ec2_logs.py")
                    
                    # Check DynamoDB record
                    print(f"\n🔍 Checking DynamoDB record...")
                    incident_id = body.get('incident_id')
                    print(f"   Run: aws dynamodb get-item --table-name incident-tracking-table --region eu-west-2 --key '{{\"incident_id\":{{\"S\":\"{incident_id}\"}}}}'")
            else:
                print(f"\n⚠️  Test completed with errors")
                print(f"   Error: {body.get('error')}")
                print(f"   Details: {body.get('details')}")
        
        # Save response
        with open('ec2_test_response.json', 'w') as f:
            json.dump(payload, f, indent=2)
        
        print(f"\n💾 Response saved to: ec2_test_response.json")
        
        return payload
        
    except Exception as e:
        print(f"\n❌ Error invoking Lambda: {e}")
        raise

def check_pattern_matching():
    """Test pattern matching locally to verify EC2 pattern detection."""
    print("\n" + "="*80)
    print("Testing Pattern Matching Locally")
    print("="*80)
    
    # Import pattern matcher
    import sys
    sys.path.insert(0, '.')
    
    from src.services.pattern_matcher import PatternMatcher
    from src.models import IncidentEvent
    
    # Create test incident
    incident = IncidentEvent(
        incident_id="test-local-001",
        event_type="EC2 CPU Spike",
        severity="high",
        source="cloudwatch",
        timestamp=datetime.utcnow(),
        resource_id="i-1234567890abcdef0",
        affected_resources=["i-1234567890abcdef0"],
        description="CPU utilization exceeded 90%",
        metadata={
            "cpu_utilization": 95.5,
            "instance_type": "t3.medium",
            "region": "eu-west-2"
        }
    )
    
    # Test pattern matching
    matcher = PatternMatcher()
    pattern = matcher.match_pattern(incident)
    
    print(f"\n📊 Pattern Matching Result:")
    print(f"  Incident Type: {incident.event_type}")
    print(f"  Matched Pattern: {pattern}")
    print(f"  Pattern Description: {matcher.get_pattern_description(pattern)}")
    
    # Test all patterns
    all_patterns = matcher.evaluate_all_patterns(incident)
    print(f"\n📋 All Pattern Evaluations:")
    for pattern_name, matches in all_patterns.items():
        status = "✅" if matches else "❌"
        print(f"  {status} {pattern_name}: {matches}")
    
    if pattern == "ec2_cpu_memory_spike":
        print(f"\n✅ EC2 pattern matched correctly!")
        handler = matcher.get_remediation_handler(pattern)
        print(f"  Handler: {handler}")
    else:
        print(f"\n⚠️  EC2 pattern did NOT match")
        print(f"  This explains why EC2RemediationLambda wasn't invoked")

if __name__ == "__main__":
    print("\n🧪 EC2 Remediation Test Suite\n")
    
    # First, test pattern matching locally
    try:
        check_pattern_matching()
    except Exception as e:
        print(f"\n⚠️  Local pattern test failed: {e}")
        print("Continuing with Lambda test...")
    
    # Then test via Lambda
    print("\n")
    test_ec2_remediation()
    
    print("\n" + "="*80)
    print("Test Complete!")
    print("="*80)
    print("\nNext steps:")
    print("1. Check CloudWatch logs: python check_logs.py")
    print("2. Check EC2 remediation logs: aws logs tail /aws/lambda/EC2RemediationLambda --region eu-west-2")
    print("3. Check DynamoDB: aws dynamodb scan --table-name incident-tracking-table --region eu-west-2 --max-items 5")
