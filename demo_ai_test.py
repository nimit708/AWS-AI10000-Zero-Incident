"""
AI-Powered Demo Test
Tests the AI remediation with improved Bedrock prompts for reliable results.
"""
import boto3
import json
import time
from datetime import datetime

def test_lambda_timeout_ai():
    """Test Lambda timeout with AI remediation"""
    print("="*80)
    print("  AI-POWERED INCIDENT REMEDIATION DEMO")
    print("="*80)
    print("\nScenario: Lambda Function Timeout")
    print("Expected: AI finds match, provides diagnostic steps, executes successfully\n")
    
    lambda_client = boto3.client('lambda', region_name='eu-west-2')
    
    timestamp = datetime.utcnow().isoformat() + 'Z'
    event = {
        "source": "aws.cloudwatch",
        "detail-type": "CloudWatch Alarm State Change",
        "timestamp": timestamp,
        "time": timestamp,
        "raw_payload": {
            "detail": {
                "alarmName": "Lambda-Timeout-IngestionLambda",
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
                                    "FunctionName": "IngestionLambda"
                                }
                            }
                        }
                    }]
                }
            }
        }
    }
    
    print("📤 Sending Lambda Timeout event...")
    print("   Function: IngestionLambda")
    print("   Metric: Duration (timeout)")
    
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
        
        print(f"\n✅ Incident Created Successfully")
        print(f"   Incident ID: {incident_id}")
        print(f"   Routing Path: {routing_path}")
        print(f"   Confidence: {confidence}")
        print(f"   Processing Time: {body.get('processing_time_seconds')}s")
        
        if routing_path == 'fast_path':
            print(f"\n🤖 AI Remediation Path Selected!")
            print(f"   Confidence: {confidence} (threshold: 0.85)")
        
        # Wait for processing
        print(f"\n⏳ Waiting 8 seconds for AI remediation...")
        time.sleep(8)
        
        # Check logs
        print(f"\n📋 Checking execution logs...")
        logs_client = boto3.client('logs', region_name='eu-west-2')
        
        try:
            log_events = logs_client.filter_log_events(
                logGroupName='/aws/lambda/IngestionLambda',
                filterPattern=incident_id,
                limit=50
            )
            
            # Look for key events
            bedrock_called = False
            steps_executed = 0
            steps_succeeded = 0
            remediation_success = False
            
            for event in log_events.get('events', []):
                message = event['message']
                
                if 'Querying Bedrock AI Agent' in message:
                    bedrock_called = True
                    print("   ✅ Bedrock AI Agent queried")
                
                if 'Agent response - Match: True' in message:
                    print("   ✅ High-confidence match found")
                
                if 'Executing step' in message and '/4:' in message:
                    steps_executed += 1
                
                if 'Successfully executed' in message:
                    steps_succeeded += 1
                    # Extract what was executed
                    if 'lambda.get_function' in message:
                        print(f"   ✅ Step {steps_succeeded}: Retrieved function configuration")
                    elif 'lambda.get_function_configuration' in message:
                        print(f"   ✅ Step {steps_succeeded}: Retrieved function settings")
                
                if 'All remediation steps completed successfully' in message:
                    remediation_success = True
                    print("   ✅ All remediation steps completed!")
                
                if 'Published notification' in message:
                    print("   ✅ SNS notification sent with Bedrock summary")
            
            # Summary
            print(f"\n📊 Execution Summary:")
            print(f"   Bedrock AI: {'✅ Used' if bedrock_called else '❌ Not used'}")
            print(f"   Steps Executed: {steps_executed}")
            print(f"   Steps Succeeded: {steps_succeeded}")
            print(f"   Remediation: {'✅ SUCCESS' if remediation_success else '⚠️  Partial/Failed'}")
            
            # Check DynamoDB
            print(f"\n💾 Checking DynamoDB...")
            dynamodb = boto3.resource('dynamodb', region_name='eu-west-2')
            table = dynamodb.Table('incident-tracking-table')
            
            db_response = table.query(
                KeyConditionExpression='incident_id = :id',
                ExpressionAttributeValues={':id': incident_id}
            )
            
            if db_response['Items']:
                item = db_response['Items'][0]
                print(f"   ✅ Incident logged in DynamoDB")
                print(f"   Status: {item.get('status')}")
                print(f"   Routing: {item.get('routing_path')}")
            
            print(f"\n📧 Check email: sharmanimit18@outlook.com")
            print(f"   Subject: AWS Incident {'Resolved' if remediation_success else 'Alert'}")
            
            return remediation_success
            
        except Exception as e:
            print(f"   ⚠️  Could not check logs: {e}")
            return False
    else:
        print(f"❌ Test Failed")
        print(f"   Status Code: {result['statusCode']}")
        print(f"   Response: {result}")
        return False

if __name__ == '__main__':
    success = test_lambda_timeout_ai()
    
    print("\n" + "="*80)
    if success:
        print("  ✅ DEMO SUCCESSFUL - AI REMEDIATION WORKING!")
    else:
        print("  ⚠️  DEMO COMPLETED - Check logs for details")
    print("="*80)
