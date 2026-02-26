# PowerShell deployment script for AWS Incident Management System

Write-Host "=== AWS Incident Management System Deployment ===" -ForegroundColor Green
Write-Host ""

# Check if AWS CLI is configured
try {
    $null = aws sts get-caller-identity 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "AWS CLI not configured"
    }
} catch {
    Write-Host "Error: AWS CLI is not configured. Please run 'aws configure' first." -ForegroundColor Red
    exit 1
}

# Get AWS account and region
$AWS_ACCOUNT = aws sts get-caller-identity --query Account --output text
$AWS_REGION = if ($env:AWS_REGION) { $env:AWS_REGION } else { "us-east-1" }

Write-Host "Deploying to Account: $AWS_ACCOUNT" -ForegroundColor Cyan
Write-Host "Region: $AWS_REGION" -ForegroundColor Cyan
Write-Host ""

# Install Python dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Install CDK dependencies
Write-Host "Installing CDK dependencies..." -ForegroundColor Yellow
npm install

# Bootstrap CDK (if not already done)
Write-Host "Bootstrapping CDK..." -ForegroundColor Yellow
cdk bootstrap "aws://$AWS_ACCOUNT/$AWS_REGION"

# Synthesize CloudFormation template
Write-Host "Synthesizing CloudFormation template..." -ForegroundColor Yellow
cdk synth

# Deploy the stack
Write-Host "Deploying stack..." -ForegroundColor Yellow
cdk deploy --require-approval never

Write-Host ""
Write-Host "=== Deployment Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Check your email and confirm SNS topic subscriptions"
Write-Host "2. Configure Bedrock AI Agent and Knowledge Base in AWS Console"
Write-Host "3. Test the system with a sample incident"
Write-Host ""
