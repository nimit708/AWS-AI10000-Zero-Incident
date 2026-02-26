"""
Deploy the SSL certificate testing Lambda function.
"""
import boto3
import json
import zipfile
import os
import subprocess
import shutil
from pathlib import Path

# Use the project's region
REGION = 'eu-west-2'

lambda_client = boto3.client('lambda', region_name=REGION)
iam_client = boto3.client('iam')

FUNCTION_NAME = 'CreateExpiredCertificateLambda'
ROLE_NAME = 'CreateExpiredCertificateLambdaRole'


def create_iam_role():
    """Create IAM role for Lambda function."""
    print("Creating IAM role...")
    
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }
    
    try:
        response = iam_client.create_role(
            RoleName=ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='Role for SSL certificate testing Lambda'
        )
        role_arn = response['Role']['Arn']
        print(f"✓ Role created: {role_arn}")
    except iam_client.exceptions.EntityAlreadyExistsException:
        response = iam_client.get_role(RoleName=ROLE_NAME)
        role_arn = response['Role']['Arn']
        print(f"✓ Role already exists: {role_arn}")
    
    # Attach policies
    policies = [
        'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
        'arn:aws:iam::aws:policy/AWSCertificateManagerFullAccess',
        'arn:aws:iam::aws:policy/AWSStepFunctionsFullAccess'
    ]
    
    for policy_arn in policies:
        try:
            iam_client.attach_role_policy(
                RoleName=ROLE_NAME,
                PolicyArn=policy_arn
            )
            print(f"✓ Attached policy: {policy_arn}")
        except Exception as e:
            print(f"  Policy already attached or error: {e}")
    
    return role_arn


def package_lambda():
    """Package Lambda function with dependencies."""
    print("\nPackaging Lambda function...")
    
    # Create temp directory
    package_dir = Path('temp_ssl_lambda_package')
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir()
    
    # Install dependencies
    print("Installing dependencies...")
    subprocess.run([
        'pip', 'install',
        '-r', 'src/testing/requirements.txt',
        '-t', str(package_dir)
    ], check=True)
    
    # Copy Lambda function
    shutil.copy('src/testing/create_expired_certificate.py', package_dir / 'lambda_function.py')
    
    # Create ZIP
    zip_path = 'ssl_test_lambda.zip'
    print(f"Creating ZIP package: {zip_path}")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(package_dir)
                zipf.write(file_path, arcname)
    
    # Cleanup
    shutil.rmtree(package_dir)
    
    print(f"✓ Package created: {zip_path}")
    return zip_path


def deploy_lambda(role_arn, zip_path, state_machine_arn=None):
    """Deploy or update Lambda function."""
    print("\nDeploying Lambda function...")
    
    with open(zip_path, 'rb') as f:
        zip_content = f.read()
    
    environment = {
        'Variables': {}
    }
    
    if state_machine_arn:
        environment['Variables']['STATE_MACHINE_ARN'] = state_machine_arn
    
    try:
        # Try to update existing function
        response = lambda_client.update_function_code(
            FunctionName=FUNCTION_NAME,
            ZipFile=zip_content
        )
        print(f"✓ Function updated: {response['FunctionArn']}")
        
        # Update environment if needed
        if state_machine_arn:
            lambda_client.update_function_configuration(
                FunctionName=FUNCTION_NAME,
                Environment=environment
            )
            print(f"✓ Environment updated with STATE_MACHINE_ARN")
        
    except lambda_client.exceptions.ResourceNotFoundException:
        # Create new function
        response = lambda_client.create_function(
            FunctionName=FUNCTION_NAME,
            Runtime='python3.11',
            Role=role_arn,
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': zip_content},
            Description='Creates expired SSL certificates for testing',
            Timeout=60,
            MemorySize=256,
            Environment=environment
        )
        print(f"✓ Function created: {response['FunctionArn']}")
    
    return response['FunctionArn']


if __name__ == '__main__':
    print("="*60)
    print("Deploying SSL Certificate Testing Lambda")
    print("="*60)
    
    # Hardcoded State Machine ARN for this project
    state_machine_arn = "arn:aws:states:eu-west-2:923906573163:stateMachine:RemediationStateMachine"
    print(f"\n✓ Using State Machine: {state_machine_arn}")
    
    # Create IAM role
    role_arn = create_iam_role()
    
    # Wait for role to propagate
    print("\nWaiting for IAM role to propagate...")
    import time
    time.sleep(10)
    
    # Package Lambda
    zip_path = package_lambda()
    
    # Deploy Lambda
    function_arn = deploy_lambda(role_arn, zip_path, state_machine_arn)
    
    # Cleanup
    os.remove(zip_path)
    
    print("\n" + "="*60)
    print("Deployment Complete!")
    print("="*60)
    print(f"Function Name: {FUNCTION_NAME}")
    print(f"Function ARN: {function_arn}")
    print("\nYou can now test with:")
    print(f"  python test_ssl_certificate_scenario.py")
