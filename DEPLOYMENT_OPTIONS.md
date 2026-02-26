# Deployment Options - Choose Your Path

You have two deployment options for the AWS Incident Management System:

## Option 1: CDK Deployment (Recommended - Try This First)

### Pros
- ✅ Single command deployment
- ✅ Automatic Lambda code packaging
- ✅ Faster and more automated
- ✅ Easier updates and changes
- ✅ Infrastructure as code with Python

### Cons
- ❌ May hang on Windows systems (as we experienced)
- ❌ Requires CDK CLI and Node.js
- ❌ More dependencies to install

### Quick Start
```bash
# Linux/Mac
./deploy-cdk.sh

# Windows PowerShell
.\deploy-cdk.ps1
```

### Manual Commands
```bash
pip install -r cdk-requirements.txt
pip install -r requirements.txt
cdk bootstrap aws://923906573163/us-east-1
cdk synth
cdk deploy --require-approval never
```

### Files to Use
- `CDK_MANUAL_DEPLOYMENT.md` - Detailed guide
- `CDK_COMMANDS_QUICK_REFERENCE.md` - Command reference
- `deploy-cdk.sh` or `deploy-cdk.ps1` - Automated scripts
- `app.py` - CDK app entry point
- `infrastructure/incident_management_stack.py` - Stack definition

### Time Required
- 12-20 minutes total
- Most time is waiting for AWS resources to create

---

## Option 2: CloudFormation Deployment (Fallback)

### Pros
- ✅ Works reliably on all platforms
- ✅ No CDK tooling required
- ✅ Deploy via AWS Console (visual)
- ✅ More control over each step

### Cons
- ❌ Two-step process (stack + Lambda code)
- ❌ Manual Lambda code packaging
- ❌ Manual code upload to each function
- ❌ More steps overall

### Quick Start
```bash
# 1. Package Lambda code
.\package-lambda.ps1  # Windows
./package-lambda.sh   # Linux/Mac

# 2. Deploy via AWS Console
# Upload cloudformation-template.yaml

# 3. Update Lambda functions
# Upload lambda-package.zip to each function
```

### Files to Use
- `CLOUDFORMATION_DEPLOYMENT.md` - Detailed guide
- `QUICK_START.md` - Quick reference
- `cloudformation-template.yaml` - CloudFormation template
- `package-lambda.ps1` or `package-lambda.sh` - Packaging scripts
- `DEPLOYMENT_CHECKLIST.md` - Step-by-step checklist

### Time Required
- 20-30 minutes total
- More manual steps involved

---

## Comparison Table

| Feature | CDK | CloudFormation |
|---------|-----|----------------|
| Deployment Method | CLI | AWS Console |
| Lambda Packaging | Automatic | Manual |
| Code Updates | `cdk deploy` | Manual upload |
| Prerequisites | More | Fewer |
| Reliability | May hang | Always works |
| Speed | Faster | Slower |
| Automation | High | Low |
| Learning Curve | Steeper | Gentler |

---

## Recommendation

### Try CDK First
Since you want to run the commands yourself, I recommend trying the CDK approach first:

1. Open a terminal/PowerShell
2. Run `.\deploy-cdk.ps1` (Windows) or `./deploy-cdk.sh` (Linux/Mac)
3. Wait and see if it completes

### If CDK Hangs
If the CDK deployment hangs (like it did before):

1. Press Ctrl+C to cancel
2. Switch to CloudFormation approach
3. Follow `QUICK_START.md` for CloudFormation deployment

---

## All Available Documentation

### CDK Deployment
1. **CDK_MANUAL_DEPLOYMENT.md** - Complete CDK guide with all commands
2. **CDK_COMMANDS_QUICK_REFERENCE.md** - Quick command reference
3. **deploy-cdk.sh** - Automated deployment script (Linux/Mac)
4. **deploy-cdk.ps1** - Automated deployment script (Windows)
5. **DEPLOYMENT.md** - Original deployment guide

### CloudFormation Deployment
1. **CLOUDFORMATION_DEPLOYMENT.md** - Complete CloudFormation guide
2. **QUICK_START.md** - 5-step quick start
3. **DEPLOYMENT_CHECKLIST.md** - Step-by-step checklist
4. **CFN_DEPLOYMENT_SUMMARY.md** - Overview and summary
5. **cloudformation-template.yaml** - The template itself
6. **package-lambda.ps1** - Lambda packaging (Windows)
7. **package-lambda.sh** - Lambda packaging (Linux/Mac)

### Infrastructure Code
1. **app.py** - CDK app entry point
2. **infrastructure/incident_management_stack.py** - Stack definition
3. **cdk.json** - CDK configuration
4. **.cdkignore** - Files excluded from Lambda packages

---

## Decision Tree

```
Start Here
    |
    ├─> Want automated deployment?
    |   └─> YES → Try CDK (deploy-cdk.sh/ps1)
    |       |
    |       ├─> Works? → Great! You're done
    |       └─> Hangs? → Switch to CloudFormation
    |
    └─> Want manual control?
        └─> Use CloudFormation (QUICK_START.md)
```

---

## What I Recommend For You

Based on our conversation, here's my recommendation:

1. **First attempt**: Try CDK deployment manually
   - Open PowerShell/Terminal
   - Run the commands from `CDK_COMMANDS_QUICK_REFERENCE.md`
   - See if it completes this time

2. **If it hangs**: Switch to CloudFormation
   - Use `QUICK_START.md` for fastest path
   - Or `CLOUDFORMATION_DEPLOYMENT.md` for detailed steps

3. **Either way**: You'll have a working system in 20-30 minutes

---

## Quick Command Summary

### CDK (Try This First)
```bash
# One command
./deploy-cdk.sh  # or .\deploy-cdk.ps1

# Or step by step
pip install -r cdk-requirements.txt
pip install -r requirements.txt
cdk bootstrap aws://923906573163/us-east-1
cdk deploy --require-approval never
```

### CloudFormation (If CDK Fails)
```bash
# Package code
./package-lambda.sh  # or .\package-lambda.ps1

# Then deploy via AWS Console
# Upload cloudformation-template.yaml
# Update Lambda functions with lambda-package.zip
```

---

## Next Steps

1. Choose your deployment method
2. Follow the appropriate guide
3. Confirm SNS email subscriptions
4. Test the system
5. Monitor CloudWatch Logs

Good luck! 🚀
