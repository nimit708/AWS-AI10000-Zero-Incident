import subprocess
import time

print("=" * 60)
print("Fixing Lambda Handler Configuration")
print("=" * 60)
print()

# Handler mappings for each function
handlers = {
    "IngestionLambda": "lambda_handler.lambda_handler",
    "DLQProcessorLambda": "src.services.graceful_degradation.process_dlq_message",
    "PatternMatcherLambda": "src.services.pattern_matcher.evaluate_pattern",
    "EC2RemediationLambda": "src.remediation.ec2_remediation.remediate",
    "LambdaRemediationLambda": "src.remediation.lambda_remediation.remediate",
    "SSLRemediationLambda": "src.remediation.ssl_certificate_remediation.remediate",
    "NetworkRemediationLambda": "src.remediation.network_timeout_remediation.remediate",
    "DeploymentRemediationLambda": "src.remediation.deployment_failure_remediation.remediate",
    "ServiceRemediationLambda": "src.remediation.service_health_remediation.remediate"
}

success_count = 0
failed_functions = []

for i, (func, handler) in enumerate(handlers.items(), 1):
    print(f"[{i}/9] Updating handler for {func}...")
    print(f"  Handler: {handler}")
    
    result = subprocess.run([
        "aws", "lambda", "update-function-configuration",
        "--function-name", func,
        "--handler", handler,
        "--region", "eu-west-2"
    ], capture_output=True, text=True, timeout=30)
    
    if result.returncode == 0:
        print(f"  ✓ {func} handler updated")
        success_count += 1
    else:
        error_msg = result.stderr.strip() if result.stderr else "Unknown error"
        print(f"  ✗ {func} failed: {error_msg}")
        failed_functions.append(func)
    
    # Small delay
    if i < len(handlers):
        time.sleep(2)

print("\n" + "=" * 60)
print("Handler Update Summary")
print("=" * 60)
print(f"Successfully updated: {success_count}/9 functions")

if failed_functions:
    print(f"\nFailed functions: {', '.join(failed_functions)}")
else:
    print("\n✓ All handlers updated successfully!")
    print("\nYour system is now ready to test!")
