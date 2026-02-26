# Post-deployment script to update IngestionLambda with StateMachine ARN

Write-Host "Updating IngestionLambda with StateMachine ARN..." -ForegroundColor Yellow

# Get the StateMachine ARN from stack outputs
$STATE_MACHINE_ARN = aws cloudformation describe-stacks `
  --stack-name IncidentManagementStack `
  --query 'Stacks[0].Outputs[?OutputKey==`StateMachineArn`].OutputValue' `
  --output text

if ([string]::IsNullOrEmpty($STATE_MACHINE_ARN)) {
    Write-Host "Error: Could not retrieve StateMachine ARN" -ForegroundColor Red
    exit 1
}

Write-Host "StateMachine ARN: $STATE_MACHINE_ARN" -ForegroundColor Cyan

# Get other environment variables
$INCIDENT_TABLE = aws cloudformation describe-stacks `
  --stack-name IncidentManagementStack `
  --query 'Stacks[0].Outputs[?OutputKey==`IncidentTableName`].OutputValue' `
  --output text

$RESOURCE_LOCK_TABLE = aws cloudformation describe-stacks `
  --stack-name IncidentManagementStack `
  --query 'Stacks[0].Outputs[?OutputKey==`ResourceLockTableName`].OutputValue' `
  --output text

$KB_BUCKET = aws cloudformation describe-stacks `
  --stack-name IncidentManagementStack `
  --query 'Stacks[0].Outputs[?OutputKey==`KnowledgeBaseBucketName`].OutputValue' `
  --output text

$SUMMARY_TOPIC = aws cloudformation describe-stacks `
  --stack-name IncidentManagementStack `
  --query 'Stacks[0].Outputs[?OutputKey==`SummaryTopicArn`].OutputValue' `
  --output text

$URGENT_TOPIC = aws cloudformation describe-stacks `
  --stack-name IncidentManagementStack `
  --query 'Stacks[0].Outputs[?OutputKey==`UrgentTopicArn`].OutputValue' `
  --output text

$DLQ_URL = aws cloudformation describe-stacks `
  --stack-name IncidentManagementStack `
  --query 'Stacks[0].Outputs[?OutputKey==`DLQUrl`].OutputValue' `
  --output text

# Build environment variables JSON
$envVars = @{
    INCIDENT_TABLE_NAME = $INCIDENT_TABLE
    RESOURCE_LOCK_TABLE_NAME = $RESOURCE_LOCK_TABLE
    KNOWLEDGE_BASE_BUCKET = $KB_BUCKET
    SUMMARY_TOPIC_ARN = $SUMMARY_TOPIC
    URGENT_TOPIC_ARN = $URGENT_TOPIC
    DLQ_URL = $DLQ_URL
    STATE_MACHINE_ARN = $STATE_MACHINE_ARN
    BEDROCK_AGENT_MODEL = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    BEDROCK_EMBEDDING_MODEL = "amazon.titan-embed-text-v2:0"
    BEDROCK_SUMMARY_MODEL = "anthropic.claude-3-haiku-20240307-v1:0"
}

$envVarsJson = $envVars | ConvertTo-Json -Compress

# Update Lambda function configuration
aws lambda update-function-configuration `
  --function-name IngestionLambda `
  --environment "Variables=$envVarsJson"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ IngestionLambda updated successfully!" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to update IngestionLambda" -ForegroundColor Red
    exit 1
}
