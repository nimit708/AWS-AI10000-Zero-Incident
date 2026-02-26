"""
Fix IAM permissions for Lambda remediation.
Adds Lambda permissions to the IncidentManagementLambdaRole.
"""
import boto3
import json

def add_lambda_permissions():
    """Add Lambda permissions to the IAM role."""
    
    iam_client = boto3.client('iam', region_name='eu-west-2')
    
    role_name = 'IncidentManagementLambdaRole'
    policy_name = 'LambdaRemediationPolicy'
    
    # Policy document
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "lambda:GetFunctionConfiguration",
                    "lambda:UpdateFunctionConfiguration",
                    "lambda:GetFunction"
                ],
                "Resource": "arn:aws:lambda:eu-west-2:923906573163:function:*"
            }
        ]
    }
    
    print("="*80)
    print("Adding Lambda Permissions to IAM Role")
    print("="*80)
    
    try:
        # Check if policy already exists
        print(f"\n🔍 Checking for existing policy: {policy_name}...")
        
        try:
            iam_client.get_role_policy(
                RoleName=role_name,
                PolicyName=policy_name
            )
            print(f"   ℹ️  Policy already exists, updating...")
        except iam_client.exceptions.NoSuchEntityException:
            print(f"   ℹ️  Policy doesn't exist, creating...")
        
        # Put (create or update) the inline policy
        print(f"\n🔄 Adding policy to role: {role_name}...")
        
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy_document)
        )
        
        print(f"   ✅ Policy added successfully!")
        print(f"\n📋 Policy Details:")
        print(f"   Role: {role_name}")
        print(f"   Policy: {policy_name}")
        print(f"   Permissions:")
        print(f"      - lambda:GetFunctionConfiguration")
        print(f"      - lambda:UpdateFunctionConfiguration")
        print(f"      - lambda:GetFunction")
        print(f"   Resource: arn:aws:lambda:eu-west-2:923906573163:function:*")
        
        print(f"\n✅ IAM permissions fixed!")
        print(f"\n📝 Next steps:")
        print(f"   1. Wait 10 seconds for IAM changes to propagate")
        print(f"   2. Run: python test_e2e_flow.py")
        print(f"   3. Verify Lambda timeout remediation works")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error adding policy: {e}")
        return False


def main():
    """Main function."""
    success = add_lambda_permissions()
    
    print("\n" + "="*80)
    if success:
        print("✅ IAM Permissions Update Complete")
    else:
        print("❌ IAM Permissions Update Failed")
    print("="*80)


if __name__ == "__main__":
    main()
