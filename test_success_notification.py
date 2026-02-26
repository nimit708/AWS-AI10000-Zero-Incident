"""
Test successful remediation notification with Bedrock summary.
This directly tests the SNS notification with Bedrock summarization.
"""
import boto3
import json
from datetime import datetime

def test_send_success_notification():
    """
    Directly test SNS success notification with Bedrock summary.
    This simulates what would happen after a successful remediation.
    """
    sns_client = boto3.client('sns', region_name='eu-west-2')
    bedrock_client = boto3.client('bedrock-runtime', region_name='eu-west-2')
    
    # Test data
    incident_id = "test-success-" + datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    event_type = "Lambda Timeout"
    severity = "medium"
    affected_resources = ["IncidentDemo-TimeoutTest"]
    actions_taken = [
        "Retrieved current Lambda function configuration",
        "Identified timeout value: 3 seconds",
        "Calculated recommended timeout: 6 seconds (2x current)",
        "Updated Lambda function timeout to 6 seconds",
        "Verified function configuration update successful"
    ]
    
    print(f"Testing Bedrock-powered SUCCESS notification...")
    print(f"Incident ID: {incident_id}")
    print(f"Event Type: {event_type}")
    print(f"Actions Taken: {len(actions_taken)} steps")
    
    # Generate Bedrock summary
    print("\n" + "="*60)
    print("Step 1: Generating Bedrock AI Summary...")
    print("="*60)
    
    prompt = f"""Generate a concise, professional incident resolution summary for the following:

Incident Type: {event_type}
Severity: {severity}
Affected Resources: {', '.join(affected_resources)}
Actions Taken:
{chr(10).join(f'- {action}' for action in actions_taken)}

Write a 2-3 sentence summary explaining what happened and how it was resolved. Use clear, non-technical language suitable for stakeholders."""

    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 200,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.3
    }
    
    try:
        response = bedrock_client.invoke_model(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        bedrock_summary = response_body['content'][0]['text'].strip()
        
        print(f"✅ Bedrock Summary Generated:")
        print(f"\n{bedrock_summary}\n")
        
    except Exception as e:
        print(f"❌ Bedrock Error: {e}")
        bedrock_summary = f"Successfully resolved {event_type} incident affecting {len(affected_resources)} resource(s). Performed {len(actions_taken)} remediation action(s) to restore normal operation. System is now operating normally."
        print(f"Using fallback summary: {bedrock_summary}")
    
    # Send SNS notification
    print("="*60)
    print("Step 2: Sending SNS Notification...")
    print("="*60)
    
    message = {
        "incidentId": incident_id,
        "eventType": event_type,
        "severity": severity,
        "affectedResources": affected_resources,
        "actionsPerformed": actions_taken,
        "resolutionTime": "8 seconds",
        "summary": bedrock_summary,
        "timestamp": datetime.utcnow().isoformat() + 'Z'
    }
    
    try:
        sns_response = sns_client.publish(
            TopicArn="arn:aws:sns:eu-west-2:923906573163:incident-summary-topic",
            Subject=f"✅ Remediation Successfully Done: {event_type}",
            Message=json.dumps(message, indent=2),
            MessageAttributes={
                'incident_id': {
                    'DataType': 'String',
                    'StringValue': incident_id
                },
                'event_type': {
                    'DataType': 'String',
                    'StringValue': event_type
                }
            }
        )
        
        message_id = sns_response.get('MessageId')
        print(f"✅ SNS Notification Sent!")
        print(f"   Message ID: {message_id}")
        print(f"   Topic: incident-summary-topic")
        print(f"   Subject: ✅ Remediation Successfully Done: {event_type}")
        
        print("\n" + "="*60)
        print("SUCCESS! Check your email for the notification.")
        print("="*60)
        print(f"\nEmail should contain:")
        print(f"  - Incident ID: {incident_id}")
        print(f"  - AI-generated summary from Bedrock")
        print(f"  - {len(actions_taken)} remediation actions")
        print(f"  - Resolution time: 8 seconds")
        
        return True
        
    except Exception as e:
        print(f"❌ SNS Error: {e}")
        return False

if __name__ == '__main__':
    success = test_send_success_notification()
    exit(0 if success else 1)
