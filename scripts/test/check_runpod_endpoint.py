#!/usr/bin/env python3
"""
Check RunPod endpoint configuration
"""

import requests
import os
from dotenv import load_dotenv

# Load from the RunPod service .env file
load_dotenv('/Users/vivekkrishnan/dev/iaso/services/iaso-scribe/runpod/.env')

def check_endpoint(endpoint_id, name):
    """Check endpoint by sending a minimal request"""
    
    api_key = os.environ.get('RUNPOD_API_KEY')
    
    print(f"\n{'='*60}")
    print(f"Checking {name} endpoint: {endpoint_id}")
    print('='*60)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Send a minimal request to trigger handler loading
    payload = {
        "input": {
            "text": "test",
            "query": "test"
        }
    }
    
    try:
        response = requests.post(
            f"https://api.runpod.ai/v2/{endpoint_id}/run",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Job submitted: {result.get('id')}")
            print(f"Status: {result.get('status')}")
            print("\nCheck the RunPod logs to see which handler loaded:")
            print("- IASOQL should show: 'IASOQL handler called'")
            print("- Phi-4 should show: 'Loading Phi-4-reasoning-plus model'")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    # Check all endpoints
    check_endpoint(os.environ.get('WHISPER_ENDPOINT_ID'), "Whisper")
    check_endpoint(os.environ.get('PHI4_ENDPOINT_ID'), "Phi-4")
    check_endpoint(os.environ.get('IASOQL_ENDPOINT_ID'), "IASOQL")