"""Update IAM permissions for Lambda role to include CloudWatch GetMetricData"""
import boto3
import json

iam_client = boto3.client('iam', region_name='eu-west-2')

role_name = 'IncidentManagementLambdaRole'
policy_name = 'RemediationAccess'

# Get current policy
response = iam_client.get_role_policy(
    RoleName=role_name,
    PolicyName=policy_name
)

policy_document = response['PolicyDocument']

# Add cloudwatch:GetMetricData to the actions
current_actions = policy_document['Statement'][0]['Action']

# Add the missing CloudWatch and CloudWatch Logs permissions
new_actions = [
    'cloudwatch:GetMetricData',
    'cloudwatch:ListMetrics',
    'cloudwatch:DescribeAlarms',
    'logs:GetLogEvents',
    'logs:FilterLogEvents',
    'logs:DescribeLogGroups',
    'logs:DescribeLogStreams'
]

for action in new_actions:
    if action not in current_actions:
        current_actions.append(action)
        print(f"✅ Adding: {action}")
    else:
        print(f"⏭️  Already exists: {action}")

# Sort actions for readability
current_actions.sort()

# Update the policy
policy_document['Statement'][0]['Action'] = current_actions

print(f"\nUpdating policy '{policy_name}' on role '{role_name}'...")

iam_client.put_role_policy(
    RoleName=role_name,
    PolicyName=policy_name,
    PolicyDocument=json.dumps(policy_document)
)

print("✅ IAM policy updated successfully!")
print(f"\nTotal permissions: {len(current_actions)}")
print("\nNew permissions:")
for action in new_actions:
    print(f"  • {action}")
