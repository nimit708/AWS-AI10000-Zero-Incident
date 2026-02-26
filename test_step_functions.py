"""
Test Step Functions integration with deployment failure incident.
"""
import json
import boto3
from datetime import datetime
import time

def test_deployment_failure_with_sf():
    """Test deployment failure incident that should trigger Step Functions."""
    
    lambda_client = boto3.client('lambda', region_name='eu-west-2')
    sf_client = boto3.client('stepfunctions', region_name='eu-west-2')
    
    # Test event for deployment failure (this pattern matches!)
    test_event = {
        "source": "demo",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "raw_payload": {
            "event_type": "Deployment Failure",
            "severity": "high",
            "resource_id": "my-app-v2.0",
            "affected_resources": ["my-app-v2.0"],
            "description": "Deployment failed during health check",
            "metadata": {
                "deployment_id": "deploy-test-sf-001",
                "stage": "health_check",
                "error": "Health check failed"
            }
        }
    }
    
    print("="*80)
    print("Testing Step Functions Integration")
    print("="*80)
    print(f"\nTest: Deployment Failure Incident")
    print(f"Expected: Should trigger Step Functions")
    
    # Invoke IngestionLambda
    print(f"\n📤 Invoking IngestionLambda...")
    
    response = lambda_client.invoke(
        FunctionName='IngestionLambda',
        InvocationType='RequestResponse',
        Payload=json.dumps(test_event)
    )
    
    payload = json.loads(response['Payload'].read())
    print(f"\n📥 Lambda Response:")
    print(json.dumps(payload, indent=2))
    
    # Wait a moment for Step Functions to start
    print(f"\n⏳ Waiting 3 seconds for Step Functions to start...")
    time.sleep(3)
    
    # Check Step Functions executions
    print(f"\n🔍 Checking Step Functions executions...")
    
    state_machine_arn = "arn:aws:states:eu-west-2:923906573163:stateMachine:RemediationStateMachine"
    
    executions = sf_client.list_executions(
        stateMachineArn=state_machine_arn,
        maxResults=5
    )
    
    if executions['executions']:
        print(f"\n✅ Found {len(executions['executions'])} Step Functions executions:")
        for exec in executions['executions']:
            print(f"\n   Execution: {exec['name']}")
            print(f"   Status: {exec['status']}")
            print(f"   Start: {exec['startDate']}")
            
            # Get execution details
            details = sf_client.describe_execution(
                executionArn=exec['executionArn']
            )
            
            print(f"   Input: {details.get('input', 'N/A')[:200]}...")
            
            if exec['status'] == 'FAILED':
                print(f"   ❌ Execution failed!")
                if 'stopDate' in exec:
                    print(f"   Stop: {exec['stopDate']}")
            elif exec['status'] == 'SUCCEEDED':
                print(f"   ✅ Execution succeeded!")
                print(f"   Output: {details.get('output', 'N/A')[:200]}...")
            elif exec['status'] == 'RUNNING':
                print(f"   ⏳ Execution still running...")
    else:
        print(f"\n❌ No Step Functions executions found")
        print(f"   Step Functions was NOT triggered")
    
    # Check DeploymentRemediationLambda logs
    print(f"\n🔍 Checking DeploymentRemediationLambda logs...")
    
    logs_client = boto3.client('logs', region_name='eu-west-2')
    
    try:
        streams = logs_client.describe_log_streams(
            logGroupName='/aws/lambda/DeploymentRemediationLambda',
            orderBy='LastEventTime',
            descending=True,
            limit=1
        )
        
        if streams['logStreams']:
            print(f"   ✅ DeploymentRemediationLambda has been invoked!")
            stream_name = streams['logStreams'][0]['logStreamName']
            print(f"   Latest stream: {stream_name}")
        else:
            print(f"   ❌ DeploymentRemediationLambda has NOT been invoked")
    except Exception as e:
        print(f"   ❌ Error checking logs: {e}")
    
    print(f"\n{'='*80}")
    print("Test Complete")
    print(f"{'='*80}")

if __name__ == "__main__":
    test_deployment_failure_with_sf()
