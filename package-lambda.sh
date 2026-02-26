#!/bin/bash
# Bash script to package Lambda code for deployment
# This script creates a zip file excluding unnecessary files

echo "Packaging Lambda code..."

# Remove old package if exists
if [ -f "lambda-package.zip" ]; then
    rm lambda-package.zip
    echo "Removed old lambda-package.zip"
fi

# Create zip excluding unnecessary files
echo "Creating zip archive..."

zip -r lambda-package.zip . \
    -x "tests/*" \
    -x "*.md" \
    -x "TASK_*.md" \
    -x "TASKS_*.md" \
    -x "infrastructure/*" \
    -x "app.py" \
    -x "cdk.json" \
    -x "cdk.out/*" \
    -x "*.js" \
    -x "*.ts" \
    -x "node_modules/*" \
    -x "package.json" \
    -x "package-lock.json" \
    -x "deploy.sh" \
    -x "deploy.ps1" \
    -x "destroy.sh" \
    -x "*.ps1" \
    -x "*.sh" \
    -x ".git/*" \
    -x ".gitignore" \
    -x ".vscode/*" \
    -x ".idea/*" \
    -x ".kiro/*" \
    -x "venv/*" \
    -x "env/*" \
    -x ".env" \
    -x "dist/*" \
    -x "build/*" \
    -x "*.egg-info/*" \
    -x "cdk-requirements.txt" \
    -x "pytest.ini" \
    -x ".pytest_cache/*" \
    -x "__pycache__/*" \
    -x "*.pyc" \
    -x "test_cdk.py" \
    -x "cloudformation-template.yaml" \
    -x "CLOUDFORMATION_DEPLOYMENT.md" \
    -x "package-lambda.sh" \
    -x "package-lambda.ps1"

if [ -f "lambda-package.zip" ]; then
    size=$(du -h lambda-package.zip | cut -f1)
    echo ""
    echo "Success! Created lambda-package.zip ($size)"
    echo ""
    echo "Next steps:"
    echo "1. Deploy CloudFormation stack via AWS Console"
    echo "2. Upload this package to update Lambda functions"
    echo ""
    echo "See CLOUDFORMATION_DEPLOYMENT.md for detailed instructions"
else
    echo "Error: Failed to create lambda-package.zip"
    exit 1
fi
