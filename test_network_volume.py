#!/usr/bin/env python3
"""
Test if network volume is properly configured
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

headers = {
    "Authorization": f"Bearer {os.environ.get('RUNPOD_API_KEY')}",
    "Content-Type": "application/json"
}

# Simple test to check storage paths
payload = {
    "input": {
        "test_storage": True  # Special flag to just test storage
    }
}

print("🔍 Testing network volume configuration...")

response = requests.post(
    f"https://api.runpod.ai/v2/{os.environ.get('RUNPOD_ENDPOINT_ID')}/runsync",
    headers=headers,
    json=payload,
    timeout=30
)

if response.status_code == 200:
    result = response.json()
    print(json.dumps(result, indent=2))
else:
    print(f"Error: {response.status_code}")
    print(response.text)