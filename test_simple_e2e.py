"""Simple E2E test"""
import boto3
import json
from datetime import datetime

print("="*60)
print("SIMPLE E2E TEST")
print("="*60)

lambda_client = boto3.client('lambda', region_name='eu-west-2')

timestamp = datetime.utcnow().isoformat() + 'Z'
event = {
    "source": "aws.cloudwatch",
    "detail-type": "CloudWatch Alarm State Change",
    "timestamp": timestamp,
    "time": timestamp,
    "raw_payload": {
        "detail": {
            "alarmName": "Lambda-Timeout-IncidentDemo-TimeoutTest",
            "state": {
                "value": "ALARM",
                "reason": "Threshold Crossed"
            },
            "configuration": {
                "metrics": [{
                    "metricStat": {
                        "metric": {
                            "name": "Duration",
                            "namespace": "AWS/Lambda",
                            "dimensions": {
                                "FunctionName": "IncidentDemo-TimeoutTest"
                            }
                        }
                    }
                }]
            }
        }
    }
}

print("\nInvoking Lambda...")
try:
    response = lambda_client.invoke(
        FunctionName='IngestionLambda',
        InvocationType='RequestResponse',
        Payload=json.dumps(event)
    )
    
    result = json.loads(response['Payload'].read())
    print(f"\n✅ Response received")
    print(f"Status Code: {result['statusCode']}")
    
    if result['statusCode'] == 200:
        body = json.loads(result['body'])
        print(f"\n📋 Incident Details:")
        print(f"  Incident ID: {body.get('incident_id')}")
        print(f"  Routing Path: {body.get('routing_path')}")
        print(f"  Confidence: {body.get('confidence')}")
        print(f"  Remediation Success: {body.get('remediation_success')}")
        print(f"  Processing Time: {body.get('processing_time_seconds')}s")
        
        print(f"\n✅ TEST PASSED")
        print(f"\nCheck your email for notification!")
    else:
        print(f"\n❌ Error: {result}")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
