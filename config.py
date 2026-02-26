"""Configuration for AWS Incident Management System"""
import os

# Bedrock Configuration
BEDROCK_AGENT_MODEL = os.getenv(
    "BEDROCK_AGENT_MODEL",
    "anthropic.claude-3-5-sonnet-20241022-v2:0"
)
BEDROCK_EMBEDDING_MODEL = os.getenv(
    "BEDROCK_EMBEDDING_MODEL",
    "amazon.titan-embed-text-v2:0"
)
BEDROCK_SUMMARY_MODEL = os.getenv(
    "BEDROCK_SUMMARY_MODEL",
    "anthropic.claude-3-haiku-20240307-v1:0"
)

# Confidence Threshold
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.85"))

# DynamoDB Configuration
INCIDENT_TABLE_NAME = os.getenv("INCIDENT_TABLE_NAME", "IncidentTracking")
RESOURCE_LOCK_TABLE_NAME = os.getenv("RESOURCE_LOCK_TABLE_NAME", "ResourceLocks")

# S3 Configuration
KNOWLEDGE_BASE_BUCKET = os.getenv("KNOWLEDGE_BASE_BUCKET", "")

# SNS Configuration
SNS_SUMMARY_TOPIC_ARN = os.getenv("SUMMARY_TOPIC_ARN", "")
SNS_URGENT_TOPIC_ARN = os.getenv("URGENT_TOPIC_ARN", "")

# Timeouts (seconds)
BEDROCK_QUERY_TIMEOUT = int(os.getenv("BEDROCK_QUERY_TIMEOUT", "10"))
REMEDIATION_TIMEOUT = int(os.getenv("REMEDIATION_TIMEOUT", "300"))

# Retry Configuration
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_BACKOFF_BASE = float(os.getenv("RETRY_BACKOFF_BASE", "1.0"))

# Lock Configuration
LOCK_EXPIRY_SECONDS = int(os.getenv("LOCK_EXPIRY_SECONDS", "300"))

# TTL Configuration (90 days)
INCIDENT_TTL_DAYS = int(os.getenv("INCIDENT_TTL_DAYS", "90"))

# AWS Region - Lambda provides this automatically, no need to set it
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "eu-west-2")
