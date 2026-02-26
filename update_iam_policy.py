"""
Update IAM policy to add missing Lambda and CloudWatch permissions.
"""
import boto3
import json

def update_remediation_policy():
    """Update RemediationAccess policy with missing permissions."""
    
    iam_client = boto3.client('iam', region_name='eu-west-2')
    
    role_name = 'IncidentManagementLambdaRole'
    policy_name = 'RemediationAccess'
    
    # Get current policy
    print("🔍 Getting current policy...")
    response = iam_client.get_role_policy(
        RoleName=role_name,
        PolicyName=policy_name
    )
    
    policy_doc = response['PolicyDocument']
    
    # Add missing permissions
    current_actions = policy_doc['Statement'][0]['Action']
    
    missing_actions = [
        'lambda:GetFunctionConfiguration',
        'cloudwatch:GetMetricStatistics',
        'autoscaling:DescribeAutoScalingGroups',
        'autoscaling:DescribeAutoScalingInstances'
    ]
    
    print(f"\n📋 Current actions: {len(current_actions)}")
    print(f"➕ Adding {len(missing_actions)} missing actions...")
    
    # Add missing actions
    for action in missing_actions:
        if action not in current_actions:
            current_actions.append(action)
            print(f"   ✅ Added: {action}")
        else:
            print(f"   ℹ️  Already exists: {action}")
    
    # Update policy
    policy_doc['Statement'][0]['Action'] = sorted(current_actions)
    
    print(f"\n🔄 Updating policy...")
    iam_client.put_role_policy(
        RoleName=role_name,
        PolicyName=policy_name,
        PolicyDocument=json.dumps(policy_doc)
    )
    
    print(f"✅ Policy updated successfully!")
    print(f"\n📋 Total actions now: {len(current_actions)}")
    
    return True


def main():
    """Main function."""
    print("="*80)
    print("Updating IAM Policy for Lambda Remediation")
    print("="*80)
    
    try:
        update_remediation_policy()
        
        print("\n" + "="*80)
        print("✅ IAM Policy Update Complete")
        print("="*80)
        print("\n⏳ Wait 10 seconds for IAM changes to propagate...")
        print("Then run: python test_lambda_timeout.py")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("="*80)


if __name__ == "__main__":
    main()
