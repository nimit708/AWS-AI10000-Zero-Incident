#!/bin/bash
# Deployment script for AWS Incident Management System

set -e

echo "=== AWS Incident Management System Deployment ==="
echo ""

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "Error: AWS CLI is not configured. Please run 'aws configure' first."
    exit 1
fi

# Get AWS account and region
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${AWS_REGION:-us-east-1}

echo "Deploying to Account: $AWS_ACCOUNT"
echo "Region: $AWS_REGION"
echo ""

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install CDK dependencies
echo "Installing CDK dependencies..."
npm install

# Bootstrap CDK (if not already done)
echo "Bootstrapping CDK..."
cdk bootstrap aws://$AWS_ACCOUNT/$AWS_REGION

# Synthesize CloudFormation template
echo "Synthesizing CloudFormation template..."
cdk synth

# Deploy the stack
echo "Deploying stack..."
cdk deploy --require-approval never

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Next steps:"
echo "1. Check your email and confirm SNS topic subscriptions"
echo "2. Configure Bedrock AI Agent and Knowledge Base in AWS Console"
echo "3. Test the system with a sample incident"
echo ""
