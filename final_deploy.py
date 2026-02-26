import subprocess
import time

print("=" * 60)
print("Final Deployment: Lambda Package with Dependencies")
print("=" * 60)
print()

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
    print(f"[{i}/9] Updating {func}...")
    
    result = subprocess.run([
        "aws", "lambda", "update-function-code",
        "--function-name", func,
        "--zip-file", "fileb://lambda-package.zip",
        "--region", "eu-west-2"
    ], capture_output=True, text=True, timeout=60)
    
    if result.returncode == 0:
        print(f"  ✓ {func} updated successfully")
        success_count += 1
    else:
        error_msg = result.stderr.strip() if result.stderr else "Unknown error"
        print(f"  ✗ {func} failed: {error_msg}")
        failed_functions.append(func)
    
    # Small delay between updates
    if i < len(functions):
        time.sleep(2)

print()
print("=" * 60)
print("Deployment Summary")
print("=" * 60)
print(f"Successfully updated: {success_count}/9 functions")

if failed_functions:
    print(f"\nFailed functions: {', '.join(failed_functions)}")
    print("\nYou may need to retry these manually.")
else:
    print("\n✓ All functions updated successfully!")
    print("\nYour AWS Incident Management System is now fully deployed!")
    print("\nNext steps:")
    print("1. Confirm SNS email subscriptions (check your email)")
    print("2. Test the system with the test command")
    print("3. Monitor CloudWatch Logs")
