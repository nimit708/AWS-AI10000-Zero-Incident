import subprocess
import zipfile
import os
from pathlib import Path
import time

print("=" * 60)
print("Updating Lambda Code (Application Only)")
print("=" * 60)
print()

# Step 1: Create clean package
print("Step 1: Creating clean application package...")

if os.path.exists("lambda-code-only.zip"):
    os.remove("lambda-code-only.zip")

with zipfile.ZipFile("lambda-code-only.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
    # Add main files
    files_to_add = ["lambda_handler.py", "config.py"]
    
    for file in files_to_add:
        if Path(file).exists():
            zipf.write(file, file)
            print(f"  Added: {file}")
    
    # Add src directory
    for root, dirs, files in os.walk("src"):
        # Skip __pycache__
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        
        for file in files:
            if not file.endswith(".pyc"):
                file_path = Path(root) / file
                arcname = str(file_path)
                zipf.write(file_path, arcname)
                print(f"  Added: {arcname}")

size_kb = os.path.getsize("lambda-code-only.zip") / 1024
print(f"\n  ✓ Package created: {size_kb:.2f} KB")

# Step 2: Deploy to all functions
print("\nStep 2: Deploying to all Lambda functions...")

functions = [
    "IngestionLambda",
    "DLQProcessorLambda",
    "PatternMatcherLambda",
    "EC2RemediationLambda",
    "LambdaRemediationLambda",
    "SSLRemediationLambda",
    "NetworkRemediationLambda",
    "DeploymentRemediationLambda",
    "ServiceRemediationLambda"
]

success_count = 0
failed_functions = []

for i, func in enumerate(functions, 1):
    print(f"\n[{i}/9] Updating {func}...")
    
    result = subprocess.run([
        "aws", "lambda", "update-function-code",
        "--function-name", func,
        "--zip-file", "fileb://lambda-code-only.zip",
        "--region", "eu-west-2"
    ], capture_output=True, text=True, timeout=60)
    
    if result.returncode == 0:
        print(f"  ✓ {func} updated successfully")
        success_count += 1
    else:
        error_msg = result.stderr.strip() if result.stderr else "Unknown error"
        print(f"  ✗ {func} failed: {error_msg}")
        failed_functions.append(func)
    
    # Small delay
    if i < len(functions):
        time.sleep(1)

print("\n" + "=" * 60)
print("Deployment Summary")
print("=" * 60)
print(f"Successfully updated: {success_count}/9 functions")

if failed_functions:
    print(f"\nFailed functions: {', '.join(failed_functions)}")
else:
    print("\n✓ All functions updated successfully!")
    print("\n🎉 Your AWS Incident Management System is fully deployed!")
    print("\nConfiguration:")
    print("  - Lambda Layer: incident-management-dependencies:1")
    print("  - Application code: Deployed to all 9 functions")
    print("  - Dependencies: Provided by Lambda Layer")
    print("\nNext steps:")
    print("  1. Test the system")
    print("  2. Check CloudWatch Logs")
    print("  3. Confirm SNS email subscriptions")
