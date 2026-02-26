"""Test parameter placeholder conversion fix"""
import boto3
import json
from datetime import datetime

lambda_client = boto3.client('lambda', region_name='eu-west-2')

timestamp = datetime.utcnow().isoformat() + 'Z'
event = {
    'source': 'aws.cloudwatch',
    'detail-type': 'CloudWatch Alarm State Change',
    'timestamp': timestamp,
    'time': timestamp,
    'raw_payload': {
        'detail': {
            'alarmName': 'Lambda-Timeout-Test',
            'state': {
                'value': 'ALARM',
                'reason': 'Lambda function exceeded timeout'
            },
            'configuration': {
                'metrics': [{
                    'metricStat': {
                        'metric': {
                            'name': 'Duration',
                            'namespace': 'AWS/Lambda',
                            'dimensions': {
                                'FunctionName': 'IngestionLambda'
                            }
                        }
                    }
                }]
            }
        }
    }
}

print("Invoking Lambda...")
response = lambda_client.invoke(
    FunctionName='IngestionLambda',
    InvocationType='RequestResponse',
    Payload=json.dumps(event)
)

result = json.loads(response['Payload'].read())
body = json.loads(result['body'])

print(f"\nIncident ID: {body['incident_id']}")
print(f"Routing Path: {body['routing_path']}")
print(f"Confidence: {body['confidence']}")
print(f"\nCheck logs in 10 seconds for parameter conversion details...")
