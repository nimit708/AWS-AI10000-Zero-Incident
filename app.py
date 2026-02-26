#!/usr/bin/env python3
"""
AWS Incident Management System - CDK Application Entry Point
"""
import os
import aws_cdk as cdk
from infrastructure.incident_management_stack import IncidentManagementStack

app = cdk.App()

# Configuration
env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION", "eu-west-2")
)

# Create the main stack
IncidentManagementStack(
    app,
    "IncidentManagementStack",
    env=env,
    description="AWS Incident Management System with AI-powered remediation"
)

app.synth()
