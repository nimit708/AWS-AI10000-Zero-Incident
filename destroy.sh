#!/bin/bash
# Destroy script for AWS Incident Management System

set -e

echo "=== AWS Incident Management System Destruction ==="
echo ""
echo "WARNING: This will delete all resources including data in DynamoDB and S3!"
echo ""
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Destruction cancelled."
    exit 0
fi

echo ""
echo "Destroying stack..."
cdk destroy --force

echo ""
echo "=== Destruction Complete ==="
