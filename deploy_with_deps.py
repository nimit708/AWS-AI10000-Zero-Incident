import subprocess

print("=" * 60)
print("Deploying Lambda Package with Dependencies")
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
        "--zip-file", "fileb://lambda-package-with-deps.zip",
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
    print("✓ All functions updated successfully!")
    print()
    print("Next step: Test the system")
    print("Run: aws lambda invoke --function-name IngestionLambda --region eu-west-2 --cli-binary-format raw-in-base64-out --payload file://test_payload.json response.json")
