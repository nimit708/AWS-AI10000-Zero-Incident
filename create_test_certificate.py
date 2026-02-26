"""
Create a test SSL certificate in ACM for testing remediation.
Uses AWS CLI to generate and import a certificate.
"""
import boto3
import subprocess
import tempfile
import os
from datetime import datetime

acm = boto3.client('acm', region_name='eu-west-2')

def create_self_signed_cert():
    """Create a self-signed certificate using OpenSSL via subprocess."""
    print("Generating self-signed certificate...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        key_file = os.path.join(tmpdir, 'private.key')
        cert_file = os.path.join(tmpdir, 'certificate.crt')
        
        # Generate private key
        subprocess.run([
            'openssl', 'genrsa',
            '-out', key_file,
            '2048'
        ], check=True, capture_output=True, shell=True)
        
        # Generate certificate (valid for 1 day)
        subprocess.run([
            'openssl', 'req', '-new', '-x509',
            '-key', key_file,
            '-out', cert_file,
            '-days', '1',
            '-subj', '/C=US/ST=Test/L=Test/O=TestOrg/CN=test-ssl.example.com'
        ], check=True, capture_output=True, shell=True)
        
        # Read files
        with open(cert_file, 'r') as f:
            cert_pem = f.read()
        with open(key_file, 'r') as f:
            key_pem = f.read()
    
    return cert_pem, key_pem


def import_to_acm(cert_pem, key_pem):
    """Import certificate to ACM."""
    print("Importing certificate to ACM...")
    
    try:
        response = acm.import_certificate(
            Certificate=cert_pem,
            PrivateKey=key_pem,
            Tags=[
                {'Key': 'Purpose', 'Value': 'SSL-Testing'},
                {'Key': 'CreatedBy', 'Value': 'IncidentManagement'},
                {'Key': 'CreatedAt', 'Value': datetime.now().isoformat()}
            ]
        )
        
        cert_arn = response['CertificateArn']
        print(f"✓ Certificate imported: {cert_arn}")
        return cert_arn
        
    except Exception as e:
        print(f"✗ Error importing certificate: {e}")
        return None


if __name__ == '__main__':
    print("="*60)
    print("Creating Test SSL Certificate")
    print("="*60)
    
    try:
        cert_pem, key_pem = create_self_signed_cert()
        cert_arn = import_to_acm(cert_pem, key_pem)
        
        if cert_arn:
            print("\n" + "="*60)
            print("✓ Certificate created successfully!")
            print("="*60)
            print(f"\nCertificate ARN: {cert_arn}")
            print("\nYou can now use this ARN for testing:")
            print(f"  python src/testing/trigger_ssl_remediation.py")
            print(f"\nOr trigger with specific ARN:")
            print(f"  # Edit trigger_ssl_remediation.py to use: {cert_arn}")
    except FileNotFoundError:
        print("\n✗ OpenSSL not found!")
        print("OpenSSL is required to generate certificates.")
        print("\nAlternative: Use an existing certificate ARN from ACM")
        print("or skip certificate creation and test with a fake ARN")
        print("(the remediation will fail but you can see the workflow)")
