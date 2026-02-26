#!/usr/bin/env python3
"""
Check the content of the Knowledge Base entry.
"""
import boto3
import json

region = 'eu-west-2'
bucket = 'incident-kb-923906573163'

s3 = boto3.client('s3', region_name=region)

print("=" * 70)
print("KNOWLEDGE BASE CONTENT")
print("=" * 70)

try:
    # List all objects
    response = s3.list_objects_v2(Bucket=bucket, Prefix='incidents/')
    
    if 'Contents' in response:
        print(f"\nFound {len(response['Contents'])} incident(s) in Knowledge Base\n")
        
        for obj in response['Contents']:
            print(f"\nFile: {obj['Key']}")
            print(f"Size: {obj['Size']} bytes")
            print(f"Last Modified: {obj['LastModified']}")
            
            # Get content
            obj_response = s3.get_object(Bucket=bucket, Key=obj['Key'])
            content = obj_response['Body'].read().decode('utf-8')
            kb_data = json.loads(content)
            
            print(f"\nContent:")
            print(json.dumps(kb_data, indent=2))
            
            print("\n" + "-" * 70)
            print("SUMMARY")
            print("-" * 70)
            print(f"Incident ID: {kb_data.get('incident_id')}")
            print(f"Event Type: {kb_data.get('event_type')}")
            print(f"Severity: {kb_data.get('severity')}")
            print(f"Outcome: {kb_data.get('outcome')}")
            print(f"Resolution Steps: {len(kb_data.get('resolution_steps', []))}")
            print(f"AI Confidence: {kb_data.get('metadata', {}).get('confidence_score')}")
            print(f"Routing Path: {kb_data.get('metadata', {}).get('routing_path')}")
            
    else:
        print("\n✗ Knowledge Base is empty")
        
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
