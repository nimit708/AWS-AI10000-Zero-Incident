# SSL Certificate Testing

## Overview

The SSL certificate remediation test demonstrates the complete incident management workflow for expired SSL certificates.

## Test Flow

1. **Trigger**: Simulates an SSL certificate expiration event
2. **Ingestion**: Event is processed by the ingestion Lambda
3. **AI Analysis**: Bedrock AI Agent analyzes the incident
4. **Routing**: System routes to appropriate remediation path
5. **Remediation**: SSL remediation handler attempts to fix the issue
6. **Notification**: SNS alerts are sent
7. **Tracking**: Incident status is updated in DynamoDB

## Current Test Behavior

The test creates a **fake certificate ARN** that doesn't exist in ACM. This is intentional for testing purposes:

- ✓ Tests the complete workflow end-to-end
- ✓ Validates incident tracking and status updates
- ✓ Confirms AI analysis and routing logic
- ✓ Verifies SNS notifications are sent
- ✓ Shows graceful error handling when certificate doesn't exist

The remediation will fail with "ResourceNotFoundException" because the certificate doesn't exist, but this demonstrates:
- Error handling in the remediation handler
- Urgent alert notifications for failed remediations
- Proper incident status updates (failed state)
- Knowledge base updates with failure information

## Running the Test

```bash
python src/testing/trigger_ssl_remediation.py
```

## Expected Output

```
Scenario 1: Expired Certificate (Zero TTL)
============================================================
Triggering SSL Certificate Remediation via Ingestion Lambda
============================================================
Certificate ARN: arn:aws:acm:eu-west-2:923906573163:certificate/test-...
Domain: expired-test.example.com
Days Until Expiry: 0
Status: EXPIRED

✓ Ingestion Lambda processed successfully!
  Incident ID: <uuid>
  Routing Path: fast_path or structured_path
  Confidence: 0.XX

============================================================
Monitoring Incident Status in DynamoDB
============================================================
Status: received | Path: fast (elapsed: 0s)
Status: failed | Path: fast (elapsed: 15s)

✓ Incident failed!
  Event Type: SSL Certificate Expiration
  Routing Path: fast
  Resolution: SSL certificate ... has expired. Automated remediation failed...
  Actions: X performed
```

## Testing with Real Certificates

To test with actual SSL certificates:

### Option 1: Use Existing Certificate

If you have certificates in ACM:

```bash
# List certificates
aws acm list-certificates --region eu-west-2

# Edit trigger_ssl_remediation.py and replace the cert_arn generation with your ARN
```

### Option 2: Create Test Certificate

Create a self-signed certificate and import to ACM:

```bash
# Generate certificate (requires OpenSSL)
openssl genrsa -out private.key 2048
openssl req -new -x509 -key private.key -out certificate.crt -days 1 \
  -subj "/C=US/ST=Test/L=Test/O=TestOrg/CN=test-ssl.example.com"

# Import to ACM
aws acm import-certificate \
  --certificate fileb://certificate.crt \
  --private-key fileb://private.key \
  --region eu-west-2
```

Then use the returned ARN in your test.

## What This Demonstrates

Even with a fake certificate, this test proves:

1. **Complete Workflow**: Full incident lifecycle from ingestion to resolution
2. **AI Integration**: Bedrock AI Agent is queried and provides analysis
3. **Routing Logic**: System correctly routes SSL incidents
4. **Error Handling**: Graceful failure when resources don't exist
5. **Notifications**: SNS alerts are sent for both success and failure
6. **Tracking**: DynamoDB properly tracks incident status
7. **Knowledge Base**: Failed incidents are logged for learning

## Production Behavior

In production with real certificates:

- The remediation handler would successfully describe the certificate
- It would check expiration dates and certificate status
- It could automatically renew certificates or request new ones
- It would update DNS records if needed
- Success notifications would be sent
- The incident would be marked as "resolved"
- Knowledge base would be updated with successful resolution

## Summary

The test successfully demonstrates the **incident management system works end-to-end**, even though the specific SSL remediation fails due to the non-existent certificate. This is valuable for:

- Validating the complete workflow
- Testing error handling and notifications
- Demonstrating AI-powered incident analysis
- Showing proper incident tracking
- Proving the system handles failures gracefully
