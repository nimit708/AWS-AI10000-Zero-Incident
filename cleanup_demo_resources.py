"""
Cleanup demo resources created for incident management testing.
"""
import boto3

def cleanup_ec2_instances():
    """Terminate demo EC2 instances."""
    print("\n" + "="*80)
    print("Cleaning up EC2 Instances")
    print("="*80)
    
    ec2_client = boto3.client('ec2', region_name='eu-west-2')
    
    try:
        # Find demo instances
        response = ec2_client.describe_instances(
            Filters=[
                {'Name': 'tag:Purpose', 'Values': ['IncidentManagementDemo']},
                {'Name': 'instance-state-name', 'Values': ['running', 'stopped', 'pending']}
            ]
        )
        
        instance_ids = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_ids.append(instance['InstanceId'])
        
        if instance_ids:
            print(f"   Found {len(instance_ids)} demo instances")
            for instance_id in instance_ids:
                print(f"   Terminating: {instance_id}")
            
            ec2_client.terminate_instances(InstanceIds=instance_ids)
            print(f"✅ Terminated {len(instance_ids)} EC2 instances")
        else:
            print("   No demo EC2 instances found")
            
    except Exception as e:
        print(f"❌ Error cleaning up EC2: {e}")

def cleanup_lambda_functions():
    """Delete demo Lambda functions."""
    print("\n" + "="*80)
    print("Cleaning up Lambda Functions")
    print("="*80)
    
    lambda_client = boto3.client('lambda', region_name='eu-west-2')
    
    try:
        # Find demo functions
        response = lambda_client.list_functions()
        
        demo_functions = [
            f['FunctionName'] for f in response['Functions']
            if f['FunctionName'].startswith('IncidentDemo-')
        ]
        
        if demo_functions:
            for function_name in demo_functions:
                print(f"   Deleting: {function_name}")
                lambda_client.delete_function(FunctionName=function_name)
            
            print(f"✅ Deleted {len(demo_functions)} Lambda functions")
        else:
            print("   No demo Lambda functions found")
            
    except Exception as e:
        print(f"❌ Error cleaning up Lambda: {e}")

def cleanup_iam_roles():
    """Delete demo IAM roles."""
    print("\n" + "="*80)
    print("Cleaning up IAM Roles")
    print("="*80)
    
    iam_client = boto3.client('iam', region_name='eu-west-2')
    
    try:
        role_name = 'IncidentDemoLambdaRole'
        
        try:
            # Detach policies
            attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)
            for policy in attached_policies['AttachedPolicies']:
                print(f"   Detaching policy: {policy['PolicyArn']}")
                iam_client.detach_role_policy(
                    RoleName=role_name,
                    PolicyArn=policy['PolicyArn']
                )
            
            # Delete role
            print(f"   Deleting role: {role_name}")
            iam_client.delete_role(RoleName=role_name)
            print(f"✅ Deleted IAM role: {role_name}")
            
        except iam_client.exceptions.NoSuchEntityException:
            print(f"   Role {role_name} not found")
            
    except Exception as e:
        print(f"❌ Error cleaning up IAM: {e}")

def cleanup_cloudwatch_alarms():
    """Delete demo CloudWatch alarms."""
    print("\n" + "="*80)
    print("Cleaning up CloudWatch Alarms")
    print("="*80)
    
    cw_client = boto3.client('cloudwatch', region_name='eu-west-2')
    
    try:
        # Find demo alarms
        response = cw_client.describe_alarms()
        
        demo_alarms = [
            alarm['AlarmName'] for alarm in response['MetricAlarms']
            if alarm['AlarmName'].startswith('IncidentDemo-')
        ]
        
        if demo_alarms:
            print(f"   Found {len(demo_alarms)} demo alarms")
            cw_client.delete_alarms(AlarmNames=demo_alarms)
            print(f"✅ Deleted {len(demo_alarms)} CloudWatch alarms")
        else:
            print("   No demo CloudWatch alarms found")
            
    except Exception as e:
        print(f"❌ Error cleaning up CloudWatch alarms: {e}")

def main():
    """Cleanup all demo resources."""
    print("\n" + "="*80)
    print("CLEANING UP DEMO RESOURCES")
    print("="*80)
    print("Region: eu-west-2")
    
    # Cleanup in order
    cleanup_cloudwatch_alarms()
    cleanup_lambda_functions()
    cleanup_ec2_instances()
    cleanup_iam_roles()
    
    print("\n" + "="*80)
    print("CLEANUP COMPLETE")
    print("="*80)
    print("\n✅ All demo resources have been cleaned up")
    print("   Your AWS account is now clean")

if __name__ == "__main__":
    main()
