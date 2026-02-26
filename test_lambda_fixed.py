"""
Test script to verify Lambda handler works correctly after deployment.
"""
import json
import boto3
from datetime import datetime

def test_lambda_invocation():
    """Test Lambda with a properly formatted event."""
    
    # Create Lambda client
    lambda_client = boto3.client('lambda', region_name='eu-west-2')
    
    # Test payload
    test_event = {
        "source": "cloudwatch",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "raw_payload": {
            "incident_id": f"test-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            "event_type": "EC2 CPU Spike",
            "severity": "high",
            "resource_id": "i-test123456",
            "description": "CPU usage exceeded 90% for 5 minutes",
            "affected_resources": ["i-test123456"],
            "metadata": {
                "region": "eu-west-2",
                "instance_type": "t3.medium",
                "cpu_utilization": 95.5
            }
        }
    }
    
    print("Testing Lambda invocation...")
    print(f"Event: {json.dumps(test_event, indent=2)}")
    
    try:
        response = lambda_client.invoke(
            FunctionName='IngestionLambda',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        # Parse response
        status_code = response['StatusCode']
        payload = json.loads(response['Payload'].read())
        
        print(f"\n✅ Lambda invocation successful!")
        print(f"Status Code: {status_code}")
        print(f"Response: {json.dumps(payload, indent=2)}")
        
        # Save response
        with open('test_response.json', 'w') as f:
            json.dump(payload, f, indent=2)
        
        return payload
        
    except Exception as e:
        print(f"\n❌ Lambda invocation failed: {e}")
        raise

if __name__ == "__main__":
    test_lambda_invocation()
