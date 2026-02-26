"""
Fix Lambda function handler configurations.
"""
import boto3

def update_handler(lambda_client, function_name, new_handler):
    """Update Lambda function handler."""
    try:
        print(f"🔄 Updating {function_name} handler to {new_handler}...")
        
        response = lambda_client.update_function_configuration(
            FunctionName=function_name,
            Handler=new_handler
        )
        
        print(f"   ✅ Updated successfully")
        print(f"   Handler: {response['Handler']}")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    """Main function."""
    region = 'eu-west-2'
    lambda_client = boto3.client('lambda', region_name=region)
    
    print("="*80)
    print("Fixing Lambda Handler Configurations")
    print("="*80)
    
    # Handler updates
    updates = [
        ('IngestionLambda', 'lambda_handler.lambda_handler'),
        ('PatternMatcherLambda', 'pattern_matcher_handler.evaluate_pattern'),
        ('EC2RemediationLambda', 'ec2_remediation_handler.remediate'),
        ('LambdaRemediationLambda', 'lambda_remediation_handler.remediate')
    ]
    
    success_count = 0
    for function_name, handler in updates:
        print(f"\n{function_name}:")
        if update_handler(lambda_client, function_name, handler):
            success_count += 1
    
    print(f"\n{'='*80}")
    print(f"✅ Updated {success_count}/{len(updates)} handlers")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
