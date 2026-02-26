"""
Clean End-to-End Test
Tests the complete incident management flow from scratch.
"""
import boto3
import json
import time
from datetime import datetime

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_e2e_flow():
    """Complete E2E test of the incident management system."""
    
    lambda_client = boto3.client('lambda', region_name='eu-west-2')
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-2')
    
    print_section("CLEAN END-TO-END TEST - INCIDENT MANAGEMENT SYSTEM")
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    print(f"Region: eu-west-2")
    
    # Test 1: Lambda Timeout (should go to fast_path with high confidence)
    print_section("TEST 1: Lambda Timeout Incident")
    
    timestamp = datetime.utcnow().isoformat() + 'Z'
    event = {
        "source": "aws.cloudwatch",
        "detail-type": "CloudWatch Alarm State Change",
        "timestamp": timestamp,
        "time": timestamp,
        "raw_payload": {
            "detail": {
                "alarmName": "Lambda-Timeout-IncidentDemo-TimeoutTest",
                "state": {
                    "value": "ALARM",
                    "reason": "Threshold Crossed: Lambda function exceeded timeout threshold"
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
    
    print("Sending Lambda Timeout event...")
    response = lambda_client.invoke(
        FunctionName='IngestionLambda',
        InvocationType='RequestResponse',
        Payload=json.dumps(event)
    )
    
    result = json.loads(response['Payload'].read())
    
    if result['statusCode'] == 200:
        body = json.loads(result['body'])
        incident_id = body.get('incident_id')
        routing_path = body.get('routing_path')
        confidence = body.get('confidence')
        
        print(f"✅ Incident Created")
        print(f"   Incident ID: {incident_id}")
        print(f"   Routing Path: {routing_path}")
        print(f"   Confidence: {confidence}")
        print(f"   Processing Time: {body.get('processing_time_seconds')}s")
        
        # Wait for processing
        print("\nWaiting 3 seconds for processing...")
        time.sleep(3)
        
        # Check DynamoDB
        print("\nChecking DynamoDB record...")
        table = dynamodb.Table('incident-tracking-table')
        
        try:
            db_response = table.query(
                KeyConditionExpression='incident_id = :id',
                ExpressionAttributeValues={':id': incident_id}
            )
            
            if db_response['Items']:
                item = db_response['Items'][0]
                print(f"✅ DynamoDB Record Found")
                print(f"   Status: {item.get('status')}")
                print(f"   Event Type: {item.get('event_type')}")
                print(f"   Routing Path: {item.get('routing_path')}")
                print(f"   Confidence: {item.get('confidence')}")
                
                if 'resolution_steps' in item:
                    steps = item['resolution_steps']
                    print(f"   Resolution Steps: {len(steps)} steps")
                    for i, step in enumerate(steps[:3], 1):  # Show first 3
                        print(f"      {i}. {step}")
            else:
                print("❌ DynamoDB record not found")
                
        except Exception as e:
            print(f"❌ Error querying DynamoDB: {e}")
        
        # Check CloudWatch Logs
        print("\nChecking CloudWatch Logs...")
        logs_client = boto3.client('logs', region_name='eu-west-2')
        
        try:
            log_events = logs_client.filter_log_events(
                logGroupName='/aws/lambda/IngestionLambda',
                filterPattern=incident_id,
                limit=20
            )
            
            key_events = []
            for event in log_events.get('events', []):
                message = event['message']
                if any(keyword in message for keyword in [
                    'Bedrock', 'fast path', 'Successfully executed', 
                    'Generated', 'Published notification', 'Updated incident'
                ]):
                    key_events.append(message.strip())
            
            if key_events:
                print(f"✅ Found {len(key_events)} key log entries:")
                for msg in key_events[:5]:  # Show first 5
                    # Extract just the important part
                    if '[INFO]' in msg:
                        msg = msg.split('[INFO]')[-1].strip()
                    elif '[ERROR]' in msg:
                        msg = msg.split('[ERROR]')[-1].strip()
                    print(f"   • {msg[:100]}")
            else:
                print("⚠️  No key log entries found yet")
                
        except Exception as e:
            print(f"⚠️  Could not check logs: {e}")
        
        return {
            'success': True,
            'incident_id': incident_id,
            'routing_path': routing_path,
            'confidence': confidence
        }
    else:
        print(f"❌ Test Failed")
        print(f"   Status Code: {result['statusCode']}")
        print(f"   Response: {result}")
        return {'success': False}

def check_sns_subscriptions():
    """Check SNS topic subscriptions."""
    print_section("SNS SUBSCRIPTION STATUS")
    
    sns_client = boto3.client('sns', region_name='eu-west-2')
    
    topics = [
        ('Summary Topic', 'arn:aws:sns:eu-west-2:923906573163:incident-summary-topic'),
        ('Urgent Topic', 'arn:aws:sns:eu-west-2:923906573163:incident-urgent-topic')
    ]
    
    for name, arn in topics:
        try:
            response = sns_client.list_subscriptions_by_topic(TopicArn=arn)
            subscriptions = response.get('Subscriptions', [])
            
            confirmed = [s for s in subscriptions if s['SubscriptionArn'] != 'PendingConfirmation']
            
            print(f"\n{name}:")
            print(f"   ARN: {arn}")
            print(f"   Subscriptions: {len(confirmed)} confirmed")
            
            for sub in confirmed:
                print(f"   • {sub['Protocol']}: {sub['Endpoint']}")
                
        except Exception as e:
            print(f"❌ Error checking {name}: {e}")

def check_bedrock_access():
    """Verify Bedrock model access."""
    print_section("BEDROCK MODEL ACCESS")
    
    bedrock_client = boto3.client('bedrock-runtime', region_name='eu-west-2')
    
    models = [
        ('Agent Model (Sonnet)', 'anthropic.claude-3-7-sonnet-20250219-v1:0'),
        ('Summary Model (Haiku)', 'anthropic.claude-3-haiku-20240307-v1:0'),
    ]
    
    for name, model_id in models:
        try:
            response = bedrock_client.invoke_model(
                modelId=model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": "test"}]
                })
            )
            print(f"✅ {name}")
            print(f"   Model ID: {model_id}")
        except Exception as e:
            print(f"❌ {name}: {e}")

def main():
    """Run complete E2E test suite."""
    
    # Pre-flight checks
    check_bedrock_access()
    check_sns_subscriptions()
    
    # Main E2E test
    result = test_e2e_flow()
    
    # Summary
    print_section("TEST SUMMARY")
    
    if result.get('success'):
        print("✅ END-TO-END TEST PASSED")
        print(f"\nIncident Details:")
        print(f"  • Incident ID: {result['incident_id']}")
        print(f"  • Routing Path: {result['routing_path']}")
        print(f"  • Confidence: {result['confidence']}")
        print(f"\nWhat to check:")
        print(f"  1. Email inbox (sharmanimit18@outlook.com)")
        print(f"  2. DynamoDB table (incident-tracking-table)")
        print(f"  3. CloudWatch Logs (/aws/lambda/IngestionLambda)")
        print(f"\nExpected behavior:")
        print(f"  • Fast path: AI remediation attempted")
        print(f"  • Bedrock: Summary generated")
        print(f"  • SNS: Email notification sent")
        print(f"  • DynamoDB: Incident record created and updated")
    else:
        print("❌ END-TO-END TEST FAILED")
        print("Check the error messages above for details.")
    
    print("\n" + "="*70)

if __name__ == '__main__':
    main()
