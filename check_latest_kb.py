import boto3
import json
import time

logs = boto3.client('logs', region_name='eu-west-2')
s3 = boto3.client('s3', region_name='eu-west-2')

incident_id = 'e6bc8e79-a96d-468e-bba3-88cd59ee788e'

print("Checking logs for incident:", incident_id)
print("="*80)

time.sleep(3)

# Check logs
response = logs.filter_log_events(
    logGroupName='/aws/lambda/IngestionLambda',
    filterPattern=incident_id,
    limit=50
)

for event in response.get('events', []):
    message = event['message'].strip()
    if 'knowledge' in message.lower() or 'added incident' in message.lower() or 'error' in message.lower():
        print(message)
        print("-"*80)

# Check S3
print("\nChecking S3 bucket...")
try:
    response = s3.list_objects_v2(
        Bucket='incident-kb-923906573163',
        Prefix='incidents/'
    )
    
    if 'Contents' in response:
        print(f"Found {len(response['Contents'])} files")
        for obj in response['Contents']:
            if incident_id in obj['Key']:
                print(f"\n✓ FOUND: {obj['Key']}")
                
                # Read content
                file_obj = s3.get_object(Bucket='incident-kb-923906573163', Key=obj['Key'])
                content = json.loads(file_obj['Body'].read().decode('utf-8'))
                print(json.dumps(content, indent=2))
    else:
        print("No files in KB")
except Exception as e:
    print(f"Error: {e}")
