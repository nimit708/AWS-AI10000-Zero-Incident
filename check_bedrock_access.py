"""
Check Bedrock model access status.
"""
import boto3
import json
from botocore.exceptions import ClientError

def check_model_access(model_id, region='eu-west-2'):
    """
    Check if a specific Bedrock model is accessible.
    
    Args:
        model_id: Bedrock model ID
        region: AWS region
        
    Returns:
        Tuple of (accessible, message)
    """
    bedrock_client = boto3.client('bedrock-runtime', region_name=region)
    
    try:
        # Try a simple invoke with minimal tokens
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 10,
            "messages": [
                {
                    "role": "user",
                    "content": "test"
                }
            ]
        }
        
        response = bedrock_client.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )
        
        return True, "✅ Model is accessible"
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        if 'AccessDeniedException' in error_code:
            if 'aws-marketplace' in error_message.lower():
                return False, "⏳ Waiting for AWS Marketplace subscription approval"
            else:
                return False, f"❌ Access denied: {error_message[:200]}"
        elif 'ValidationException' in error_code:
            # Model exists but validation failed (still means we have access)
            return True, "✅ Model is accessible (validation error is OK)"
        else:
            return False, f"❌ Error: {error_code} - {error_message[:200]}"
    
    except Exception as e:
        return False, f"❌ Unexpected error: {str(e)[:200]}"


def list_available_models(region='eu-west-2'):
    """
    List all available Bedrock models.
    
    Args:
        region: AWS region
        
    Returns:
        List of model IDs
    """
    try:
        bedrock_client = boto3.client('bedrock', region_name=region)
        
        response = bedrock_client.list_foundation_models()
        
        models = []
        for model in response.get('modelSummaries', []):
            model_id = model.get('modelId')
            model_name = model.get('modelName')
            provider = model.get('providerName')
            
            models.append({
                'id': model_id,
                'name': model_name,
                'provider': provider
            })
        
        return models
        
    except Exception as e:
        print(f"Error listing models: {e}")
        return []


def check_all_models():
    """Check access for all models used in the system."""
    
    region = 'eu-west-2'
    
    print("="*80)
    print("Bedrock Model Access Status Check")
    print("="*80)
    
    # Models used in the system
    models = {
        'Agent Model (Sonnet)': 'anthropic.claude-3-sonnet-20240229-v1:0',
        'Summary Model (Haiku)': 'anthropic.claude-3-haiku-20240307-v1:0',
        'Embedding Model (Titan)': 'amazon.titan-embed-text-v1'
    }
    
    print(f"\nRegion: {region}")
    print(f"\nChecking {len(models)} models...\n")
    
    results = {}
    
    for name, model_id in models.items():
        print(f"🔍 {name}")
        print(f"   Model ID: {model_id}")
        
        accessible, message = check_model_access(model_id, region)
        results[name] = accessible
        
        print(f"   Status: {message}")
        print()
    
    # Summary
    print("="*80)
    print("Summary")
    print("="*80)
    
    accessible_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    print(f"\n✅ Accessible: {accessible_count}/{total_count} models")
    
    if accessible_count == total_count:
        print("\n🎉 All models are accessible!")
        print("\n📝 Next steps:")
        print("   1. Run: python test_complete_e2e.py")
        print("   2. Check email for AI-generated summaries")
        print("   3. Verify Bedrock is being used in logs")
    elif accessible_count > 0:
        print(f"\n⚠️  Some models are accessible, others pending")
        print("\n📝 Next steps:")
        print("   1. Wait for remaining models to be approved")
        print("   2. Check again in a few minutes")
    else:
        print(f"\n⏳ All models are pending approval")
        print("\n📝 How to request access:")
        print("   1. Go to AWS Console → Bedrock → Model access")
        print("   2. Click 'Manage model access'")
        print("   3. Select the models you need")
        print("   4. Click 'Request model access'")
        print("   5. Wait for approval (usually instant for some models)")
        print("\n📝 Alternative:")
        print("   Run this command to check in AWS Console:")
        print("   aws bedrock list-foundation-models --region eu-west-2")
    
    print("\n" + "="*80)
    
    return results


def check_via_console_link():
    """Provide direct link to check in AWS Console."""
    
    region = 'eu-west-2'
    
    print("\n" + "="*80)
    print("AWS Console Links")
    print("="*80)
    
    print(f"\n🔗 Check Model Access:")
    print(f"   https://{region}.console.aws.amazon.com/bedrock/home?region={region}#/modelaccess")
    
    print(f"\n🔗 Request Model Access:")
    print(f"   https://{region}.console.aws.amazon.com/bedrock/home?region={region}#/modelaccess")
    
    print(f"\n🔗 Bedrock Dashboard:")
    print(f"   https://{region}.console.aws.amazon.com/bedrock/home?region={region}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    # Check all models
    results = check_all_models()
    
    # Provide console links
    check_via_console_link()
    
    # Additional info
    print("\n💡 Tips:")
    print("   • Model access is usually instant for Claude models")
    print("   • Titan embedding model is usually pre-approved")
    print("   • If still pending, check AWS Console for status")
    print("   • Some models require accepting terms & conditions")
    print("   • System works perfectly without Bedrock (graceful fallback)")
