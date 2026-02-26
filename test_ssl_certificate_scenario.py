"""
Test script to create expired SSL certificate and verify remediation workflow.
"""
import boto3
import json
import time
from datetime import datetime

# Use the project's region
REGION = 'eu-west-2'

lambda_client = boto3.client('lambda', region_name=REGION)
sfn_client = boto3.client('stepfunctions', region_name=REGION)
acm_client = boto3.client('acm', region_name=REGION)

LAMBDA_FUNCTION_NAME = 'CreateExpiredCertificateLambda'
STATE_MACHINE_ARN = 'arn:aws:states:eu-west-2:923906573163:stateMachine:RemediationStateMachine'


def create_expired_certificate(days_valid=0, hours_valid=0, trigger_remediation=True):
    """Invoke Lambda to create expired certificate."""
    print(f"\n{'='*60}")
    print(f"Creating SSL Certificate Test Scenario")
    print(f"{'='*60}")
    print(f"Validity: {days_valid} days, {hours_valid} hours")
    print(f"Trigger Remediation: {trigger_remediation}")
    
    payload = {
        'days_valid': days_valid,
        'hours_valid': hours_valid,
        'trigger_remediation': trigger_remediation
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName=LAMBDA_FUNCTION_NAME,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        # Check if Lambda execution failed
        if 'FunctionError' in response:
            print(f"\n✗ Lambda execution failed!")
            print(f"  Error: {result.get('errorMessage', 'Unknown error')}")
            print(f"  Type: {result.get('errorType', 'Unknown')}")
            if 'stackTrace' in result:
                print(f"  Stack trace:")
                for line in result['stackTrace'][:5]:  # Show first 5 lines
                    print(f"    {line}")
            return None
        
        # Parse successful response
        if response['StatusCode'] == 200 and 'body' in result:
            body = json.loads(result['body'])
            
            if result.get('statusCode') == 500:
                print(f"\n✗ Error creating certificate")
                print(f"  Error: {body.get('error', 'Unknown error')}")
                print(f"  Message: {body.get('message', 'No message')}")
                return None
            
            print(f"\n✓ Certificate created successfully!")
            print(f"  Certificate ARN: {body['certificateArn']}")
            print(f"  Expiry Date: {body['expiryDate']}")
            
            if body.get('executionArn'):
                print(f"  Execution ARN: {body['executionArn']}")
            
            return body
        else:
            print(f"\n✗ Unexpected response format")
            print(f"  Response: {json.dumps(result, indent=2)}")
            return None
            
    except Exception as e:
        print(f"\n✗ Error invoking Lambda: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def check_execution_status(execution_arn, max_wait=300):
    """Monitor Step Functions execution status."""
    print(f"\n{'='*60}")
    print(f"Monitoring Step Functions Execution")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = sfn_client.describe_execution(
                executionArn=execution_arn
            )
            
            status = response['status']
            print(f"Status: {status}")
            
            if status == 'SUCCEEDED':
                print(f"\n✓ Execution completed successfully!")
                output = json.loads(response.get('output', '{}'))
                print(f"\nOutput:")
                print(json.dumps(output, indent=2))
                return True
                
            elif status == 'FAILED':
                print(f"\n✗ Execution failed!")
                print(f"Error: {response.get('error', 'Unknown')}")
                print(f"Cause: {response.get('cause', 'Unknown')}")
                return False
                
            elif status == 'TIMED_OUT':
                print(f"\n✗ Execution timed out!")
                return False
                
            elif status == 'ABORTED':
                print(f"\n✗ Execution was aborted!")
                return False
            
            # Still running
            time.sleep(10)
            
        except Exception as e:
            print(f"\n✗ Error checking execution: {str(e)}")
            return False
    
    print(f"\n⚠ Timeout waiting for execution to complete")
    return False


def verify_certificate_status(cert_arn):
    """Verify certificate status in ACM."""
    print(f"\n{'='*60}")
    print(f"Verifying Certificate Status")
    print(f"{'='*60}")
    
    try:
        response = acm_client.describe_certificate(
            CertificateArn=cert_arn
        )
        
        cert = response['Certificate']
        print(f"Domain: {cert['DomainName']}")
        print(f"Status: {cert['Status']}")
        print(f"Not After: {cert['NotAfter']}")
        print(f"In Use: {cert.get('InUseBy', [])}")
        
        # Check if expired
        if cert['NotAfter'] < datetime.now(cert['NotAfter'].tzinfo):
            print(f"\n⚠ Certificate is EXPIRED")
        else:
            print(f"\n✓ Certificate is still valid")
        
        return cert
        
    except Exception as e:
        print(f"\n✗ Error verifying certificate: {str(e)}")
        return None


def run_test_scenario(scenario_name, days_valid=0, hours_valid=0):
    """Run complete test scenario."""
    print(f"\n\n{'#'*60}")
    print(f"# TEST SCENARIO: {scenario_name}")
    print(f"{'#'*60}")
    
    # Create certificate
    result = create_expired_certificate(days_valid, hours_valid, trigger_remediation=True)
    
    if not result:
        print(f"\n✗ Scenario failed: Could not create certificate")
        return False
    
    cert_arn = result['certificateArn']
    execution_arn = result.get('executionArn')
    
    # Verify certificate
    verify_certificate_status(cert_arn)
    
    # Monitor execution if triggered
    if execution_arn:
        success = check_execution_status(execution_arn)
        
        if success:
            print(f"\n✓ Scenario '{scenario_name}' completed successfully!")
        else:
            print(f"\n✗ Scenario '{scenario_name}' failed!")
        
        return success
    else:
        print(f"\n⚠ No remediation triggered")
        return True


if __name__ == '__main__':
    print("SSL Certificate Testing Scenarios")
    print("=" * 60)
    
    # Scenario 1: Already expired certificate (zero TTL)
    run_test_scenario(
        "Expired Certificate (Zero TTL)",
        days_valid=0,
        hours_valid=0
    )
    
    # Scenario 2: Certificate expiring in 1 hour
    run_test_scenario(
        "Certificate Expiring Soon (1 hour)",
        days_valid=0,
        hours_valid=1
    )
    
    # Scenario 3: Certificate expiring in 1 day
    run_test_scenario(
        "Certificate Expiring Soon (1 day)",
        days_valid=1,
        hours_valid=0
    )
    
    print(f"\n\n{'='*60}")
    print("All test scenarios completed!")
    print(f"{'='*60}")
