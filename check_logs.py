"""
Script to check CloudWatch logs for Lambda errors.
"""
import boto3
from datetime import datetime, timedelta

def check_lambda_logs():
    """Check recent Lambda logs for errors."""
    
    logs_client = boto3.client('logs', region_name='eu-west-2')
    log_group = '/aws/lambda/IngestionLambda'
    
    # Get logs from last 30 minutes
    start_time = int((datetime.utcnow() - timedelta(minutes=30)).timestamp() * 1000)
    end_time = int(datetime.utcnow().timestamp() * 1000)
    
    print(f"Checking logs for {log_group}...")
    print(f"Time range: Last 30 minutes\n")
    
    try:
        # Get log streams
        streams_response = logs_client.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=5
        )
        
        if not streams_response['logStreams']:
            print("No log streams found")
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
            print("No log events found in time range")
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
        raise

if __name__ == "__main__":
    check_lambda_logs()
