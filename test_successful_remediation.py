"""Test successful remediation with Bedrock summary"""
import boto3
import json
from datetime import datetime

def test_lambda_timeout_structured_path():
    """
    Test Lambda timeout with LOW confidence to force structured_path.
    This will use the working Lambda remediation handler.
    """
    lambda_client = boto3.client('lambda', region_name='eu-west-2')
    
    # First, let's lower the Lambda timeout to trigger a real issue
    print("Setting up test: Lowering Lambda timeout to 3 seconds...")
    try:
        lambda_client.update_function_configuration(
            FunctionName='IncidentDemo-TimeoutTest',
            Timeout=3
        )
        print("✅ Lambda timeout set to 3 seconds")
    except Exception as e:
        print(f"Note: {e}")
    
    # Create Lambda timeout event with a DIFFERENT alarm name
    # This will cause Bedrock to NOT find a match (low confidence)
    # forcing it to go through structured_path
    timestamp = datetime.utcnow().isoformat() + 'Z'
    event = {
        "source": "aws.cloudwatch",
        "detail-type": "CloudWatch Alarm State Change",
        "timestamp": timestamp,
        "time": timestamp,
        "raw_payload": {
            "detail": {
                "alarmName": "Lambda-Duration-Alert-IncidentDemo-TimeoutTest",  # Different name
                "state": {
                    "value": "ALARM",
                    "reason": "Threshold Crossed: Lambda function duration exceeded 2900ms"
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
    
    print("\nTesting Lambda Timeout incident (structured path)...")
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
        print(f"\n{'='*60}")
        print(f"Incident ID: {body.get('incident_id')}")
        print(f"Routing Path: {body.get('routing_path')}")
        print(f"Confidence: {body.get('confidence')}")
        print(f"Remediation Success: {body.get('remediation_success')}")
        print(f"{'='*60}")
    
    return result

if __name__ == '__main__':
    test_lambda_timeout_structured_path()
