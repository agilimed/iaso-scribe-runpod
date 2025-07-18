#!/usr/bin/env python3
"""
Verify all RunPod endpoints are working after repository update
"""

import os
import requests
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/Users/vivekkrishnan/dev/iaso/services/iaso-scribe/runpod/.env')

def check_endpoint(name, endpoint_id, test_payload):
    """Check if an endpoint is working"""
    api_key = os.environ.get('RUNPOD_API_KEY')
    
    print(f"\n🔍 Checking {name} endpoint ({endpoint_id})...")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Check endpoint status
    status_response = requests.get(
        f"https://api.runpod.ai/v2/{endpoint_id}/health",
        headers=headers
    )
    
    if status_response.status_code == 200:
        print(f"✅ {name} endpoint is healthy")
        
        # Try a test request
        print(f"📤 Sending test request to {name}...")
        test_response = requests.post(
            f"https://api.runpod.ai/v2/{endpoint_id}/runsync",
            headers=headers,
            json={"input": test_payload},
            timeout=30
        )
        
        if test_response.status_code == 200:
            result = test_response.json()
            if result.get("status") == "COMPLETED":
                print(f"✅ {name} test successful")
                return True
            else:
                print(f"⚠️  {name} test returned status: {result.get('status')}")
                if result.get("error"):
                    print(f"   Error: {result.get('error')}")
        else:
            print(f"❌ {name} test failed: HTTP {test_response.status_code}")
    else:
        print(f"❌ {name} endpoint not healthy: HTTP {status_response.status_code}")
    
    return False

def main():
    """Check all endpoints"""
    print("🚀 IASO RunPod Endpoint Verification")
    print("=" * 50)
    
    endpoints = [
        {
            "name": "Whisper",
            "id": os.environ.get('WHISPER_ENDPOINT_ID'),
            "test_payload": {
                "audio_url": "https://www.w3schools.com/html/horse.mp3"
            }
        },
        {
            "name": "Phi-4",
            "id": os.environ.get('PHI4_ENDPOINT_ID'),
            "test_payload": {
                "prompt": "Summarize: Patient has diabetes",
                "max_tokens": 50
            }
        },
        {
            "name": "IASOQL",
            "id": os.environ.get('IASOQL_ENDPOINT_ID'),
            "test_payload": {
                "query": "How many patients are there?",
                "text": "How many patients are there?"
            }
        }
    ]
    
    results = []
    for endpoint in endpoints:
        if endpoint["id"]:
            success = check_endpoint(
                endpoint["name"],
                endpoint["id"],
                endpoint["test_payload"]
            )
            results.append((endpoint["name"], success))
        else:
            print(f"\n⚠️  {endpoint['name']} endpoint ID not configured")
            results.append((endpoint["name"], False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Summary:")
    for name, success in results:
        status = "✅ Working" if success else "❌ Not Working"
        print(f"   {name}: {status}")
    
    # Instructions if any failed
    if any(not success for _, success in results):
        print("\n⚠️  Some endpoints are not working.")
        print("Please update them in RunPod console:")
        print("1. Go to https://www.runpod.io/console/serverless")
        print("2. Update GitHub URL to: https://github.com/agilimed/iaso-scribe-runpod")
        print("3. Wait for builds to complete (check build logs)")

if __name__ == "__main__":
    main()