#!/usr/bin/env python3
"""
Generate test payload JSON files for all 6 incident types.

This script creates individual JSON files that can be used to test
the incident management system via AWS CLI or API Gateway.
"""
import json
import os
from datetime import datetime, timezone
from tests.integration.test_payloads import get_all_test_payloads


def main():
    """Generate all test payload files."""
    # Create output directory
    output_dir = "test_payloads"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Generating test payloads in {output_dir}/")
    print("=" * 60)
    
    # Get all payloads
    payloads = get_all_test_payloads()
    
    # Save each payload to a file
    for name, payload in payloads.items():
        filename = os.path.join(output_dir, f"{name}.json")
        
        with open(filename, 'w') as f:
            json.dump(payload, f, indent=2)
        
        print(f"✓ Created {filename}")
        
        # Print summary
        if 'raw_payload' in payload:
            event_type = payload['raw_payload'].get('AlarmName', 'Unknown')
            print(f"  Event: {event_type}")
        elif 'body' in payload:
            incident_type = payload['body'].get('incident_type', 'Unknown')
            print(f"  Incident: {incident_type}")
        print()
    
    print("=" * 60)
    print(f"Generated {len(payloads)} test payload files")
    print(f"\nTo test with AWS Lambda:")
    print(f"  aws lambda invoke --function-name <FUNCTION_NAME> \\")
    print(f"    --payload file://test_payloads/ec2_cpu_spike.json \\")
    print(f"    response.json")
    print(f"\nTo test locally:")
    print(f"  python -c \"import json; from lambda_handler import lambda_handler; \\")
    print(f"    event = json.load(open('test_payloads/ec2_cpu_spike.json')); \\")
    print(f"    print(lambda_handler(event, None))\"")


if __name__ == "__main__":
    main()
