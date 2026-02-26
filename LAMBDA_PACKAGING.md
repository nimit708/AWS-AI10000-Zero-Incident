# Lambda Packaging Configuration

## Overview
The `.cdkignore` file controls what gets included in Lambda deployment packages when using CDK's `lambda_.Code.from_asset(".")`.

## What Gets Included in Lambda Packages

### ✅ Included Files
- `src/` - All source code
  - `src/models/` - Data models
  - `src/services/` - Service implementations
  - `src/remediation/` - Remediation handlers
  - `src/utils/` - Utility functions
- `lambda_handler.py` - Main Lambda entry point
- `config.py` - Configuration file
- `requirements.txt` - Python dependencies

### ❌ Excluded Files
- `tests/` - All test files (unit, integration, property tests)
- `infrastructure/` - CDK infrastructure code
- `*.md` - All documentation files
- `deploy.sh`, `deploy.ps1`, `destroy.sh` - Deployment scripts
- `.kiro/` - Kiro configuration
- `node_modules/` - Node.js dependencies
- `package.json`, `package-lock.json` - NPM configuration
- `cdk.json`, `app.py` - CDK configuration
- `.vscode/`, `.idea/` - IDE configuration
- `__pycache__/`, `.pytest_cache/` - Python cache
- `cdk-requirements.txt` - CDK Python dependencies
- `pytest.ini` - Test configuration

## Package Size Optimization

### Before `.cdkignore`
- Estimated size: ~50-100 MB (includes tests, docs, node_modules)
- Deployment time: Slow
- Cold start: Slower

### After `.cdkignore`
- Estimated size: ~5-10 MB (only source code + dependencies)
- Deployment time: Fast
- Cold start: Faster

## Verification

To verify what will be packaged:

```bash
# Synthesize CDK (creates cdk.out/)
cdk synth

# Check the asset directory
ls cdk.out/asset.*

# Or use CDK's asset bundling in verbose mode
cdk synth --verbose
```

## Lambda Layer Alternative

For even better optimization, consider creating a Lambda Layer for dependencies:

```bash
# Create layer directory
mkdir -p lambda_layer/python

# Install dependencies to layer
pip install -r requirements.txt -t lambda_layer/python

# Update CDK stack to use layer
# (Already prepared in infrastructure code, just uncomment)
```

Benefits:
- Smaller function packages (only code, no dependencies)
- Faster deployments (layer cached)
- Shared dependencies across functions
- Faster cold starts

## Best Practices

1. **Keep Lambda packages small**: Only include necessary code
2. **Use layers for dependencies**: Separate code from dependencies
3. **Exclude tests**: Never deploy test code to production
4. **Exclude documentation**: Keep docs in repository only
5. **Monitor package size**: Lambda has a 250 MB limit (unzipped)

## Troubleshooting

### Package too large
- Check `.cdkignore` patterns
- Consider using Lambda layers
- Remove unused dependencies from `requirements.txt`

### Missing files in Lambda
- Check if file is excluded in `.cdkignore`
- Verify file exists in source directory
- Check CDK asset bundling logs

### Import errors in Lambda
- Ensure all required files are included
- Check Python path configuration
- Verify dependencies in `requirements.txt`
