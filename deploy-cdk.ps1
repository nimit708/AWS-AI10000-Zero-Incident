# CDK Deployment Script for Windows PowerShell

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "AWS Incident Management System - CDK Deploy" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verify prerequisites
Write-Host "Step 1: Checking prerequisites..." -ForegroundColor Yellow
Write-Host "Verifying AWS credentials..."
try {
    aws sts get-caller-identity | Out-Null
    Write-Host "✓ AWS credentials verified" -ForegroundColor Green
} catch {
    Write-Host "Error: AWS CLI not configured" -ForegroundColor Red
    exit 1
}

Write-Host "Checking Python version..."
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Python not found" -ForegroundColor Red
    exit 1
}

Write-Host "Checking Node.js version..."
node --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Node.js not found" -ForegroundColor Red
    exit 1
}

Write-Host "Checking CDK version..."
cdk --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: CDK not installed" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Prerequisites verified" -ForegroundColor Green
Write-Host ""

# 2. Install dependencies
Write-Host "Step 2: Installing Python dependencies..." -ForegroundColor Yellow
pip install -r cdk-requirements.txt -q
pip install -r requirements.txt -q
Write-Host "✓ Dependencies installed" -ForegroundColor Green
Write-Host ""

# 3. Bootstrap (if needed)
Write-Host "Step 3: Bootstrapping CDK (if needed)..." -ForegroundColor Yellow
cdk bootstrap aws://923906573163/eu-west-2
Write-Host "✓ Bootstrap complete" -ForegroundColor Green
Write-Host ""

# 4. Synthesize
Write-Host "Step 4: Synthesizing CloudFormation template..." -ForegroundColor Yellow
cdk synth | Out-Null
Write-Host "✓ Template synthesized" -ForegroundColor Green
Write-Host ""

# 5. Show diff
Write-Host "Step 5: Showing changes to be deployed..." -ForegroundColor Yellow
cdk diff
Write-Host ""

# 6. Deploy
Write-Host "Step 6: Deploying stack..." -ForegroundColor Yellow
Write-Host "This will take 10-15 minutes..." -ForegroundColor Cyan
cdk deploy --require-approval never

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 7. Get outputs
Write-Host "Stack Outputs:" -ForegroundColor Yellow
aws cloudformation describe-stacks `
  --stack-name IncidentManagementStack `
  --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' `
  --output table

Write-Host ""
Write-Host "⚠️  IMPORTANT: Check your email and confirm SNS subscriptions!" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Confirm 2 SNS email subscriptions" -ForegroundColor White
Write-Host "2. Test the system with: aws lambda invoke --function-name IngestionLambda --payload '{\"test\":\"event\"}' response.json" -ForegroundColor White
Write-Host "3. Monitor CloudWatch Logs" -ForegroundColor White
Write-Host ""
