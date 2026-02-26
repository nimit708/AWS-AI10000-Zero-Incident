"""Test Bedrock SNS summarization with successful remediation"""
import boto3
import json
from datetime import datetime

def test_lambda_timeout():
    """Test Lambda timeout incident - should trigger structured path and succeed"""
    lambda_client = boto3.client('lambda', region_name='eu-west-2')
    
    # Create Lambda timeout event
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
                    "reason": "Threshold Crossed: Lambda function exceeded timeout threshold"
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
    
    print("Testing Lambda Timeout incident (should use structured path)...")
    print(f"Event: {json.dumps(event, indent=2)}")
    
    response = lambda_client.invoke(
        FunctionName='IngestionLambda',
        InvocationType='RequestResponse',
        Payload=json.dumps(event)
    )
    
    result = json.loads(response['Payload'].read())
    print(f"\nResponse: {json.dumps(result, indent=2)}")
    
    # Parse the body
    if 'body' in result:
        body = json.loads(result['body'])
        print(f"\nIncident ID: {body.get('incident_id')}")
        print(f"Routing Path: {body.get('routing_path')}")
        print(f"Confidence: {body.get('confidence')}")
        print(f"Remediation Success: {body.get('remediation_success')}")
    
    return result

if __name__ == '__main__':
    test_lambda_timeout()
