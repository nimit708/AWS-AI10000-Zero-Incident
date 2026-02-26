"""
Update Lambda function code for all 9 functions.
"""
import boto3
import zipfile
import os
from pathlib import Path

def create_lambda_package():
    """Create Lambda deployment package with application code only."""
    print("Creating Lambda deployment package...")
    
    # Files and directories to include
    include_patterns = [
        'lambda_handler.py',
        'config.py',
        'src/**/*.py',
    ]
    
    # Files to exclude
    exclude_patterns = [
        'tests',
        '__pycache__',
        '*.pyc',
        '.pytest_cache',
        'docs',
        'infrastructure',
        '*.md',
        '.git',
        'node_modules',
        'cdk.out',
        '.vscode',
        '.kiro'
    ]
    
    zip_path = 'lambda-code-update.zip'
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add lambda_handler.py
        if os.path.exists('lambda_handler.py'):
            zipf.write('lambda_handler.py', 'lambda_handler.py')
            print(f"  ✅ Added lambda_handler.py")
        
        # Add config.py
        if os.path.exists('config.py'):
            zipf.write('config.py', 'config.py')
            print(f"  ✅ Added config.py")
        
        # Add src directory
        if os.path.exists('src'):
            for root, dirs, files in os.walk('src'):
                # Skip excluded directories
                dirs[:] = [d for d in dirs if d not in exclude_patterns and not d.startswith('.')]
                
                for file in files:
                    if file.endswith('.py') and not file.startswith('.'):
                        file_path = os.path.join(root, file)
                        arcname = file_path.replace('\\', '/')
                        zipf.write(file_path, arcname)
                        print(f"  ✅ Added {arcname}")
    
    size = os.path.getsize(zip_path)
    print(f"\n✅ Package created: {zip_path} ({size:,} bytes)")
    return zip_path

def update_lambda_functions(zip_path):
    """Update all Lambda functions with new code."""
    lambda_client = boto3.client('lambda', region_name='eu-west-2')
    
    functions = [
        'IngestionLambda',
        'DLQProcessorLambda',
        'PatternMatcherLambda',
        'EC2RemediationLambda',
        'LambdaRemediationLambda',
        'SSLRemediationLambda',
        'NetworkRemediationLambda',
        'DeploymentRemediationLambda',
        'ServiceRemediationLambda'
    ]
    
    print(f"\nUpdating {len(functions)} Lambda functions...")
    
    with open(zip_path, 'rb') as f:
        zip_content = f.read()
    
    for function_name in functions:
        try:
            print(f"\n📦 Updating {function_name}...")
            
            response = lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_content
            )
            
            print(f"   ✅ Updated successfully")
            print(f"   Version: {response['Version']}")
            print(f"   Code Size: {response['CodeSize']:,} bytes")
            print(f"   Last Modified: {response['LastModified']}")
            
        except Exception as e:
            print(f"   ❌ Error updating {function_name}: {e}")
    
    print("\n✅ All Lambda functions updated!")

def main():
    """Main function."""
    print("="*80)
    print("UPDATING LAMBDA FUNCTION CODE")
    print("="*80)
    
    try:
        # Create package
        zip_path = create_lambda_package()
        
        # Update functions
        update_lambda_functions(zip_path)
        
        print("\n" + "="*80)
        print("✅ CODE UPDATE COMPLETE!")
        print("="*80)
        print("\nNext steps:")
        print("1. Test Lambda: python test_lambda_fixed.py")
        print("2. Check logs: python check_logs.py")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise

if __name__ == "__main__":
    main()
