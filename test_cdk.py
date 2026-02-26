#!/usr/bin/env python3
"""Test CDK synthesis"""
import sys
print("Starting CDK test...", flush=True)

try:
    print("Importing aws_cdk...", flush=True)
    import aws_cdk as cdk
    print("CDK imported successfully", flush=True)
    
    print("Importing stack...", flush=True)
    from infrastructure.incident_management_stack import IncidentManagementStack
    print("Stack imported successfully", flush=True)
    
    print("Creating app...", flush=True)
    app = cdk.App()
    print("App created successfully", flush=True)
    
    print("Creating stack...", flush=True)
    env = cdk.Environment(
        account="923906573163",
        region="us-east-1"
    )
    
    stack = IncidentManagementStack(
        app,
        "IncidentManagementStack",
        env=env,
        description="AWS Incident Management System with AI-powered remediation"
    )
    print("Stack created successfully", flush=True)
    
    print("Synthesizing...", flush=True)
    app.synth()
    print("Synthesis complete!", flush=True)
    
except Exception as e:
    print(f"Error: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)
