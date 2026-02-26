"""
Complete demo test script for incident management system.
Tests all 6 incident patterns with proper formatting.
"""
import json
import boto3
from datetime import datetime
import time

def test_incident(incident_name, test_event):
    """Test a single incident."""
    lambda_client = boto3.client('lambda', region_name='eu-west-2')
    
    print(f"\n{'='*80}")
    print(f"Testing: {incident_name}")
    print(f"{'='*80}")
    
    try:
        response = lambda_client.invoke(
            FunctionName='IngestionLambda',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        status_code = response['StatusCode']
        payload = json.loads(response['Payload'].read())
        
        if status_code == 200:
            body = json.loads(payload.get('body', '{}'))
            
            if body.get('success'):
                print(f"✅ SUCCESS")
                print(f"   Incident ID: {body.get('incident_id')}")
                print(f"   Routing Path: {body.get('routing_path')}")
                print(f"   Confidence: {body.get('confidence')}")
                print(f"   Processing Time: {body.get('processing_time_seconds')}s")
                return True, body.get('incident_id')
            else:
                print(f"❌ FAILED: {body.get('error')}")
                return False, None
        else:
            print(f"❌ Lambda error: Status {status_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False, None

def main():
    """Run all demo tests."""
    
    print("\n" + "="*80)
    print("INCIDENT MANAGEMENT SYSTEM - DEMO TEST SUITE")
    print("="*80)
    print(f"Time: {datetime.utcnow().isoformat()}Z")
    print(f"Region: eu-west-2")
    
    results = []
    
    # Test 1: EC2 CPU Spike
    test1 = {
        "source": "demo",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "raw_payload": {
            "event_type": "EC2 CPU Spike",
            "severity": "high",
            "resource_id": "i-1234567890abcdef0",
            "affected_resources": ["i-1234567890abcdef0"],
            "description": "CPU utilization exceeded 90% for 5 minutes",
            "metadata": {
                "cpu_utilization": 95.5,
                "instance_type": "t3.medium",
                "region": "eu-west-2"
            }
        }
    }
    success, incident_id = test_incident("EC2 CPU Spike", test1)
    results.append(("EC2 CPU Spike", success, incident_id))
    time.sleep(1)
    
    # Test 2: Lambda Timeout
    test2 = {
        "source": "demo",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "raw_payload": {
            "event_type": "Lambda Timeout",
            "severity": "medium",
            "resource_id": "my-function",
            "affected_resources": ["my-function"],
            "description": "Function execution exceeded timeout limit",
            "metadata": {
                "timeout": 30,
                "duration": 31,
                "memory_used": 256
            }
        }
    }
    success, incident_id = test_incident("Lambda Timeout", test2)
    results.append(("Lambda Timeout", success, incident_id))
    time.sleep(1)
    
    # Test 3: SSL Certificate Error
    test3 = {
        "source": "demo",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "raw_payload": {
            "event_type": "SSL Certificate Error",
            "severity": "high",
            "resource_id": "api.example.com",
            "affected_resources": ["api.example.com"],
            "description": "SSL certificate expires in 5 days",
            "metadata": {
                "domain": "api.example.com",
                "expiry_date": "2026-03-01",
                "days_until_expiry": 5
            }
        }
    }
    success, incident_id = test_incident("SSL Certificate Error", test3)
    results.append(("SSL Certificate Error", success, incident_id))
    time.sleep(1)
    
    # Test 4: Network Timeout
    test4 = {
        "source": "demo",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "raw_payload": {
            "event_type": "Network Timeout",
            "severity": "medium",
            "resource_id": "api.external.com",
            "affected_resources": ["api.external.com"],
            "description": "Connection timeout to external API",
            "metadata": {
                "endpoint": "https://api.external.com/v1",
                "timeout_seconds": 30,
                "retry_count": 3
            }
        }
    }
    success, incident_id = test_incident("Network Timeout", test4)
    results.append(("Network Timeout", success, incident_id))
    time.sleep(1)
    
    # Test 5: Deployment Failure
    test5 = {
        "source": "demo",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "raw_payload": {
            "event_type": "Deployment Failure",
            "severity": "high",
            "resource_id": "my-app-v2.0",
            "affected_resources": ["my-app-v2.0"],
            "description": "Deployment failed during health check",
            "metadata": {
                "deployment_id": "deploy-12345",
                "stage": "health_check",
                "error": "Health check failed"
            }
        }
    }
    success, incident_id = test_incident("Deployment Failure", test5)
    results.append(("Deployment Failure", success, incident_id))
    time.sleep(1)
    
    # Test 6: Service Unhealthy
    test6 = {
        "source": "demo",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "raw_payload": {
            "event_type": "Service Unhealthy",
            "severity": "critical",
            "resource_id": "payment-service",
            "affected_resources": ["payment-service"],
            "description": "Service health check failing",
            "metadata": {
                "service_name": "payment-service",
                "health_status": "unhealthy",
                "failed_checks": 5
            }
        }
    }
    success, incident_id = test_incident("Service Unhealthy", test6)
    results.append(("Service Unhealthy", success, incident_id))
    
    # Summary
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    print(f"\nResults: {passed}/{total} tests passed\n")
    
    for name, success, incident_id in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if incident_id:
            print(f"         Incident ID: {incident_id}")
    
    print(f"\n{'='*80}")
    print("NEXT STEPS")
    print(f"{'='*80}")
    print("\n1. Check CloudWatch Logs:")
    print("   python check_logs.py")
    print("\n2. Check DynamoDB Records:")
    print("   aws dynamodb scan --table-name incident-tracking-table --region eu-west-2 --max-items 10")
    print("\n3. Check your email for SNS notifications:")
    print("   Email: sharmanimit18@outlook.com")
    print("\n4. Check remediation Lambda logs:")
    print("   aws logs tail /aws/lambda/EC2RemediationLambda --region eu-west-2")
    
    if passed == total:
        print(f"\n🎉 All tests passed! System is fully operational!")
    else:
        print(f"\n⚠️  Some tests failed. Check logs for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
