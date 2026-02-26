"""
Test Lambda timeout remediation after IAM fix.
"""
import json
import boto3
from datetime import datetime
import time

def test_lambda_timeout():
    """Test Lambda timeout incident."""
    
    lambda_client = boto3.client('lambda', region_name='eu-west-2')
    sf_client = boto3.client('stepfunctions', region_name='eu-west-2')
    logs_client = boto3.client('logs', region_name='eu-west-2')
    
    # Test event
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
                "alarm_name": "Lambda-Timeout-High"
            }
        }
    }
    
    print("="*80)
    print("Testing Lambda Timeout Remediation (After IAM Fix)")
    print("="*80)
    
    # Invoke IngestionLambda
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
    
    print(f"\n✅ Incident created: {incident_id}")
    
    # Wait for Step Functions
    print(f"\n⏳ Waiting 5 seconds for Step Functions...")
    time.sleep(5)
    
    # Check Step Functions
    state_machine_arn = "arn:aws:states:eu-west-2:923906573163:stateMachine:RemediationStateMachine"
    
    executions = sf_client.list_executions(
        stateMachineArn=state_machine_arn,
        maxResults=1
    )
    
    if executions['executions']:
        exec = executions['executions'][0]
        print(f"\n✅ Step Functions execution:")
        print(f"   Name: {exec['name']}")
        print(f"   Status: {exec['status']}")
        
        # Wait for completion
        if exec['status'] == 'RUNNING':
            print(f"\n⏳ Waiting for execution to complete...")
            time.sleep(5)
            
            details = sf_client.describe_execution(executionArn=exec['executionArn'])
            print(f"   Final Status: {details['status']}")
    
    # Check Lambda logs
    print(f"\n📋 Checking LambdaRemediationLambda logs...")
    time.sleep(2)
    
    try:
        streams = logs_client.describe_log_streams(
            logGroupName='/aws/lambda/LambdaRemediationLambda',
            orderBy='LastEventTime',
            descending=True,
            limit=1
        )
        
        if streams['logStreams']:
            stream_name = streams['logStreams'][0]['logStreamName']
            
            events = logs_client.get_log_events(
                logGroupName='/aws/lambda/LambdaRemediationLambda',
                logStreamName=stream_name,
                limit=30,
                startFromHead=False
            )
            
            print(f"\n📜 Recent log events:")
            for event in events['events'][-15:]:
                message = event['message'].strip()
                if message and not message.startswith('INIT_START') and not message.startswith('START'):
                    print(f"   {message}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print(f"\n{'='*80}")
    print("Test Complete")
    print(f"{'='*80}")


if __name__ == "__main__":
    test_lambda_timeout()
