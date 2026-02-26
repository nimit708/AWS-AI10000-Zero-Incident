"""
Three Demo Scenarios for Incident Management System
These scenarios use the structured path (Step Functions) for reliable, predictable results.
"""
import boto3
import json
import time
from datetime import datetime

lambda_client = boto3.client('lambda', region_name='eu-west-2')
dynamodb = boto3.resource('dynamodb', region_name='eu-west-2')

def print_header(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def wait_and_check_result(incident_id, scenario_name):
    """Wait for processing and check results"""
    print(f"\n⏳ Waiting 5 seconds for processing...")
    time.sleep(5)
    
    # Check DynamoDB
    table = dynamodb.Table('incident-tracking-table')
    try:
        response = table.query(
            KeyConditionExpression='incident_id = :id',
            ExpressionAttributeValues={':id': incident_id}
        )
        
        if response['Items']:
            item = response['Items'][0]
            print(f"\n✅ {scenario_name} - Results:")
            print(f"   Incident ID: {incident_id}")
            print(f"   Status: {item.get('status')}")
            print(f"   Event Type: {item.get('event_type')}")
            print(f"   Routing Path: {item.get('routing_path')}")
            print(f"   Severity: {item.get('severity')}")
            
            if item.get('routing_path') == 'structured_path':
                print(f"   ✅ Routed to Step Functions (reliable remediation)")
            
            return True
        else:
            print(f"❌ No DynamoDB record found")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def scenario_1_ec2_high_cpu():
    """Scenario 1: EC2 High CPU - Structured Path"""
    print_header("SCENARIO 1: EC2 High CPU Utilization")
    
    timestamp = datetime.utcnow().isoformat() + 'Z'
    event = {
        "source": "aws.cloudwatch",
        "detail-type": "CloudWatch Alarm State Change",
        "timestamp": timestamp,
        "time": timestamp,
        "raw_payload": {
            "detail": {
                "alarmName": "EC2-HighCPU-DemoInstance",
                "state": {
                    "value": "ALARM",
                    "reason": "Threshold Crossed: 1 datapoint [95.0] was greater than the threshold (80.0)"
                },
                "configuration": {
                    "metrics": [{
                        "metricStat": {
                            "metric": {
                                "name": "CPUUtilization",
                                "namespace": "AWS/EC2",
                                "dimensions": {
                                    "InstanceId": "i-demo123456"
                                }
                            }
                        }
                    }]
                }
            }
        }
    }
    
    print("📤 Sending EC2 High CPU alarm...")
    print("   Expected: Structured path (Step Functions)")
    print("   Reason: Low confidence or no match from Bedrock")
    
    response = lambda_client.invoke(
        FunctionName='IngestionLambda',
        InvocationType='RequestResponse',
        Payload=json.dumps(event)
    )
    
    result = json.loads(response['Payload'].read())
    
    if result['statusCode'] == 200:
        body = json.loads(result['body'])
        incident_id = body.get('incident_id')
        return wait_and_check_result(incident_id, "EC2 High CPU")
    else:
        print(f"❌ Failed: {result}")
        return False

def scenario_2_lambda_errors():
    """Scenario 2: Lambda Errors - Structured Path"""
    print_header("SCENARIO 2: Lambda Function Errors")
    
    timestamp = datetime.utcnow().isoformat() + 'Z'
    event = {
        "source": "aws.cloudwatch",
        "detail-type": "CloudWatch Alarm State Change",
        "timestamp": timestamp,
        "time": timestamp,
        "raw_payload": {
            "detail": {
                "alarmName": "Lambda-Errors-DemoFunction",
                "state": {
                    "value": "ALARM",
                    "reason": "Threshold Crossed: Lambda function error rate exceeded threshold"
                },
                "configuration": {
                    "metrics": [{
                        "metricStat": {
                            "metric": {
                                "name": "Errors",
                                "namespace": "AWS/Lambda",
                                "dimensions": {
                                    "FunctionName": "DemoFunction"
                                }
                            }
                        }
                    }]
                }
            }
        }
    }
    
    print("📤 Sending Lambda Errors alarm...")
    print("   Expected: Structured path (Step Functions)")
    print("   Reason: Reliable pattern-based remediation")
    
    response = lambda_client.invoke(
        FunctionName='IngestionLambda',
        InvocationType='RequestResponse',
        Payload=json.dumps(event)
    )
    
    result = json.loads(response['Payload'].read())
    
    if result['statusCode'] == 200:
        body = json.loads(result['body'])
        incident_id = body.get('incident_id')
        return wait_and_check_result(incident_id, "Lambda Errors")
    else:
        print(f"❌ Failed: {result}")
        return False

def scenario_3_rds_connection():
    """Scenario 3: RDS Connection Issues - Structured Path"""
    print_header("SCENARIO 3: RDS Connection Issues")
    
    timestamp = datetime.utcnow().isoformat() + 'Z'
    event = {
        "source": "aws.cloudwatch",
        "detail-type": "CloudWatch Alarm State Change",
        "timestamp": timestamp,
        "time": timestamp,
        "raw_payload": {
            "detail": {
                "alarmName": "RDS-ConnectionCount-DemoDB",
                "state": {
                    "value": "ALARM",
                    "reason": "Threshold Crossed: Database connection count exceeded maximum"
                },
                "configuration": {
                    "metrics": [{
                        "metricStat": {
                            "metric": {
                                "name": "DatabaseConnections",
                                "namespace": "AWS/RDS",
                                "dimensions": {
                                    "DBInstanceIdentifier": "demo-database"
                                }
                            }
                        }
                    }]
                }
            }
        }
    }
    
    print("📤 Sending RDS Connection alarm...")
    print("   Expected: Structured path (Step Functions)")
    print("   Reason: Pattern-based routing for database issues")
    
    response = lambda_client.invoke(
        FunctionName='IngestionLambda',
        InvocationType='RequestResponse',
        Payload=json.dumps(event)
    )
    
    result = json.loads(response['Payload'].read())
    
    if result['statusCode'] == 200:
        body = json.loads(result['body'])
        incident_id = body.get('incident_id')
        return wait_and_check_result(incident_id, "RDS Connection")
    else:
        print(f"❌ Failed: {result}")
        return False

def main():
    """Run all three demo scenarios"""
    print_header("INCIDENT MANAGEMENT SYSTEM - DEMO SCENARIOS")
    print("Region: eu-west-2")
    print("Email: sharmanimit18@outlook.com")
    print("\nThese scenarios demonstrate the complete incident management flow:")
    print("  1. Event ingestion and normalization")
    print("  2. Bedrock AI analysis")
    print("  3. Intelligent routing (structured path for reliability)")
    print("  4. DynamoDB tracking")
    print("  5. SNS notifications with Bedrock summaries")
    
    results = []
    
    # Run scenarios
    results.append(("EC2 High CPU", scenario_1_ec2_high_cpu()))
    time.sleep(2)  # Brief pause between scenarios
    
    results.append(("Lambda Errors", scenario_2_lambda_errors()))
    time.sleep(2)
    
    results.append(("RDS Connection", scenario_3_rds_connection()))
    
    # Summary
    print_header("DEMO SUMMARY")
    
    success_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    print(f"\n📊 Results: {success_count}/{total_count} scenarios completed successfully\n")
    
    for scenario, success in results:
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"   {status} - {scenario}")
    
    print("\n📧 Check your email (sharmanimit18@outlook.com) for notifications")
    print("📊 Check DynamoDB table: incident-tracking-table")
    print("📝 Check CloudWatch Logs: /aws/lambda/IngestionLambda")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    main()
