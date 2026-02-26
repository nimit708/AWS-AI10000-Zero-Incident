"""
Update all Lambda functions with the latest code.
This script packages and deploys the code to all Lambda functions.
"""
import boto3
import zipfile
import os
import io
import time

def create_lambda_package():
    """Create a ZIP package with all Lambda code and dependencies."""
    print("📦 Creating Lambda deployment package...")
    
    # Create in-memory ZIP file
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add main handlers
        handlers = [
            'lambda_handler.py',
            'pattern_matcher_handler.py',
            'ec2_remediation_handler.py',
            'lambda_remediation_handler.py',
            'sf_remediation_handler.py',
            'config.py'
        ]
        
        for handler in handlers:
            if os.path.exists(handler):
                zipf.write(handler, handler)
                print(f"   ✅ Added {handler}")
        
        # Add src directory
        for root, dirs, files in os.walk('src'):
            # Skip __pycache__ and test directories
            dirs[:] = [d for d in dirs if d not in ['__pycache__', 'tests', 'test']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    arcname = file_path.replace('\\', '/')
                    zipf.write(file_path, arcname)
                    print(f"   ✅ Added {arcname}")
    
    zip_buffer.seek(0)
    print(f"✅ Package created ({len(zip_buffer.getvalue()) / 1024 / 1024:.2f} MB)")
    return zip_buffer.getvalue()


def update_lambda_function(lambda_client, function_name, zip_content):
    """Update a Lambda function with new code."""
    try:
        print(f"\n🔄 Updating {function_name}...")
        
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        
        print(f"   ✅ Updated successfully")
        print(f"   Version: {response['Version']}")
        print(f"   Last Modified: {response['LastModified']}")
        
        # Wait for update to complete
        print(f"   ⏳ Waiting for update to complete...")
        waiter = lambda_client.get_waiter('function_updated')
        waiter.wait(FunctionName=function_name)
        print(f"   ✅ Update complete")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error updating {function_name}: {e}")
        return False


def update_environment_variable(lambda_client, function_name, var_name, var_value):
    """Update a single environment variable for a Lambda function."""
    try:
        # Get current configuration
        response = lambda_client.get_function_configuration(FunctionName=function_name)
        
        # Update environment variables
        env_vars = response.get('Environment', {}).get('Variables', {})
        env_vars[var_name] = var_value
        
        # Update function configuration
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Environment={'Variables': env_vars}
        )
        
        print(f"   ✅ Updated {var_name} = {var_value}")
        return True
        
    except Exception as e:
        print(f"   ❌ Error updating environment variable: {e}")
        return False


def main():
    """Main function to update all Lambda functions."""
    region = 'eu-west-2'
    
    print("="*80)
    print("Lambda Functions Update Script")
    print("="*80)
    
    # Initialize AWS clients
    lambda_client = boto3.client('lambda', region_name=region)
    sf_client = boto3.client('stepfunctions', region_name=region)
    
    # Get Step Functions ARN
    print("\n🔍 Getting Step Functions ARN...")
    state_machine_arn = "arn:aws:states:eu-west-2:923906573163:stateMachine:RemediationStateMachine"
    print(f"   State Machine ARN: {state_machine_arn}")
    
    # Create deployment package
    zip_content = create_lambda_package()
    
    # List of Lambda functions to update
    functions = [
        'IngestionLambda',
        'PatternMatcherLambda',
        'EC2RemediationLambda',
        'LambdaRemediationLambda'
    ]
    
    # Update each function
    print("\n" + "="*80)
    print("Updating Lambda Functions")
    print("="*80)
    
    success_count = 0
    for function_name in functions:
        if update_lambda_function(lambda_client, function_name, zip_content):
            success_count += 1
            time.sleep(2)  # Brief pause between updates
    
    # Update IngestionLambda environment variable
    print("\n" + "="*80)
    print("Updating Environment Variables")
    print("="*80)
    print(f"\n🔄 Updating IngestionLambda environment...")
    update_environment_variable(
        lambda_client,
        'IngestionLambda',
        'STATE_MACHINE_ARN',
        state_machine_arn
    )
    
    # Summary
    print("\n" + "="*80)
    print("Update Summary")
    print("="*80)
    print(f"✅ Successfully updated: {success_count}/{len(functions)} functions")
    
    if success_count == len(functions):
        print("\n🎉 All Lambda functions updated successfully!")
        print("\n📝 Next steps:")
        print("   1. Test the end-to-end flow with demo_test.py")
        print("   2. Check Step Functions executions in AWS Console")
        print("   3. Verify SNS notifications are sent")
    else:
        print(f"\n⚠️  Some functions failed to update. Please check the errors above.")
    
    print("="*80)


if __name__ == "__main__":
    main()
