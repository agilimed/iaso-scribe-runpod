#!/usr/bin/env python3
"""
Generate pre-signed URL for IASOQL model download
This allows RunPod to download the model without AWS credentials
"""

import boto3
import sys
import os
from datetime import datetime, timedelta

# Configuration
BUCKET_NAME = "nexuscare-ai-models"
MODEL_PATH = "models/iasoql-merged-complete/"  # Directory path
EXPIRES_IN = 86400  # 24 hours in seconds

def create_model_archive():
    """Create a tar.gz archive of the model directory"""
    import tarfile
    import tempfile
    
    print("Creating model archive from S3 directory...")
    
    # Initialize S3 client
    s3 = boto3.client('s3')
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        model_temp_path = os.path.join(temp_dir, "iasoql-model")
        os.makedirs(model_temp_path)
        
        # Download all files from S3
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=BUCKET_NAME, Prefix=MODEL_PATH)
        
        file_count = 0
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    key = obj['Key']
                    if key.endswith('/'):
                        continue
                    
                    # Get relative path
                    relative_path = key[len(MODEL_PATH):]
                    local_file_path = os.path.join(model_temp_path, relative_path)
                    
                    # Create subdirectories if needed
                    os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                    
                    # Download file
                    print(f"Downloading {relative_path}...")
                    s3.download_file(BUCKET_NAME, key, local_file_path)
                    file_count += 1
        
        print(f"Downloaded {file_count} files")
        
        # Create tar.gz archive
        archive_path = os.path.join(temp_dir, "iasoql-model.tar.gz")
        print("Creating tar.gz archive...")
        with tarfile.open(archive_path, 'w:gz') as tar:
            tar.add(model_temp_path, arcname="iasoql-model")
        
        # Upload archive to S3
        archive_key = f"{MODEL_PATH}iasoql-model.tar.gz"
        print(f"Uploading archive to s3://{BUCKET_NAME}/{archive_key}")
        s3.upload_file(archive_path, BUCKET_NAME, archive_key)
        
        return archive_key

def generate_presigned_url(object_key=None):
    """Generate pre-signed URL for model download"""
    
    # Initialize S3 client
    s3 = boto3.client('s3')
    
    if object_key is None:
        # Check if archive already exists
        archive_key = f"{MODEL_PATH}iasoql-model.tar.gz"
        try:
            s3.head_object(Bucket=BUCKET_NAME, Key=archive_key)
            print(f"Using existing archive: {archive_key}")
            object_key = archive_key
        except:
            print("Archive not found. Creating one...")
            object_key = create_model_archive()
    
    # Generate pre-signed URL
    url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': BUCKET_NAME, 'Key': object_key},
        ExpiresIn=EXPIRES_IN
    )
    
    return url

def main():
    """Generate and display pre-signed URL"""
    
    print("IASOQL Model Pre-signed URL Generator")
    print("=" * 50)
    
    # Check for existing archive or create new one
    if len(sys.argv) > 1 and sys.argv[1] == "--create-archive":
        print("Forcing creation of new archive...")
        archive_key = create_model_archive()
        url = generate_presigned_url(archive_key)
    else:
        url = generate_presigned_url()
    
    print("\n✅ Pre-signed URL generated successfully!")
    print(f"Valid for: {EXPIRES_IN // 3600} hours")
    print("\n" + "=" * 50)
    print("Copy this URL and use it as MODEL_DOWNLOAD_URL in RunPod:")
    print("\n" + url)
    print("\n" + "=" * 50)
    
    # Save to file for easy copying
    with open("presigned_url.txt", "w") as f:
        f.write(url)
    print("\nURL also saved to: presigned_url.txt")

if __name__ == "__main__":
    main()