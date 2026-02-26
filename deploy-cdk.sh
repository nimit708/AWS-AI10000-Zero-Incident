#!/bin/bash
# CDK Deployment Script for Linux/Mac

set -e  # Exit on error

echo "=========================================="
echo "AWS Incident Management System - CDK Deploy"
echo "=========================================="
echo ""

# 1. Verify prerequisites
echo "Step 1: Checking prerequisites..."
echo "Verifying AWS credentials..."
aws sts get-caller-identity || { echo "Error: AWS CLI not configured"; exit 1; }

echo "Checking Python version..."
python --version || { echo "Error: Python not found"; exit 1; }

echo "Checking Node.js version..."
node --version || { echo "Error: Node.js not found"; exit 1; }

echo "Checking CDK version..."
cdk --version || { echo "Error: CDK not installed"; exit 1; }

echo "✓ Prerequisites verified"
echo ""

# 2. Install dependencies
echo "Step 2: Installing Python dependencies..."
pip install -r cdk-requirements.txt -q
pip install -r requirements.txt -q
echo "✓ Dependencies installed"
echo ""

# 3. Bootstrap (if needed)
echo "Step 3: Bootstrapping CDK (if needed)..."
cdk bootstrap aws://923906573163/eu-west-2
echo "✓ Bootstrap complete"
echo ""

# 4. Synthesize
echo "Step 4: Synthesizing CloudFormation template..."
cdk synth > /dev/null
echo "✓ Template synthesized"
echo ""

# 5. Show diff
echo "Step 5: Showing changes to be deployed..."
cdk diff || true
echo ""

# 6. Deploy
echo "Step 6: Deploying stack..."
echo "This will take 10-15 minutes..."
cdk deploy --require-approval never

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""

# 7. Get outputs
echo "Stack Outputs:"
aws cloudformation describe-stacks \
  --stack-name IncidentManagementStack \
  --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
  --output table

echo ""
echo "⚠️  IMPORTANT: Check your email and confirm SNS subscriptions!"
echo ""
echo "Next steps:"
echo "1. Confirm 2 SNS email subscriptions"
echo "2. Test the system with: aws lambda invoke --function-name IngestionLambda --payload '{\"test\":\"event\"}' response.json"
echo "3. Monitor CloudWatch Logs"
echo ""
