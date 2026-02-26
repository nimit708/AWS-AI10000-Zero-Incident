"""
Create sample AWS resources for testing all 6 incident scenarios.
These are minimal resources for demo purposes.
"""
import boto3
import json
import time

def create_demo_ec2_instance():
    """Create a small EC2 instance for CPU spike testing."""
    print("\n" + "="*80)
    print("1. Creating Demo EC2 Instance")
    print("="*80)
    
    ec2_client = boto3.client('ec2', region_name='eu-west-2')
    
    try:
        # Get default VPC
        vpcs = ec2_client.describe_vpcs(Filters=[{'Name': 'isDefault', 'Values': ['true']}])
        if not vpcs['Vpcs']:
            print("⚠️  No default VPC found. Skipping EC2 instance creation.")
            return None
        
        vpc_id = vpcs['Vpcs'][0]['VpcId']
        
        # Get a subnet
        subnets = ec2_client.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
        if not subnets['Subnets']:
            print("⚠️  No subnets found. Skipping EC2 instance creation.")
            return None
        
        subnet_id = subnets['Subnets'][0]['SubnetId']
        
        # Get latest Amazon Linux 2 AMI
        images = ec2_client.describe_images(
            Owners=['amazon'],
            Filters=[
                {'Name': 'name', 'Values': ['amzn2-ami-hvm-*-x86_64-gp2']},
                {'Name': 'state', 'Values': ['available']}
            ]
        )
        
        if not images['Images']:
            print("⚠️  No AMI found. Skipping EC2 instance creation.")
            return None
        
        # Sort by creation date and get latest
        latest_ami = sorted(images['Images'], key=lambda x: x['CreationDate'], reverse=True)[0]
        ami_id = latest_ami['ImageId']
        
        print(f"   Using AMI: {ami_id}")
        print(f"   Using Subnet: {subnet_id}")
        
        # Create instance
        response = ec2_client.run_instances(
            ImageId=ami_id,
            InstanceType='t2.micro',  # Free tier eligible
            MinCount=1,
            MaxCount=1,
            SubnetId=subnet_id,
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {'Key': 'Name', 'Value': 'IncidentDemo-EC2'},
                        {'Key': 'Purpose', 'Value': 'IncidentManagementDemo'}
                    ]
                }
            ]
        )
        
        instance_id = response['Instances'][0]['InstanceId']
        print(f"✅ Created EC2 instance: {instance_id}")
        print(f"   Instance Type: t2.micro")
        print(f"   Status: Launching...")
        
        return instance_id
        
    except Exception as e:
        print(f"❌ Error creating EC2 instance: {e}")
        return None

def create_demo_lambda_function():
    """Create a simple Lambda function for timeout testing."""
    print("\n" + "="*80)
    print("2. Creating Demo Lambda Function")
    print("="*80)
    
    lambda_client = boto3.client('lambda', region_name='eu-west-2')
    iam_client = boto3.client('iam', region_name='eu-west-2')
    
    try:
        # Create IAM role for Lambda
        role_name = 'IncidentDemoLambdaRole'
        
        try:
            role = iam_client.get_role(RoleName=role_name)
            role_arn = role['Role']['Arn']
            print(f"   Using existing role: {role_arn}")
        except iam_client.exceptions.NoSuchEntityException:
            # Create role
            assume_role_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "lambda.amazonaws.com"},
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
            
            role = iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(assume_role_policy),
                Description='Role for incident management demo Lambda'
            )
            role_arn = role['Role']['Arn']
            
            # Attach basic execution policy
            iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
            )
            
            print(f"   Created IAM role: {role_arn}")
            print(f"   Waiting 10 seconds for role to propagate...")
            time.sleep(10)
        
        # Create Lambda function
        function_name = 'IncidentDemo-TimeoutTest'
        
        # Simple function code that can timeout
        function_code = '''
def lambda_handler(event, context):
    import time
    # This function can be made to timeout by setting a low timeout value
    time.sleep(2)  # Sleep for 2 seconds
    return {
        'statusCode': 200,
        'body': 'Function completed successfully'
    }
'''
        
        import zipfile
        import io
        
        # Create zip file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr('lambda_function.py', function_code)
        
        zip_buffer.seek(0)
        
        try:
            # Try to create function
            response = lambda_client.create_function(
                FunctionName=function_name,
                Runtime='python3.11',
                Role=role_arn,
                Handler='lambda_function.lambda_handler',
                Code={'ZipFile': zip_buffer.read()},
                Timeout=3,  # 3 second timeout (can timeout if we increase sleep)
                MemorySize=128,
                Tags={
                    'Purpose': 'IncidentManagementDemo'
                }
            )
            
            function_arn = response['FunctionArn']
            print(f"✅ Created Lambda function: {function_name}")
            print(f"   ARN: {function_arn}")
            print(f"   Timeout: 3 seconds")
            
        except lambda_client.exceptions.ResourceConflictException:
            # Function already exists
            response = lambda_client.get_function(FunctionName=function_name)
            function_arn = response['Configuration']['FunctionArn']
            print(f"✅ Using existing Lambda function: {function_name}")
            print(f"   ARN: {function_arn}")
        
        return function_name
        
    except Exception as e:
        print(f"❌ Error creating Lambda function: {e}")
        return None

def create_demo_cloudwatch_alarms(instance_id, function_name):
    """Create CloudWatch alarms for EC2 and Lambda."""
    print("\n" + "="*80)
    print("3. Creating CloudWatch Alarms")
    print("="*80)
    
    cw_client = boto3.client('cloudwatch', region_name='eu-west-2')
    
    alarms_created = []
    
    # EC2 CPU Alarm
    if instance_id:
        try:
            alarm_name = f'IncidentDemo-EC2-CPU-{instance_id}'
            cw_client.put_metric_alarm(
                AlarmName=alarm_name,
                ComparisonOperator='GreaterThanThreshold',
                EvaluationPeriods=1,
                MetricName='CPUUtilization',
                Namespace='AWS/EC2',
                Period=300,
                Statistic='Average',
                Threshold=80.0,  # Alert if CPU > 80%
                ActionsEnabled=False,  # Don't trigger actions, just for demo
                AlarmDescription='Demo alarm for EC2 CPU spike testing',
                Dimensions=[
                    {
                        'Name': 'InstanceId',
                        'Value': instance_id
                    }
                ],
                Tags=[
                    {'Key': 'Purpose', 'Value': 'IncidentManagementDemo'}
                ]
            )
            print(f"✅ Created EC2 CPU alarm: {alarm_name}")
            alarms_created.append(alarm_name)
        except Exception as e:
            print(f"⚠️  Error creating EC2 alarm: {e}")
    
    # Lambda Errors Alarm
    if function_name:
        try:
            alarm_name = f'IncidentDemo-Lambda-Errors-{function_name}'
            cw_client.put_metric_alarm(
                AlarmName=alarm_name,
                ComparisonOperator='GreaterThanThreshold',
                EvaluationPeriods=1,
                MetricName='Errors',
                Namespace='AWS/Lambda',
                Period=300,
                Statistic='Sum',
                Threshold=0.0,  # Alert on any error
                ActionsEnabled=False,
                AlarmDescription='Demo alarm for Lambda error testing',
                Dimensions=[
                    {
                        'Name': 'FunctionName',
                        'Value': function_name
                    }
                ],
                Tags=[
                    {'Key': 'Purpose', 'Value': 'IncidentManagementDemo'}
                ]
            )
            print(f"✅ Created Lambda errors alarm: {alarm_name}")
            alarms_created.append(alarm_name)
        except Exception as e:
            print(f"⚠️  Error creating Lambda alarm: {e}")
    
    return alarms_created

def print_demo_scenarios():
    """Print instructions for testing each scenario."""
    print("\n" + "="*80)
    print("DEMO SCENARIOS - How to Test")
    print("="*80)
    
    print("""
1. EC2 CPU SPIKE
   - Resource: EC2 instance created above
   - How to trigger: SSH into instance and run: stress --cpu 2 --timeout 60s
   - Or: Use demo_test.py to simulate the incident
   
2. LAMBDA TIMEOUT
   - Resource: Lambda function created above
   - How to trigger: Update function timeout to 1 second, then invoke it
   - Or: Use demo_test.py to simulate the incident
   
3. SSL CERTIFICATE ERROR
   - Resource: No AWS resource needed
   - How to trigger: Use demo_test.py to simulate certificate expiry
   - Real scenario: Monitor ACM certificates approaching expiry
   
4. NETWORK TIMEOUT
   - Resource: No AWS resource needed
   - How to trigger: Use demo_test.py to simulate network timeout
   - Real scenario: API Gateway timeout, VPC endpoint issues
   
5. DEPLOYMENT FAILURE
   - Resource: No AWS resource needed
   - How to trigger: Use demo_test.py to simulate deployment failure
   - Real scenario: CodeDeploy failure, ECS task failure
   
6. SERVICE UNHEALTHY
   - Resource: No AWS resource needed
   - How to trigger: Use demo_test.py to simulate service health issue
   - Real scenario: ECS service unhealthy, ALB target unhealthy

RECOMMENDED FOR DEMO:
Use demo_test.py to simulate all 6 scenarios - it's faster and more reliable!

python demo_test.py
""")

def create_demo_resources_summary():
    """Create a summary document."""
    summary = """# Demo Resources Created

## Resources

### 1. EC2 Instance
- **Name**: IncidentDemo-EC2
- **Type**: t2.micro (Free tier)
- **Purpose**: Test EC2 CPU spike incidents
- **CloudWatch Alarm**: Monitors CPU > 80%

### 2. Lambda Function
- **Name**: IncidentDemo-TimeoutTest
- **Runtime**: Python 3.11
- **Timeout**: 3 seconds
- **Purpose**: Test Lambda timeout incidents
- **CloudWatch Alarm**: Monitors errors

### 3. CloudWatch Alarms
- EC2 CPU utilization alarm
- Lambda errors alarm

## How to Use for Demo

### Option 1: Use Demo Script (Recommended)
```bash
python demo_test.py
```
This simulates all 6 incident types without needing real AWS resources.

### Option 2: Trigger Real Incidents

**EC2 CPU Spike:**
```bash
# SSH into EC2 instance
aws ec2 describe-instances --filters "Name=tag:Name,Values=IncidentDemo-EC2" --region eu-west-2

# Install stress tool and run
sudo amazon-linux-extras install epel -y
sudo yum install stress -y
stress --cpu 2 --timeout 60s
```

**Lambda Timeout:**
```bash
# Invoke Lambda function
aws lambda invoke --function-name IncidentDemo-TimeoutTest --region eu-west-2 response.json
```

**Other Scenarios:**
Use `demo_test.py` to simulate SSL, Network, Deployment, and Service incidents.

## Cleanup After Demo

```bash
python cleanup_demo_resources.py
```

This will remove all demo resources to avoid charges.

## Cost Estimate

- EC2 t2.micro: Free tier eligible (750 hours/month free)
- Lambda: Free tier eligible (1M requests/month free)
- CloudWatch Alarms: $0.10/alarm/month
- **Total**: ~$0.20/month (if within free tier)

## Notes

- All resources are tagged with `Purpose: IncidentManagementDemo`
- Resources are minimal and cost-effective
- Can be safely deleted after demo
"""
    
    with open('DEMO_RESOURCES.md', 'w') as f:
        f.write(summary)
    
    print(f"\n💾 Created DEMO_RESOURCES.md with resource details")

def main():
    """Create all demo resources."""
    print("\n" + "="*80)
    print("CREATING DEMO RESOURCES FOR INCIDENT MANAGEMENT SYSTEM")
    print("="*80)
    print("Region: eu-west-2")
    print("Purpose: Demo and testing")
    
    resources = {}
    
    # Create EC2 instance
    instance_id = create_demo_ec2_instance()
    if instance_id:
        resources['ec2_instance'] = instance_id
    
    # Create Lambda function
    function_name = create_demo_lambda_function()
    if function_name:
        resources['lambda_function'] = function_name
    
    # Create CloudWatch alarms
    alarms = create_demo_cloudwatch_alarms(instance_id, function_name)
    if alarms:
        resources['cloudwatch_alarms'] = alarms
    
    # Print scenarios
    print_demo_scenarios()
    
    # Create summary document
    create_demo_resources_summary()
    
    # Summary
    print("\n" + "="*80)
    print("DEMO RESOURCES CREATED")
    print("="*80)
    
    if resources:
        print("\n✅ Resources created successfully:")
        for resource_type, resource_id in resources.items():
            if isinstance(resource_id, list):
                print(f"   {resource_type}: {len(resource_id)} items")
                for item in resource_id:
                    print(f"      - {item}")
            else:
                print(f"   {resource_type}: {resource_id}")
    else:
        print("\n⚠️  No resources were created")
    
    print("\n📋 Next Steps:")
    print("   1. Run demo: python demo_test.py")
    print("   2. Check resources: aws ec2 describe-instances --region eu-west-2")
    print("   3. After demo: python cleanup_demo_resources.py")
    
    print("\n💡 Tip: Use demo_test.py for fastest and most reliable demo!")

if __name__ == "__main__":
    main()
