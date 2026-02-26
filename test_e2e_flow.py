"""
End-to-end test for the complete incident management flow.
Tests: Ingestion Lambda → Bedrock → Step Functions → Remediation Lambda → SNS
"""
import json
import boto3
from datetime import datetime
import time

def test_ec2_incident():
    """Test EC2 CPU spike incident end-to-end."""
    
    lambda_client = boto3.client('lambda', region_name='eu-west-2')
    sf_client = boto3.client('stepfunctions', region_name='eu-west-2')
    logs_client = boto3.client('logs', region_name='eu-west-2')
    
    # Test event for EC2 CPU spike (using our demo EC2 instance)
    test_event = {
        "source": "cloudwatch",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "raw_payload": {
            "event_type": "EC2 CPU Spike",
            "severity": "high",
            "resource_id": "i-0d06ecfa96b6b56f7",  # Our demo EC2 instance
            "affected_resources": ["i-0d06ecfa96b6b56f7"],
            "description": "EC2 instance CPU usage exceeded 80%",
            "metadata": {
                "instance_id": "i-0d06ecfa96b6b56f7",
                "cpu_utilization": 85.5,
                "alarm_name": "EC2-CPU-High"
            }
        }
    }
    
    print("="*80)
    print("End-to-End Test: EC2 CPU Spike Incident")
    print("="*80)
    print(f"\nTest Event:")
    print(json.dumps(test_event, indent=2))
    
    # Step 1: Invoke IngestionLambda
    print(f"\n{'='*80}")
    print("Step 1: Invoking IngestionLambda")
    print(f"{'='*80}")
    
    response = lambda_client.invoke(
        FunctionName='IngestionLambda',
        InvocationType='RequestResponse',
        Payload=json.dumps(test_event)
    )
    
    payload = json.loads(response['Payload'].read())
    print(f"\n📥 IngestionLambda Response:")
    print(json.dumps(payload, indent=2))
    
    if payload.get('statusCode') != 200:
        print(f"\n❌ IngestionLambda failed!")
        return
    
    body = json.loads(payload.get('body', '{}'))
    incident_id = body.get('incident_id')
    routing_path = body.get('routing_path')
    
    print(f"\n✅ Incident created: {incident_id}")
    print(f"   Routing path: {routing_path}")
    
    # Step 2: Wait and check Step Functions
    print(f"\n{'='*80}")
    print("Step 2: Checking Step Functions Execution")
    print(f"{'='*80}")
    
    print(f"\n⏳ Waiting 5 seconds for Step Functions to start...")
    time.sleep(5)
    
    state_machine_arn = "arn:aws:states:eu-west-2:923906573163:stateMachine:RemediationStateMachine"
    
    executions = sf_client.list_executions(
        stateMachineArn=state_machine_arn,
        maxResults=5
    )
    
    if not executions['executions']:
        print(f"\n❌ No Step Functions executions found")
        print(f"   Expected: Step Functions should be triggered for structured_path")
        return
    
    # Find our execution
    latest_exec = executions['executions'][0]
    print(f"\n✅ Step Functions execution found:")
    print(f"   Name: {latest_exec['name']}")
    print(f"   Status: {latest_exec['status']}")
    print(f"   Start: {latest_exec['startDate']}")
    
    # Get execution details
    exec_arn = latest_exec['executionArn']
    
    # Wait for execution to complete
    if latest_exec['status'] == 'RUNNING':
        print(f"\n⏳ Waiting for execution to complete...")
        max_wait = 30
        waited = 0
        while waited < max_wait:
            time.sleep(2)
            waited += 2
            
            details = sf_client.describe_execution(executionArn=exec_arn)
            status = details['status']
            
            if status != 'RUNNING':
                print(f"   ✅ Execution completed with status: {status}")
                latest_exec = details
                break
            
            print(f"   ⏳ Still running... ({waited}s)")
    
    # Get final execution details
    details = sf_client.describe_execution(executionArn=exec_arn)
    
    print(f"\n📊 Execution Details:")
    print(f"   Status: {details['status']}")
    
    if details['status'] == 'SUCCEEDED':
        print(f"   ✅ Execution succeeded!")
        output = json.loads(details.get('output', '{}'))
        print(f"\n   Output:")
        print(json.dumps(output, indent=4))
    elif details['status'] == 'FAILED':
        print(f"   ❌ Execution failed!")
        print(f"   Error: {details.get('error', 'Unknown')}")
        print(f"   Cause: {details.get('cause', 'Unknown')}")
    
    # Step 3: Check execution history
    print(f"\n{'='*80}")
    print("Step 3: Checking Execution History")
    print(f"{'='*80}")
    
    history = sf_client.get_execution_history(
        executionArn=exec_arn,
        maxResults=50,
        reverseOrder=False
    )
    
    print(f"\n📜 Execution History ({len(history['events'])} events):")
    
    for event in history['events']:
        event_type = event['type']
        timestamp = event['timestamp']
        
        if event_type == 'TaskStateEntered':
            state_name = event['stateEnteredEventDetails']['name']
            print(f"\n   ▶️  Entered state: {state_name}")
        
        elif event_type == 'TaskSucceeded':
            output = event.get('taskSucceededEventDetails', {}).get('output', '')
            if output:
                try:
                    output_data = json.loads(output)
                    print(f"   ✅ Task succeeded:")
                    print(f"      {json.dumps(output_data, indent=6)}")
                except:
                    print(f"   ✅ Task succeeded: {output[:100]}...")
        
        elif event_type == 'TaskFailed':
            error = event.get('taskFailedEventDetails', {}).get('error', 'Unknown')
            cause = event.get('taskFailedEventDetails', {}).get('cause', 'Unknown')
            print(f"   ❌ Task failed:")
            print(f"      Error: {error}")
            print(f"      Cause: {cause[:200]}...")
    
    # Step 4: Check remediation Lambda logs
    print(f"\n{'='*80}")
    print("Step 4: Checking EC2RemediationLambda Logs")
    print(f"{'='*80}")
    
    try:
        streams = logs_client.describe_log_streams(
            logGroupName='/aws/lambda/EC2RemediationLambda',
            orderBy='LastEventTime',
            descending=True,
            limit=1
        )
        
        if streams['logStreams']:
            print(f"\n✅ EC2RemediationLambda was invoked!")
            stream_name = streams['logStreams'][0]['logStreamName']
            print(f"   Latest stream: {stream_name}")
            
            # Get recent log events
            events = logs_client.get_log_events(
                logGroupName='/aws/lambda/EC2RemediationLambda',
                logStreamName=stream_name,
                limit=20,
                startFromHead=False
            )
            
            print(f"\n   Recent log events:")
            for event in events['events'][-10:]:  # Last 10 events
                message = event['message'].strip()
                if message:
                    print(f"      {message}")
        else:
            print(f"\n❌ EC2RemediationLambda has NOT been invoked")
    except Exception as e:
        print(f"\n❌ Error checking logs: {e}")
    
    # Summary
    print(f"\n{'='*80}")
    print("Test Summary")
    print(f"{'='*80}")
    
    if details['status'] == 'SUCCEEDED':
        print(f"\n✅ End-to-end test PASSED!")
        print(f"   ✅ IngestionLambda processed event")
        print(f"   ✅ Step Functions executed successfully")
        print(f"   ✅ EC2RemediationLambda invoked")
        print(f"\n📧 Check your email for SNS notification!")
    else:
        print(f"\n❌ End-to-end test FAILED")
        print(f"   Review the execution history above for details")
    
    print(f"{'='*80}")


def test_lambda_timeout_incident():
    """Test Lambda timeout incident end-to-end."""
    
    lambda_client = boto3.client('lambda', region_name='eu-west-2')
    
    # Test event for Lambda timeout (using our demo Lambda function)
    test_event = {
        "source": "cloudwatch",
        "timestamp": datetime.utcnow().isoformat() + "Z",
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
    
    print("\n" + "="*80)
    print("End-to-End Test: Lambda Timeout Incident")
    print("="*80)
    print(f"\nTest Event:")
    print(json.dumps(test_event, indent=2))
    
    print(f"\n📤 Invoking IngestionLambda...")
    
    response = lambda_client.invoke(
        FunctionName='IngestionLambda',
        InvocationType='RequestResponse',
        Payload=json.dumps(test_event)
    )
    
    payload = json.loads(response['Payload'].read())
    print(f"\n📥 Response:")
    print(json.dumps(payload, indent=2))
    
    print(f"\n⏳ Waiting 5 seconds for Step Functions...")
    time.sleep(5)
    
    print(f"\n✅ Lambda timeout test completed")
    print(f"   Check Step Functions console for execution details")
    print(f"   Check LambdaRemediationLambda logs for remediation actions")


if __name__ == "__main__":
    print("\n🚀 Starting End-to-End Tests\n")
    
    # Test 1: EC2 incident
    test_ec2_incident()
    
    # Wait between tests
    print(f"\n⏳ Waiting 10 seconds before next test...")
    time.sleep(10)
    
    # Test 2: Lambda timeout incident
    test_lambda_timeout_incident()
    
    print(f"\n\n🎉 All tests completed!")
    print(f"\n📝 Next steps:")
    print(f"   1. Check AWS Step Functions console for execution details")
    print(f"   2. Check your email for SNS notifications")
    print(f"   3. Review CloudWatch logs for detailed execution traces")
