# PowerShell script to package Lambda code for deployment
# This script creates a zip file excluding unnecessary files

Write-Host "Packaging Lambda code..." -ForegroundColor Green

# Remove old package if exists
if (Test-Path "lambda-package.zip") {
    Remove-Item "lambda-package.zip"
    Write-Host "Removed old lambda-package.zip" -ForegroundColor Yellow
}

# Create list of files to exclude
$excludePatterns = @(
    "tests",
    "*.md",
    "TASK_*.md",
    "TASKS_*.md",
    "infrastructure",
    "app.py",
    "cdk.json",
    "cdk.out",
    "*.js",
    "*.ts",
    "node_modules",
    "package.json",
    "package-lock.json",
    "deploy.sh",
    "deploy.ps1",
    "destroy.sh",
    "*.ps1",
    "*.sh",
    ".git",
    ".gitignore",
    ".vscode",
    ".idea",
    ".kiro",
    "venv",
    "env",
    ".env",
    "dist",
    "build",
    "*.egg-info",
    "cdk-requirements.txt",
    "pytest.ini",
    ".pytest_cache",
    "__pycache__",
    "*.pyc",
    "test_cdk.py",
    "cloudformation-template.yaml",
    "CLOUDFORMATION_DEPLOYMENT.md",
    "package-lambda.ps1"
)

Write-Host "Creating zip archive..." -ForegroundColor Green

# Use Python to create the zip (more reliable than PowerShell Compress-Archive)
$pythonScript = @"
import zipfile
import os
from pathlib import Path

exclude_patterns = $($excludePatterns | ConvertTo-Json)

def should_exclude(path):
    path_str = str(path)
    for pattern in exclude_patterns:
        if pattern.startswith('*'):
            if path_str.endswith(pattern[1:]):
                return True
        elif pattern in path_str:
            return True
    return False

with zipfile.ZipFile('lambda-package.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk('.'):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if not should_exclude(Path(root) / d)]
        
        for file in files:
            file_path = Path(root) / file
            if not should_exclude(file_path):
                arcname = str(file_path.relative_to('.'))
                zipf.write(file_path, arcname)
                print(f'Added: {arcname}')

print('\nPackage created successfully!')
"@

$pythonScript | python

if (Test-Path "lambda-package.zip") {
    $size = (Get-Item "lambda-package.zip").Length / 1MB
    Write-Host "`nSuccess! Created lambda-package.zip ($([math]::Round($size, 2)) MB)" -ForegroundColor Green
    Write-Host "`nNext steps:" -ForegroundColor Cyan
    Write-Host "1. Deploy CloudFormation stack via AWS Console" -ForegroundColor White
    Write-Host "2. Upload this package to update Lambda functions" -ForegroundColor White
    Write-Host "`nSee CLOUDFORMATION_DEPLOYMENT.md for detailed instructions" -ForegroundColor Yellow
} else {
    Write-Host "Error: Failed to create lambda-package.zip" -ForegroundColor Red
}
