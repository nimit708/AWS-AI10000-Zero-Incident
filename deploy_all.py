import subprocess
import json

print("=" * 60)
print("Deploying Lambda Code to All Functions")
print("=" * 60)
print()

# Step 1: Update IngestionLambda environment variable
print("Step 1: Updating IngestionLambda environment variable...")
print("-" * 60)

state_machine_arn = "arn:aws:states:eu-west-2:923906573163:stateMachine:RemediationStateMachine"

# Get current environment variables
result = subprocess.run([
    "aws", "lambda", "get-function-configuration",
    "--function-name", "IngestionLambda",
    "--region", "eu-west-2",
    "--query", "Environment.Variables"
], capture_output=True, text=True)

if result.returncode == 0:
    env_vars = json.loads(result.stdout)
    env_vars['STATE_MACHINE_ARN'] = state_machine_arn
    
    # Update the environment
    env_json = json.dumps(env_vars)
    result = subprocess.run([
        "aws", "lambda", "update-function-configuration",
        "--function-name", "IngestionLambda",
        "--region", "eu-west-2",
        "--environment", f"Variables={env_json}"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✓ IngestionLambda environment updated successfully!")
    else:
        print(f"✗ Failed to update IngestionLambda: {result.stderr}")
else:
    print(f"✗ Failed to get IngestionLambda config: {result.stderr}")

print()

# Step 2: Deploy code to all 9 Lambda functions
print("Step 2: Deploying code to all 9 Lambda functions...")
print("-" * 60)

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
        "--zip-file", "fileb://lambda-package.zip",
        "--region", "eu-west-2"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"  ✓ {func} updated successfully")
        success_count += 1
    else:
        print(f"  ✗ {func} failed: {result.stderr}")
        failed_functions.append(func)

print()
print("=" * 60)
print("Deployment Summary")
print("=" * 60)
print(f"Successfully updated: {success_count}/9 functions")

if failed_functions:
    print(f"Failed functions: {', '.join(failed_functions)}")
else:
    print("All functions updated successfully! ✓")

print()
print("Next steps:")
print("1. Test the IngestionLambda")
print("2. Check CloudWatch Logs")
print("3. Verify Step Functions execution")
