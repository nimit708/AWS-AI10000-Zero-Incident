import zipfile
import os
from pathlib import Path

exclude_patterns = [
    'tests', '.md', 'TASK_', 'TASKS_', 'infrastructure', 'app.py', 
    'cdk.json', 'cdk.out', '.js', '.ts', 'node_modules', 'package.json', 
    'package-lock.json', 'deploy.sh', 'deploy.ps1', 'destroy.sh', '.ps1', 
    '.sh', '.git', '.gitignore', '.vscode', '.idea', '.kiro', 'venv', 
    'env', '.env', 'dist', 'build', '.egg-info', 'cdk-requirements.txt', 
    'pytest.ini', '.pytest_cache', '__pycache__', '.pyc', 'test_cdk.py', 
    'cloudformation-template.yaml', 'package-lambda', 'CIRCULAR_DEPENDENCY', 
    'AWS_REGION_FIX', 'DEPLOYMENT_OPTIONS', 'CDK_', 'CFN_', 'QUICK_START', 
    'update-ingestion-lambda', 'response.json', 'create_package.py',
    'lambda-package.zip'
]

def should_exclude(path):
    path_str = str(path)
    return any(pattern in path_str for pattern in exclude_patterns)

print('Creating lambda-package.zip...')
with zipfile.ZipFile('lambda-package.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk('.'):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if not should_exclude(Path(root) / d)]
        
        for file in files:
            file_path = Path(root) / file
            if not should_exclude(file_path):
                arcname = str(file_path.relative_to('.'))
                z.write(file_path, arcname)
                print(f'Added: {arcname}')

size_mb = os.path.getsize('lambda-package.zip') / 1024 / 1024
print(f'\nPackage created successfully: {size_mb:.2f} MB')
