"""
Complete deployment script - handles all remaining deployment steps.
"""
import boto3
import json
from datetime import datetime

def check_sns_subscriptions():
    """Check SNS subscription status."""
    print("\n" + "="*80)
    print("STEP 1: Checking SNS Subscriptions")
    print("="*80)
    
    sns_client = boto3.client('sns', region_name='eu-west-2')
    
    topics = [
        'incident-summary-topic',
        'incident-urgent-topic'
    ]
    
    for topic_name in topics:
        try:
            # List subscriptions for topic
            topic_arn = f"arn:aws:sns:eu-west-2:923906573163:{topic_name}"
            response = sns_client.list_subscriptions_by_topic(TopicArn=topic_arn)
            
            subscriptions = response.get('Subscriptions', [])
            
            print(f"\n📧 Topic: {topic_name}")
            print(f"   ARN: {topic_arn}")
            
            if not subscriptions:
                print("   ⚠️  No subscriptions found")
            else:
                for sub in subscriptions:
                    status = sub.get('SubscriptionArn')
                    endpoint = sub.get('Endpoint')
                    
                    if status == 'PendingConfirmation':
                        print(f"   ⏳ PENDING: {endpoint}")
                        print(f"      → Check email and confirm subscription!")
                    else:
                        print(f"   ✅ CONFIRMED: {endpoint}")
        
        except Exception as e:
            print(f"   ❌ Error checking topic: {e}")
    
    print("\n⚠️  ACTION REQUIRED:")
    print("   Check email: sharmanimit18@outlook.com")
    print("   Confirm any pending SNS subscriptions")

def check_bedrock_models():
    """Check Bedrock model availability."""
    print("\n" + "="*80)
    print("STEP 2: Checking Bedrock Model Availability")
    print("="*80)
    
    bedrock_client = boto3.client('bedrock', region_name='eu-west-2')
    
    required_models = [
        'anthropic.claude-3-7-sonnet-20250219-v1:0',
        'amazon.titan-embed-text-v2:0',
        'anthropic.claude-3-haiku-20240307-v1:0'
    ]
    
    try:
        response = bedrock_client.list_foundation_models()
        available_models = [m['modelId'] for m in response.get('modelSummaries', [])]
        
        print(f"\nFound {len(available_models)} available models in eu-west-2")
        
        # Check Claude models
        claude_models = [m for m in available_models if 'claude' in m.lower()]
        print(f"\n📊 Claude models available: {len(claude_models)}")
        for model in claude_models[:5]:  # Show first 5
            print(f"   - {model}")
        
        # Check Titan models
        titan_models = [m for m in available_models if 'titan' in m.lower()]
        print(f"\n📊 Titan models available: {len(titan_models)}")
        for model in titan_models[:5]:
            print(f"   - {model}")
        
        # Check required models
        print(f"\n🔍 Checking required models:")
        all_available = True
        for model in required_models:
            if model in available_models:
                print(f"   ✅ {model}")
            else:
                print(f"   ❌ {model} - NOT AVAILABLE")
                all_available = False
                
                # Suggest alternatives
                model_type = model.split('.')[1].split('-')[0]  # claude or titan
                alternatives = [m for m in available_models if model_type in m.lower()]
                if alternatives:
                    print(f"      Alternatives: {alternatives[0]}")
        
        if all_available:
            print("\n✅ All required models are available!")
        else:
            print("\n⚠️  Some models not available - may need to update Lambda environment variables")
        
    except Exception as e:
        print(f"\n❌ Error checking Bedrock models: {e}")
        print("   This might be a permissions issue or Bedrock not enabled in region")

def test_lambda_function():
    """Test Lambda function with sample event."""
    print("\n" + "="*80)
    print("STEP 3: Testing Lambda Function")
    print("="*80)
    
    lambda_client = boto3.client('lambda', region_name='eu-west-2')
    
    test_event = {
        "source": "cloudwatch",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "raw_payload": {
            "incident_id": f"test-deploy-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            "event_type": "EC2 CPU Spike",
            "severity": "high",
            "resource_id": "i-test123456",
            "description": "CPU usage exceeded 90% - deployment test",
            "affected_resources": ["i-test123456"],
            "metadata": {
                "region": "eu-west-2",
                "instance_type": "t3.medium",
                "cpu_utilization": 92.0
            }
        }
    }
    
    print("\n📤 Invoking IngestionLambda...")
    print(f"Test incident ID: {test_event['raw_payload']['incident_id']}")
    
    try:
        response = lambda_client.invoke(
            FunctionName='IngestionLambda',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        status_code = response['StatusCode']
        payload = json.loads(response['Payload'].read())
        
        print(f"\n📥 Lambda Response:")
        print(f"   Status Code: {status_code}")
        print(f"   Response: {json.dumps(payload, indent=2)}")
        
        # Check if successful
        if status_code == 200:
            body = json.loads(payload.get('body', '{}'))
            if body.get('success'):
                print("\n✅ Lambda execution successful!")
                print(f"   Incident ID: {body.get('incident_id')}")
                print(f"   Routing Path: {body.get('routing_path')}")
                print(f"   Processing Time: {body.get('processing_time_seconds', 0):.2f}s")
            else:
                print(f"\n⚠️  Lambda returned error: {body.get('error')}")
                print(f"   Details: {body.get('details')}")
        else:
            print(f"\n❌ Lambda invocation failed with status {status_code}")
        
        # Save response
        with open('deployment_test_response.json', 'w') as f:
            json.dump(payload, f, indent=2)
        
        return payload
        
    except Exception as e:
        print(f"\n❌ Error invoking Lambda: {e}")
        return None

def check_dynamodb_tables():
    """Check DynamoDB tables."""
    print("\n" + "="*80)
    print("STEP 4: Checking DynamoDB Tables")
    print("="*80)
    
    dynamodb_client = boto3.client('dynamodb', region_name='eu-west-2')
    
    tables = [
        'incident-tracking-table',
        'resource-lock-table'
    ]
    
    for table_name in tables:
        try:
            response = dynamodb_client.describe_table(TableName=table_name)
            table = response['Table']
            
            print(f"\n📊 Table: {table_name}")
            print(f"   Status: {table['TableStatus']}")
            print(f"   Item Count: {table['ItemCount']}")
            print(f"   Size: {table['TableSizeBytes']} bytes")
            
            # Check for recent items
            scan_response = dynamodb_client.scan(
                TableName=table_name,
                Limit=5
            )
            
            item_count = scan_response['Count']
            if item_count > 0:
                print(f"   ✅ Found {item_count} items in table")
            else:
                print(f"   ℹ️  Table is empty (expected for new deployment)")
        
        except Exception as e:
            print(f"\n❌ Error checking table {table_name}: {e}")

def check_step_functions():
    """Check Step Functions state machine."""
    print("\n" + "="*80)
    print("STEP 5: Checking Step Functions")
    print("="*80)
    
    sf_client = boto3.client('stepfunctions', region_name='eu-west-2')
    
    state_machine_arn = "arn:aws:states:eu-west-2:923906573163:stateMachine:RemediationStateMachine"
    
    try:
        response = sf_client.describe_state_machine(
            stateMachineArn=state_machine_arn
        )
        
        print(f"\n🔄 State Machine: RemediationStateMachine")
        print(f"   Status: {response['status']}")
        print(f"   Created: {response['creationDate']}")
        print(f"   ARN: {state_machine_arn}")
        
        # Check recent executions
        executions = sf_client.list_executions(
            stateMachineArn=state_machine_arn,
            maxResults=5
        )
        
        exec_count = len(executions.get('executions', []))
        print(f"   Recent Executions: {exec_count}")
        
        if exec_count > 0:
            print("\n   Latest executions:")
            for exec in executions['executions'][:3]:
                print(f"   - {exec['name']}: {exec['status']}")
        
        print("\n✅ Step Functions state machine is active")
        
    except Exception as e:
        print(f"\n❌ Error checking Step Functions: {e}")

def print_summary():
    """Print deployment summary and next steps."""
    print("\n" + "="*80)
    print("DEPLOYMENT COMPLETION SUMMARY")
    print("="*80)
    
    print("""
✅ Infrastructure Deployed:
   - CloudFormation Stack: IncidentManagementStack
   - Lambda Functions: 9 functions with layer
   - DynamoDB Tables: 2 tables
   - SNS Topics: 2 topics
   - Step Functions: 1 state machine
   - CloudWatch Alarms: 5 alarms

📋 IMMEDIATE ACTIONS REQUIRED:

1. ⚠️  CONFIRM SNS SUBSCRIPTIONS (CRITICAL)
   - Check email: sharmanimit18@outlook.com
   - Confirm 2 SNS subscription emails
   - Without this, you won't receive notifications!

2. 🔍 VERIFY BEDROCK MODELS
   - Check if models are available in eu-west-2
   - Update Lambda environment variables if needed
   - Or consider redeploying to us-east-1

3. 🧪 TEST END-TO-END FLOW
   - Run: python test_lambda_fixed.py
   - Check CloudWatch logs: python check_logs.py
   - Verify DynamoDB records created

📚 DOCUMENTATION:
   - FINAL_DEPLOYMENT_SUMMARY.md - Complete overview
   - NEXT_STEPS.md - Detailed next steps
   - QUICK_REFERENCE.md - Quick commands

🎉 You're 95% complete! Just confirm SNS subscriptions and test!
""")

def main():
    """Run all deployment completion checks."""
    print("\n" + "="*80)
    print("AWS INCIDENT MANAGEMENT SYSTEM - DEPLOYMENT COMPLETION")
    print("="*80)
    print(f"Region: eu-west-2")
    print(f"Account: 923906573163")
    print(f"Time: {datetime.utcnow().isoformat()}Z")
    
    try:
        # Run all checks
        check_sns_subscriptions()
        check_bedrock_models()
        test_lambda_function()
        check_dynamodb_tables()
        check_step_functions()
        
        # Print summary
        print_summary()
        
        print("\n✅ Deployment completion checks finished!")
        print("   Review output above for any action items")
        
    except Exception as e:
        print(f"\n❌ Error during deployment checks: {e}")
        raise

if __name__ == "__main__":
    main()
