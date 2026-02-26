"""
Check the status of recent Step Functions executions.
"""
import boto3
import json
from datetime import datetime, timedelta

def check_executions():
    """Check recent Step Functions executions."""
    
    sf_client = boto3.client('stepfunctions', region_name='eu-west-2')
    logs_client = boto3.client('logs', region_name='eu-west-2')
    
    state_machine_arn = "arn:aws:states:eu-west-2:923906573163:stateMachine:RemediationStateMachine"
    
    print("="*80)
    print("Step Functions Execution Status")
    print("="*80)
    
    # Get recent executions
    executions = sf_client.list_executions(
        stateMachineArn=state_machine_arn,
        maxResults=10
    )
    
    if not executions['executions']:
        print("\n❌ No executions found")
        return
    
    print(f"\n📊 Found {len(executions['executions'])} recent executions:\n")
    
    for i, exec in enumerate(executions['executions'], 1):
        print(f"{i}. Execution: {exec['name']}")
        print(f"   Status: {exec['status']}")
        print(f"   Start: {exec['startDate']}")
        
        if 'stopDate' in exec:
            duration = (exec['stopDate'] - exec['startDate']).total_seconds()
            print(f"   Stop: {exec['stopDate']}")
            print(f"   Duration: {duration:.1f}s")
        
        # Get execution details
        details = sf_client.describe_execution(executionArn=exec['executionArn'])
        
        # Show input
        input_data = json.loads(details.get('input', '{}'))
        incident_id = input_data.get('incident', {}).get('incident_id', 'N/A')
        event_type = input_data.get('incident', {}).get('event_type', 'N/A')
        pattern = input_data.get('pattern', 'N/A')
        
        print(f"   Incident ID: {incident_id}")
        print(f"   Event Type: {event_type}")
        print(f"   Pattern: {pattern}")
        
        # Show output/error
        if exec['status'] == 'SUCCEEDED':
            output = json.loads(details.get('output', '{}'))
            print(f"   ✅ Output:")
            
            # Extract key information
            remediation = output.get('remediation_result', {})
            if isinstance(remediation, dict):
                payload = remediation.get('Payload', {})
                if isinstance(payload, dict):
                    success = payload.get('success', False)
                    actions = payload.get('actions_performed', [])
                    print(f"      Success: {success}")
                    if actions:
                        print(f"      Actions: {', '.join(actions[:3])}")
        
        elif exec['status'] == 'FAILED':
            print(f"   ❌ Error: {details.get('error', 'Unknown')}")
            cause = details.get('cause', '')
            if cause:
                try:
                    cause_data = json.loads(cause)
                    print(f"      {cause_data.get('errorMessage', cause[:100])}")
                except:
                    print(f"      {cause[:100]}")
        
        elif exec['status'] == 'RUNNING':
            # Get execution history to see current state
            history = sf_client.get_execution_history(
                executionArn=exec['executionArn'],
                maxResults=50,
                reverseOrder=True
            )
            
            # Find the most recent state
            for event in history['events']:
                if event['type'] == 'TaskStateEntered':
                    state_name = event['stateEnteredEventDetails']['name']
                    print(f"   ⏳ Current state: {state_name}")
                    break
        
        print()
    
    # Check remediation Lambda logs
    print("="*80)
    print("Recent Remediation Lambda Invocations")
    print("="*80)
    
    remediation_lambdas = [
        'EC2RemediationLambda',
        'LambdaRemediationLambda'
    ]
    
    for lambda_name in remediation_lambdas:
        print(f"\n{lambda_name}:")
        try:
            streams = logs_client.describe_log_streams(
                logGroupName=f'/aws/lambda/{lambda_name}',
                orderBy='LastEventTime',
                descending=True,
                limit=1
            )
            
            if streams['logStreams']:
                stream = streams['logStreams'][0]
                last_event_time = datetime.fromtimestamp(stream['lastEventTime'] / 1000)
                
                # Check if recent (within last 10 minutes)
                if datetime.now() - last_event_time < timedelta(minutes=10):
                    print(f"   ✅ Recently invoked ({last_event_time.strftime('%H:%M:%S')})")
                    
                    # Get recent logs
                    events = logs_client.get_log_events(
                        logGroupName=f'/aws/lambda/{lambda_name}',
                        logStreamName=stream['logStreamName'],
                        limit=30,
                        startFromHead=False
                    )
                    
                    # Look for key messages
                    for event in events['events'][-15:]:
                        message = event['message'].strip()
                        if any(keyword in message.lower() for keyword in ['success', 'failed', 'error', 'remediation result']):
                            print(f"      {message}")
                else:
                    print(f"   ⏰ Last invoked: {last_event_time.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print(f"   ❌ No invocations found")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    check_executions()
