import boto3
import time

logs = boto3.client('logs', region_name='eu-west-2')

# Get recent logs
response = logs.filter_log_events(
    logGroupName='/aws/lambda/IngestionLambda',
    startTime=int((time.time()-300)*1000),
    limit=50
)

print("Recent IngestionLambda logs (last 5 minutes):")
print("="*80)

for event in response.get('events', []):
    message = event['message'].strip()
    if any(keyword in message.lower() for keyword in ['knowledge', 'kb', 'added incident', 'error', 'exception', 'resolved']):
        print(message)
        print("-"*80)
