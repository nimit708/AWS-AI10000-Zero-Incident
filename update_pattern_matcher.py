"""
Update only the PatternMatcherLambda function.
"""
import boto3
import zipfile
import os
import shutil
from pathlib import Path

def create_lambda_package():
    """Create Lambda deployment package."""
    print("Creating Lambda package...")
    
    # Create temp directory
    package_dir = Path('temp_lambda_package')
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir()
    
    # Copy source files
    print("Copying source files...")
    
    # Copy handlers
    shutil.copy('pattern_matcher_handler.py', package_dir / 'pattern_matcher_handler.py')
    
    # Copy src directory
    src_dest = package_dir / 'src'
    shutil.copytree('src', src_dest, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'testing'))
    
    # Create ZIP
    zip_path = 'pattern_matcher_lambda.zip'
    print(f"Creating ZIP: {zip_path}")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            # Skip __pycache__ directories
            dirs[:] = [d for d in dirs if d != '__pycache__']
            
            for file in files:
                if file.endswith('.pyc'):
                    continue
                file_path = Path(root) / file
                arcname = file_path.relative_to(package_dir)
                zipf.write(file_path, arcname)
    
    # Cleanup
    shutil.rmtree(package_dir)
    
    print(f"✓ Package created: {zip_path}")
    return zip_path


def update_lambda(function_name, zip_path):
    """Update Lambda function with new code."""
    lambda_client = boto3.client('lambda', region_name='eu-west-2')
    
    print(f"\nUpdating {function_name}...")
    
    with open(zip_path, 'rb') as f:
        zip_content = f.read()
    
    try:
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        
        print(f"✓ {function_name} updated successfully!")
        print(f"  Version: {response['Version']}")
        print(f"  Last Modified: {response['LastModified']}")
        print(f"  Code Size: {response['CodeSize']} bytes")
        return True
        
    except Exception as e:
        print(f"✗ Error updating {function_name}: {str(e)}")
        return False


if __name__ == '__main__':
    print("="*60)
    print("Updating PatternMatcherLambda")
    print("="*60)
    
    # Create package
    zip_path = create_lambda_package()
    
    # Update function
    success = update_lambda('PatternMatcherLambda', zip_path)
    
    # Cleanup
    os.remove(zip_path)
    
    print("\n" + "="*60)
    if success:
        print("✓ Update complete!")
    else:
        print("✗ Update failed!")
    print("="*60)
