import subprocess
import zipfile
import os
import shutil
from pathlib import Path

print("Creating Lambda package with dependencies...")
print("=" * 60)

# Step 1: Install dependencies to a temp directory
print("\nStep 1: Installing dependencies...")
if os.path.exists("package"):
    shutil.rmtree("package")
os.makedirs("package")

# Install only runtime dependencies (not test/CDK dependencies)
runtime_deps = ["boto3>=1.34.0", "pydantic>=2.5.0"]

for dep in runtime_deps:
    print(f"  Installing {dep}...")
    subprocess.run([
        "pip", "install", dep, "-t", "package", "--upgrade"
    ], check=True, capture_output=True)

print("  ✓ Dependencies installed")

# Step 2: Copy application code
print("\nStep 2: Copying application code...")
app_files = [
    "lambda_handler.py",
    "config.py",
    "src/"
]

for item in app_files:
    src = Path(item)
    if src.is_file():
        dest = Path("package") / src.name
        shutil.copy2(src, dest)
        print(f"  Copied: {item}")
    elif src.is_dir():
        dest = Path("package") / src.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
        print(f"  Copied: {item}")

print("  ✓ Application code copied")

# Step 3: Create zip file
print("\nStep 3: Creating zip file...")
if os.path.exists("lambda-package.zip"):
    os.remove("lambda-package.zip")

with zipfile.ZipFile("lambda-package.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk("package"):
        for file in files:
            file_path = Path(root) / file
            arcname = file_path.relative_to("package")
            zipf.write(file_path, arcname)

# Clean up
shutil.rmtree("package")

size_mb = os.path.getsize("lambda-package.zip") / 1024 / 1024
print(f"  ✓ Package created: {size_mb:.2f} MB")

print("\n" + "=" * 60)
print("Lambda package with dependencies created successfully!")
print("=" * 60)
