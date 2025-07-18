#!/usr/bin/env python3
"""
Upload IASOQL model from S3 to HuggingFace
"""

import os
import sys
import boto3
from huggingface_hub import HfApi, create_repo, upload_folder
import tempfile
import shutil

# Configuration
S3_BUCKET = "nexuscare-ai-models"
S3_PREFIX = "models/iasoql-merged-complete/"
HF_REPO_ID = "vivkris/iasoql-7B"
LOCAL_TEMP_DIR = "./iasoql-upload-temp"

def download_from_s3():
    """Download model files from S3"""
    print(f"📥 Downloading model from s3://{S3_BUCKET}/{S3_PREFIX}")
    
    s3 = boto3.client('s3')
    os.makedirs(LOCAL_TEMP_DIR, exist_ok=True)
    
    # List all files
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=S3_BUCKET, Prefix=S3_PREFIX)
    
    total_files = 0
    total_size = 0
    
    for page in pages:
        if 'Contents' in page:
            for obj in page['Contents']:
                key = obj['Key']
                size = obj['Size']
                
                # Skip directories
                if key.endswith('/'):
                    continue
                
                # Get relative path
                relative_path = key[len(S3_PREFIX):]
                local_path = os.path.join(LOCAL_TEMP_DIR, relative_path)
                
                # Create subdirectories if needed
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                
                # Download file
                print(f"Downloading {relative_path} ({size / 1024 / 1024:.1f} MB)...")
                s3.download_file(S3_BUCKET, key, local_path)
                
                total_files += 1
                total_size += size
    
    print(f"✅ Downloaded {total_files} files ({total_size / 1024 / 1024 / 1024:.1f} GB)")
    return LOCAL_TEMP_DIR

def create_model_card():
    """Create README.md with attribution"""
    readme_content = """---
license: apache-2.0
language:
- en
tags:
- text-to-sql
- healthcare
- fhir
- clickhouse
- medical
base_model: XGenerationLab/XiYanSQL-QwenCoder-7B-2504
---

# IASOQL-7B Healthcare SQL Generation Model

## Model Description

IASOQL-7B is a specialized text-to-SQL model fine-tuned for healthcare analytics on FHIR data stored in ClickHouse databases.

This model is derived from [XiYanSQL-QwenCoder-7B-2504](https://huggingface.co/XGenerationLab/XiYanSQL-QwenCoder-7B-2504) by XGenerationLab, originally released under the Apache 2.0 License.

## Key Features

- **Healthcare-specific SQL generation** for FHIR resources
- **ClickHouse optimized** with JSON function expertise
- **Fine-tuned** on healthcare queries and FHIR data structures
- **Supports complex analytical queries** on patient data

## Intended Use

This model is designed for:
- Healthcare analytics platforms
- FHIR data analysis
- Clinical decision support systems
- Healthcare reporting and dashboards

## Training Data

Fine-tuned on:
- Healthcare-specific SQL queries
- FHIR resource structures
- ClickHouse JSON functions
- Real-world healthcare analytics patterns

## Usage Example

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("vivkris/iasoql-7B")
tokenizer = AutoTokenizer.from_pretrained("vivkris/iasoql-7B")

query = "How many patients have diabetes?"
# Model generates ClickHouse SQL for FHIR data
```

## Limitations

- Optimized specifically for ClickHouse databases
- Requires FHIR-compliant data structure
- Should not be used for direct medical diagnosis

## License

This model is released under the Apache 2.0 License, inherited from the base model.

## Attribution

This model, IASOQL, is derived from XiYanSQL-QwenCoder-7B-2504 by XGenerationLab, originally released under the Apache 2.0 License.

## Citation

If you use this model, please cite both:
- Original model: XGenerationLab/XiYanSQL-QwenCoder-7B-2504
- This fine-tuned version: vivkris/iasoql-7B
"""
    
    readme_path = os.path.join(LOCAL_TEMP_DIR, "README.md")
    with open(readme_path, 'w') as f:
        f.write(readme_content)
    
    print("✅ Created model card with attribution")

def upload_to_huggingface():
    """Upload model to HuggingFace"""
    # Check for HF token
    hf_token = os.environ.get("HUGGINGFACE_TOKEN") or os.environ.get("HF_TOKEN")
    if not hf_token:
        print("❌ Please set HUGGINGFACE_TOKEN or HF_TOKEN environment variable")
        print("Get your token from: https://huggingface.co/settings/tokens")
        sys.exit(1)
    
    api = HfApi()
    
    print(f"📤 Uploading to HuggingFace: {HF_REPO_ID}")
    
    try:
        # Create repo if it doesn't exist
        create_repo(
            repo_id=HF_REPO_ID,
            token=hf_token,
            private=True,
            exist_ok=True,
            repo_type="model"
        )
        
        # Upload the folder
        api.upload_folder(
            folder_path=LOCAL_TEMP_DIR,
            repo_id=HF_REPO_ID,
            token=hf_token,
            commit_message="Upload IASOQL-7B model fine-tuned for healthcare SQL generation"
        )
        
        print(f"✅ Model uploaded successfully to: https://huggingface.co/{HF_REPO_ID}")
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        raise

def cleanup():
    """Clean up temporary files"""
    if os.path.exists(LOCAL_TEMP_DIR):
        print("🧹 Cleaning up temporary files...")
        shutil.rmtree(LOCAL_TEMP_DIR)

def main():
    print("IASOQL Model Upload to HuggingFace")
    print("=" * 50)
    
    try:
        # Download from S3
        download_from_s3()
        
        # Create model card
        create_model_card()
        
        # Upload to HuggingFace
        upload_to_huggingface()
        
        print("\n✅ Success! Next steps:")
        print("1. Update handler.py to use 'vivkris/iasoql-7B'")
        print("2. Build and push Docker image to RunPod")
        print("3. Set HUGGINGFACE_TOKEN in RunPod environment variables")
        
    except KeyboardInterrupt:
        print("\n⚠️  Upload interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    finally:
        cleanup()

if __name__ == "__main__":
    main()