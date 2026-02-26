import boto3
import json

sfn = boto3.client('stepfunctions', region_name='eu-west-2')
execution_arn = 'arn:aws:states:eu-west-2:923906573163:execution:RemediationStateMachine:d4243afc-af49-4ccd-9fb7-6d643fe11126'

r = sfn.describe_execution(executionArn=execution_arn)
print(f"Status: {r['status']}")

if r['status'] == 'SUCCEEDED':
    print(f"\n✓ Execution completed successfully!")
    output = json.loads(r.get('output', '{}'))
    print(f"\nOutput:")
    print(json.dumps(output, indent=2))
elif r['status'] == 'FAILED':
    print(f"\n✗ Execution failed!")
    print(f"Error: {r.get('error', 'Unknown')}")
    print(f"Cause: {r.get('cause', 'Unknown')[:500]}")
elif r['status'] == 'RUNNING':
    print(f"\n⏳ Still running...")
