import subprocess
import json
import time

print("=" * 60)
print("Publishing and Attaching Lambda Layer")
print("=" * 60)
print()

# Step 1: Publish the layer
print("Step 1: Publishing Lambda Layer...")
result = subprocess.run([
    "aws", "lambda", "publish-layer-version",
    "--layer-name", "incident-management-dependencies",
    "--description", "Pydantic and other dependencies for Incident Management System",
    "--zip-file", "fileb://lambda-layer.zip",
    "--compatible-runtimes", "python3.11",
    "--region", "eu-west-2"
], capture_output=True, text=True)

if result.returncode != 0:
    print(f"  ✗ Failed to publish layer: {result.stderr}")
    exit(1)

layer_response = json.loads(result.stdout)
layer_arn = layer_response['LayerVersionArn']
layer_version = layer_response['Version']

print(f"  ✓ Layer published successfully!")
print(f"    ARN: {layer_arn}")
print(f"    Version: {layer_version}")

# Step 2: Attach layer to all Lambda functions
print("\nStep 2: Attaching layer to all Lambda functions...")

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
    print(f"\n[{i}/9] Attaching layer to {func}...")
    
    result = subprocess.run([
        "aws", "lambda", "update-function-configuration",
        "--function-name", func,
        "--layers", layer_arn,
        "--region", "eu-west-2"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"  ✓ Layer attached to {func}")
        success_count += 1
    else:
        error_msg = result.stderr.strip() if result.stderr else "Unknown error"
        print(f"  ✗ Failed to attach layer to {func}: {error_msg}")
        failed_functions.append(func)
    
    # Small delay to avoid rate limiting
    if i < len(functions):
        time.sleep(2)

# Step 3: Update Lambda code (without dependencies)
print("\nStep 3: Updating Lambda code (application code only)...")

# Create a clean package without dependencies
print("  Creating clean application package...")
import zipfile
from pathlib import Path

with zipfile.ZipFile("lambda-code-only.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
    # Add application files
    files_to_add = [
        "lambda_handler.py",
        "config.py"
    ]
    
    for file in files_to_add:
        if Path(file).exists():
            zipf.write(file, file)
    
    # Add src directory
    for root, dirs, files in Path("src").rglob("*"):
        if root.name != "__pycache__" and not str(root).endswith(".pyc"):
            for file in files:
                if not file.endswith(".pyc"):
                    file_path = Path(root) / file
                    arcname = file_path
                    zipf.write(file_path, arcname)

print("  ✓ Clean package created")

# Deploy to all functions
for i, func in enumerate(functions, 1):
    print(f"\n[{i}/9] Updating code for {func}...")
    
    result = subprocess.run([
        "aws", "lambda", "update-function-code",
        "--function-name", func,
        "--zip-file", "fileb://lambda-code-only.zip",
        "--region", "eu-west-2"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"  ✓ Code updated for {func}")
    else:
        print(f"  ✗ Failed to update code for {func}")
    
    if i < len(functions):
        time.sleep(1)

print("\n" + "=" * 60)
print("Deployment Summary")
print("=" * 60)
print(f"Layer published: {layer_arn}")
print(f"Functions with layer attached: {success_count}/9")

if failed_functions:
    print(f"\nFailed functions: {', '.join(failed_functions)}")
else:
    print("\n✓ All functions configured successfully!")
    print("\nYour AWS Incident Management System is ready!")
    print("\nNext steps:")
    print("1. Test the system")
    print("2. Check CloudWatch Logs")
    print("3. Confirm SNS email subscriptions")
