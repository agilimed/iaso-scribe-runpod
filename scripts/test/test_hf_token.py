#!/usr/bin/env python3
"""
Test HuggingFace token access to private repository
"""

from huggingface_hub import HfApi
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get token from environment
HF_TOKEN = os.environ.get("HUGGINGFACE_TOKEN") or os.environ.get("HF_TOKEN")
if not HF_TOKEN:
    print("❌ No HuggingFace token found in environment variables!")
    print("Please set HUGGINGFACE_TOKEN or HF_TOKEN in your .env file")
    exit(1)

def test_token():
    """Test if token can access the private repo"""
    
    api = HfApi(token=HF_TOKEN)
    
    try:
        # Try to get repo info
        repo_info = api.repo_info(repo_id="vivkris/iasoql-7B", repo_type="model")
        print("✅ Token is valid and can access the repository!")
        print(f"Repository: {repo_info.id}")
        print(f"Private: {repo_info.private}")
        print(f"Last modified: {repo_info.lastModified}")
        
    except Exception as e:
        print(f"❌ Token test failed: {str(e)}")
        
    # Also test with transformers
    print("\nTesting with transformers...")
    try:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            "vivkris/iasoql-7B",
            token=HF_TOKEN,
            trust_remote_code=True
        )
        print("✅ Transformers can load tokenizer with this token!")
    except Exception as e:
        print(f"❌ Transformers test failed: {str(e)}")

if __name__ == "__main__":
    test_token()