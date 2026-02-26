"""
Quick test to verify SNS notifications are sent.
"""
import json
import boto3
from datetime import datetime
import time

def test_sns():
    """Test SNS notification."""
    
    lambda_client = boto3.client('lambda', region_name='eu-west-2')
    
    test_event = {
        "source": "cloudwatch",
        "timestamp": datetime.now().isoformat() + "Z",
        "raw_payload": {
            "event_type": "Lambda Timeout",
            "severity": "high",
            "resource_id": "IncidentDemo-TimeoutTest",
            "affected_resources": ["IncidentDemo-TimeoutTest"],
            "description": "Lambda function execution timed out",
            "metadata": {
                "function_name": "IncidentDemo-TimeoutTest",
                "timeout": 3,
                "alarm_name": "Lambda-Timeout-Test"
            }
        }
    }
    
    print("="*80)
    print("Testing SNS Notification")
    print("="*80)
    
    print(f"\n📤 Invoking IngestionLambda...")
    
    response = lambda_client.invoke(
        FunctionName='IngestionLambda',
        InvocationType='RequestResponse',
        Payload=json.dumps(test_event)
    )
    
    payload = json.loads(response['Payload'].read())
    print(f"\n📥 Response:")
    print(json.dumps(payload, indent=2))
    
    body = json.loads(payload.get('body', '{}'))
    incident_id = body.get('incident_id')
    routing_path = body.get('routing_path')
    
    print(f"\n✅ Incident ID: {incident_id}")
    print(f"   Routing Path: {routing_path}")
    
    print(f"\n⏳ Waiting 5 seconds...")
    time.sleep(5)
    
    print(f"\n📧 Check your email (sharmanimit18@outlook.com) for:")
    if routing_path == 'fast_path':
        print(f"   Subject: '✅ Remediation Successfully Done: Lambda Timeout'")
        print(f"   OR")
        print(f"   Subject: 'URGENT: Incident Requires Attention - Lambda Timeout'")
        print(f"   (depending on if AI remediation succeeded or failed)")
    else:
        print(f"   Subject: '✅ Remediation Successfully Done: Lambda Timeout'")
    
    print(f"\n{'='*80}")


if __name__ == "__main__":
    test_sns()
