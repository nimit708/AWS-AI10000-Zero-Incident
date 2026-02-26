# AWS Incident Management System

AI-powered incident detection, analysis, and automated remediation system using AWS Bedrock.

## Architecture

- **Fast Path**: High-confidence incidents resolved by Bedrock AI Agent (2-5 seconds)
- **Structured Path**: Unknown incidents evaluated through Step Functions workflow (10-30 seconds)
- **Continuous Learning**: Knowledge Base improves over time with resolved incidents

## Prerequisites

- Python 3.9+
- AWS CLI configured with credentials
- Node.js and npm (for CDK CLI)
- AWS CDK CLI: `npm install -g aws-cdk`

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Bootstrap CDK (first time only):
```bash
cdk bootstrap
```

## Configuration

### Bedrock Models
- **AI Agent**: Claude 3.5 Sonnet (`anthropic.claude-3-5-sonnet-20241022-v2:0`)
- **Embeddings**: Titan Embeddings V2 (`amazon.titan-embed-text-v2:0`)
- **Summaries**: Claude 3 Haiku (`anthropic.claude-3-haiku-20240307-v1:0`)

### Notifications
- Email: sharmanimit18@outlook.com (configured in stack)

## Deployment

```bash
# Synthesize CloudFormation template
cdk synth

# Deploy to AWS
cdk deploy

# View differences before deployment
cdk diff
```

## Testing

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run property tests only
pytest tests/property/ -m property_test

# Run with coverage
pytest --cov=src --cov-report=html
```

## Project Structure

```
.
├── app.py                      # CDK app entry point
├── cdk.json                    # CDK configuration
├── requirements.txt            # Python dependencies
├── infrastructure/             # CDK infrastructure code
│   └── incident_management_stack.py
├── src/                        # Application source code
│   ├── models/                 # Data models
│   ├── lambdas/                # Lambda function handlers
│   ├── services/               # Business logic services
│   └── utils/                  # Utility functions
└── tests/                      # Test suite
    ├── unit/                   # Unit tests
    ├── property/               # Property-based tests
    └── integration/            # Integration tests
```

## Development

Follow the implementation tasks in `.kiro/specs/aws-incident-management/tasks.md`



