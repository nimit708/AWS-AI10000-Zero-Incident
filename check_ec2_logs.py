"""
Check EC2RemediationLambda CloudWatch logs.
"""
import boto3
from datetime import datetime, timedelta

def check_ec2_logs():
    """Check EC2 remediation Lambda logs."""
    
    logs_client = boto3.client('logs', region_name='eu-west-2')
    log_group = '/aws/lambda/EC2RemediationLambda'
    
    # Get logs from last 30 minutes
    start_time = int((datetime.utcnow() - timedelta(minutes=30)).timestamp() * 1000)
    end_time = int(datetime.utcnow().timestamp() * 1000)
    
    print("="*80)
    print(f"Checking logs for {log_group}")
    print("="*80)
    print(f"Time range: Last 30 minutes\n")
    
    try:
        # Check if log group exists
        try:
            logs_client.describe_log_groups(logGroupNamePrefix=log_group)
        except Exception as e:
            print(f"❌ Log group not found: {log_group}")
            print(f"   This means EC2RemediationLambda has never been invoked")
            print(f"\n💡 Reason: The test event didn't match the EC2 pattern")
            print(f"   Run: python test_ec2_remediation.py to test with correct format")
            return
        
        # Get log streams
        streams_response = logs_client.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=5
        )
        
        if not streams_response['logStreams']:
            print("ℹ️  No log streams found")
            print("   This means EC2RemediationLambda has never been invoked")
            print(f"\n💡 Reason: The test event didn't match the EC2 pattern")
            print(f"   Run: python test_ec2_remediation.py to test with correct format")
            return
        
        # Get events from most recent stream
        latest_stream = streams_response['logStreams'][0]
        stream_name = latest_stream['logStreamName']
        
        print(f"Latest log stream: {stream_name}\n")
        
        events_response = logs_client.get_log_events(
            logGroupName=log_group,
            logStreamName=stream_name,
            startTime=start_time,
            endTime=end_time,
            limit=100
        )
        
        events = events_response['events']
        
        if not events:
            print("ℹ️  No log events found in time range")
            print("   EC2RemediationLambda hasn't been invoked recently")
            return
        
        print(f"Found {len(events)} log events:\n")
        print("=" * 80)
        
        for event in events:
            timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
            message = event['message']
            print(f"[{timestamp}] {message}")
        
        print("=" * 80)
        
        # Look for errors
        errors = [e for e in events if 'ERROR' in e['message'] or 'error' in e['message'].lower()]
        
        if errors:
            print(f"\n⚠️ Found {len(errors)} error messages:")
            for error in errors:
                print(f"\n{error['message']}")
        else:
            print("\n✅ No errors found in recent logs")
        
    except Exception as e:
        print(f"❌ Error checking logs: {e}")

def check_all_remediation_lambdas():
    """Check all remediation Lambda functions for recent invocations."""
    
    lambda_client = boto3.client('lambda', region_name='eu-west-2')
    logs_client = boto3.client('logs', region_name='eu-west-2')
    
    remediation_functions = [
        'EC2RemediationLambda',
        'LambdaRemediationLambda',
        'SSLRemediationLambda',
        'NetworkRemediationLambda',
        'DeploymentRemediationLambda',
        'ServiceRemediationLambda'
    ]
    
    print("\n" + "="*80)
    print("Checking All Remediation Lambda Functions")
    print("="*80)
    
    for function_name in remediation_functions:
        print(f"\n📦 {function_name}")
        
        try:
            # Get function info
            response = lambda_client.get_function(FunctionName=function_name)
            
            # Check for recent invocations
            log_group = f'/aws/lambda/{function_name}'
            
            try:
                streams = logs_client.describe_log_streams(
                    logGroupName=log_group,
                    orderBy='LastEventTime',
                    descending=True,
                    limit=1
                )
                
                if streams['logStreams']:
                    last_event = streams['logStreams'][0].get('lastEventTime')
                    if last_event:
                        last_time = datetime.fromtimestamp(last_event / 1000)
                        print(f"   Last invocation: {last_time}")
                    else:
                        print(f"   Status: Never invoked")
                else:
                    print(f"   Status: Never invoked")
                    
            except logs_client.exceptions.ResourceNotFoundException:
                print(f"   Status: Never invoked (no log group)")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "="*80)
    print("\n💡 To trigger EC2 remediation:")
    print("   Run: python test_ec2_remediation.py")

if __name__ == "__main__":
    check_ec2_logs()
    check_all_remediation_lambdas()
