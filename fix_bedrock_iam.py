"""
Add AWS Marketplace permissions for Bedrock model access.
"""
import boto3
import json

def add_marketplace_permissions():
    """Add AWS Marketplace permissions to Lambda role."""
    
    iam_client = boto3.client('iam', region_name='eu-west-2')
    
    role_name = 'IncidentManagementLambdaRole'
    policy_name = 'BedrockAccess'
    
    print("="*80)
    print("Adding AWS Marketplace Permissions for Bedrock")
    print("="*80)
    
    try:
        # Get current Bedrock policy
        print(f"\n🔍 Getting current BedrockAccess policy...")
        response = iam_client.get_role_policy(
            RoleName=role_name,
            PolicyName=policy_name
        )
        
        policy_doc = response['PolicyDocument']
        
        # Check current actions
        current_actions = policy_doc['Statement'][0]['Action']
        print(f"   Current actions: {len(current_actions)}")
        
        # Add marketplace actions if not present
        marketplace_actions = [
            'aws-marketplace:ViewSubscriptions',
            'aws-marketplace:Subscribe'
        ]
        
        added = []
        for action in marketplace_actions:
            if action not in current_actions:
                current_actions.append(action)
                added.append(action)
        
        if added:
            print(f"\n➕ Adding {len(added)} marketplace actions:")
            for action in added:
                print(f"   ✅ {action}")
            
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
            
            print(f"\n⏳ Wait 10-30 seconds for IAM changes to propagate...")
            print(f"Then run: python test_complete_e2e.py")
            
        else:
            print(f"\n✅ Marketplace permissions already exist!")
            print(f"\nℹ️  If still getting access denied:")
            print(f"   1. Wait a few minutes for IAM to propagate")
            print(f"   2. Check Bedrock model access in AWS Console")
            print(f"   3. Ensure models are enabled for your account")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def main():
    """Main function."""
    success = add_marketplace_permissions()
    
    print("\n" + "="*80)
    if success:
        print("✅ IAM Update Complete")
    else:
        print("❌ IAM Update Failed")
    print("="*80)


if __name__ == "__main__":
    main()
