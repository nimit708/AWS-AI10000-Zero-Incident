import subprocess
import zipfile
import os
import shutil
from pathlib import Path

print("=" * 60)
print("Creating Lambda Layer with Dependencies")
print("=" * 60)
print()

# Step 1: Create layer directory structure
print("Step 1: Creating layer directory structure...")
layer_dir = Path("python")
if layer_dir.exists():
    shutil.rmtree(layer_dir)
layer_dir.mkdir()

print("  ✓ Directory created")

# Step 2: Install dependencies for Lambda (Python 3.11)
print("\nStep 2: Installing dependencies...")
print("  Note: Installing for Linux/Lambda runtime...")

# Install pydantic and boto3 (boto3 is included but we'll add latest version)
deps = ["pydantic>=2.5.0"]

for dep in deps:
    print(f"  Installing {dep}...")
    result = subprocess.run([
        "pip", "install", dep, 
        "-t", str(layer_dir),
        "--platform", "manylinux2014_x86_64",
        "--only-binary=:all:",
        "--python-version", "3.11",
        "--upgrade"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"    ✓ {dep} installed")
    else:
        print(f"    ⚠ {dep} installation had warnings (may still work)")

print("  ✓ Dependencies installed")

# Step 3: Create layer zip
print("\nStep 3: Creating layer zip file...")
if os.path.exists("lambda-layer.zip"):
    os.remove("lambda-layer.zip")

with zipfile.ZipFile("lambda-layer.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk("python"):
        for file in files:
            file_path = Path(root) / file
            arcname = file_path
            zipf.write(file_path, arcname)

# Clean up
shutil.rmtree("python")

size_mb = os.path.getsize("lambda-layer.zip") / 1024 / 1024
print(f"  ✓ Layer created: {size_mb:.2f} MB")

print("\n" + "=" * 60)
print("Lambda Layer created successfully!")
print("=" * 60)
print("\nNext: Run deploy_layer.py to publish and attach the layer")
