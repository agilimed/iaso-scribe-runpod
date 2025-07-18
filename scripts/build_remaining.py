#!/usr/bin/env python3
import subprocess
import os
import sys

# Change to project directory
os.chdir('/Users/vivekkrishnan/dev/iaso')

# Configuration
ECR_REGISTRY = "727646479986.dkr.ecr.us-west-2.amazonaws.com"
AWS_REGION = "us-west-2"

def run_command(cmd, description):
    """Run a shell command and print output"""
    print(f"\n🔵 {description}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error: {result.stderr}")
        return False
    print(f"✅ {description} completed")
    return True

def build_and_push(service_name, dockerfile_path, build_context):
    """Build and push a Docker image"""
    image_tag = f"{ECR_REGISTRY}/iaso-{service_name}:latest"
    
    # Build
    if not run_command(
        f"docker build -t {image_tag} -f {dockerfile_path} {build_context}",
        f"Building {service_name}"
    ):
        return False
    
    # Push
    if not run_command(
        f"docker push {image_tag}",
        f"Pushing {service_name}"
    ):
        return False
    
    return True

# Login to ECR
print("🔐 Logging into ECR...")
login_cmd = f"aws ecr get-login-password --region {AWS_REGION} | docker login --username AWS --password-stdin {ECR_REGISTRY}"
if not run_command(login_cmd, "ECR login"):
    sys.exit(1)

# List of services to build
services = [
    ("template", "clinical-ai/template_service/Dockerfile", "clinical-ai/"),
    ("slm", "clinical-ai/slm_service/Dockerfile", "clinical-ai/"),
    ("embeddings", "services/embeddings-service/Dockerfile", "services/embeddings-service/")
]

# Build and push each service
successful = []
failed = []

for service_name, dockerfile, context in services:
    if build_and_push(service_name, dockerfile, context):
        successful.append(service_name)
    else:
        failed.append(service_name)

# Summary
print("\n📊 Build Summary:")
print(f"✅ Successful: {', '.join(successful) if successful else 'None'}")
print(f"❌ Failed: {', '.join(failed) if failed else 'None'}")

# Check final status
print("\n📋 Checking all IASO services in ECR:")
all_services = ["clinical-ai", "terminology", "knowledge", "template", "slm", "api-gateway", "embeddings"]
for service in all_services:
    cmd = f"aws ecr describe-images --repository-name iaso-{service} --region {AWS_REGION} --query 'imageDetails[0].imageTags[0]' --output text 2>/dev/null"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0 and "latest" in result.stdout:
        print(f"✅ iaso-{service}:latest")
    else:
        print(f"❌ iaso-{service}:latest - Not found")

print("\n🎉 Build process complete!")
print("\nNext steps:")
print("1. Deploy to EKS using: cd infrastructure/terraform && ./deploy.sh -e dev -a apply")
print("2. Configure MeiliSearch indices for terminology search")
print("3. Set up RunPod endpoints for model serving")