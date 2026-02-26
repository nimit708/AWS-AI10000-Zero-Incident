# Quick Reference - Finish Deployment Today

## 🎯 3 Steps to Complete (30 minutes total)

### Step 1: Confirm SNS Subscriptions (2 minutes) ⚠️ CRITICAL

**What:** Check your email and confirm 2 AWS SNS subscription emails

**Why:** Without this, you won't receive any incident notifications

**How:**
1. Open email: sharmanimit18@outlook.com
2. Look for 2 emails from "AWS Notifications"
3. Click "Confirm subscription" in each email
4. You should see a confirmation page

**Topics:**
- incident-summary-topic (regular notifications)
- incident-urgent-topic (urgent alerts)

---

### Step 2: Run Deployment Completion Script (10 minutes)

**What:** Automated script that checks all components and tests the system

**How:**
```bash
python complete_deployment.py
```

**What it does:**
- ✅ Checks SNS subscription status
- ✅ Verifies Bedrock models available in eu-west-2
- ✅ Tests Lambda function with sample incident
- ✅ Checks DynamoDB tables
- ✅ Verifies Step Functions state machine
- ✅ Provides detailed status report

**Expected output:**
- All green checkmarks ✅
- Test incident processed successfully
- DynamoDB record created
- No critical errors

---

### Step 3: Review and Test (15 minutes)

**Check CloudWatch Logs:**
```bash
python check_logs.py
```

**Test Lambda manually:**
```bash
python test_lambda_fixed.py
```

**Check DynamoDB records:**
```bash
aws dynamodb scan --table-name incident-tracking-table --region eu-west-2 --max-items 5
```

**View Step Functions executions:**
```bash
aws stepfunctions list-executions \
  --state-machine-arn arn:aws:states:eu-west-2:923906573163:stateMachine:RemediationStateMachine \
  --region eu-west-2
```

---

## 📊 Current Status

### ✅ Completed
- CloudFormation stack deployed
- All 9 Lambda functions deployed with correct handlers
- Lambda Layer created and attached (3.55 MB)
- DynamoDB tables created
- SNS topics created
- Step Functions state machine created
- CloudWatch alarms configured
- IAM roles and permissions set up

### ⏳ Pending
- SNS email subscriptions (YOU must confirm)
- Bedrock model verification (script will check)
- End-to-end testing (script will test)

---

## 🔧 If Issues Found

### Issue: SNS subscriptions not confirmed
**Fix:** Check spam folder, resend confirmation email:
```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:eu-west-2:923906573163:incident-summary-topic \
  --protocol email \
  --notification-endpoint sharmanimit18@outlook.com \
  --region eu-west-2
```

### Issue: Bedrock models not available
**Option 1:** Use different model versions (script will suggest)

**Option 2:** Redeploy to us-east-1:
```bash
# Update region in cloudformation-template.yaml
# Redeploy stack to us-east-1
```

### Issue: Lambda errors
**Check logs:**
```bash
aws logs tail /aws/lambda/IngestionLambda --region eu-west-2 --follow
```

**Update code:**
```bash
python update_code_only.py
```

---

## 📚 Key Files

### Deployment Scripts
- `complete_deployment.py` - Main completion script (RUN THIS)
- `check_logs.py` - Check CloudWatch logs
- `test_lambda_fixed.py` - Test Lambda function
- `update_code_only.py` - Update Lambda code if needed

### Documentation
- `FINAL_DEPLOYMENT_SUMMARY.md` - Complete deployment overview
- `NEXT_STEPS.md` - Detailed next steps guide
- `CLOUDFORMATION_DEPLOYMENT.md` - Infrastructure details

### Configuration
- `cloudformation-template.yaml` - Infrastructure as code
- `config.py` - Application configuration
- `lambda_handler.py` - Main Lambda handler

---

## 🎯 Success Criteria

Your deployment is complete when:

1. ✅ SNS subscriptions confirmed (both topics)
2. ✅ `complete_deployment.py` runs without errors
3. ✅ Test Lambda invocation succeeds (StatusCode 200)
4. ✅ DynamoDB record created for test incident
5. ✅ CloudWatch logs show successful processing

---

## 🚀 After Completion

### Monitor Your System
```bash
# Watch logs in real-time
aws logs tail /aws/lambda/IngestionLambda --region eu-west-2 --follow

# Check CloudWatch dashboard
# Go to AWS Console → CloudWatch → Dashboards
```

### Test Different Incident Types
```bash
# EC2 CPU Spike
python test_lambda_fixed.py

# Lambda Timeout (modify test_lambda_fixed.py)
# Network Timeout
# SSL Certificate Error
# etc.
```

### Set Up Monitoring
- Create CloudWatch Dashboard
- Configure additional alarms
- Set up cost alerts

---

## 💡 Quick Commands

**Check everything:**
```bash
python complete_deployment.py
```

**Test Lambda:**
```bash
python test_lambda_fixed.py
```

**View logs:**
```bash
python check_logs.py
```

**Check DynamoDB:**
```bash
aws dynamodb scan --table-name incident-tracking-table --region eu-west-2
```

**List Lambda functions:**
```bash
aws lambda list-functions --region eu-west-2 --query "Functions[?contains(FunctionName, 'Incident')].FunctionName"
```

**Check SNS subscriptions:**
```bash
aws sns list-subscriptions --region eu-west-2
```

---

## 🆘 Need Help?

1. Run `python complete_deployment.py` - it will tell you what's wrong
2. Check `FINAL_DEPLOYMENT_SUMMARY.md` for detailed info
3. Review CloudWatch logs: `python check_logs.py`
4. Check AWS Console for visual status

---

## 🎉 You're Almost Done!

**Time to complete:** ~30 minutes
**Current progress:** 95%
**Remaining:** Confirm SNS + Run tests

**Let's finish this today! 🚀**

Run this now:
```bash
python complete_deployment.py
```
